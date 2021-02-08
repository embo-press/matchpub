import email
from argparse import ArgumentParser
from pathlib import Path
from uuid import uuid4
from smtplib import SMTP_SSL
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dataclasses import dataclass, field, InitVar, asdict
from typing import ByteString, List, Dict, Union, Tuple
from string import Template

from imapclient import IMAPClient, SEEN, ANSWERED

from .ejp import EJPReport
from .scan import Scanner
from . import logger
from . import EMAIL, IMAP_SERVER, SMTP_SERVER, PASSWORD, DATA


# adapted from https://www.thepythoncode.com/article/reading-emails-in-python
# https://tools.ietf.org/html/rfc3501#page-49
# https://docs.python.org/3.6/library/asyncio-task.html
# http://theautomatic.net/2020/04/28/how-to-hide-a-password-in-a-python-script/
# https://blog.tecladocode.com/learn-python-encrypting-passwords-python-flask-and-passlib/

MATCHPUB_MESSAGE_TEMPLATE = Template("""From: ${from_address}\nReply to: ${reply_to}\nSubject: ${subject}\n\nBody: ${body}\n\nAttachment: ${attachment_path}""")


@dataclass
class MatchPubMessage:
    from_address: str = field(default="")
    reply_to: str = field(default="")
    subject: str = field(default="")
    body: str = field(default="")
    attachment_path: Path = field(default=None)
    uuid: str = field(default="")

    uid: InitVar[int] = None
    msg_data: InitVar[Dict[ByteString, Union[int, ByteString]]] = None

    def __post_init__(self, uid: int, msg_data: Dict[ByteString, Union[int, ByteString]], dest_dir: Path = Path(DATA)):
        self.uid = uid
        msg = email.message_from_bytes(msg_data[b"RFC822"])
        logger.info(f"msg {uid} keys:\n{msg.keys()}\n\n")
        self.from_address = msg.get("from")
        self.subject = msg.get("subject")
        self.reply_to = msg.get("Return-Path")
        logger.info(f"From: {self.from_address}")
        logger.info(f"Subject: {self.subject}")
        logger.info(f"Return address: {self.reply_to}")
        logger.info(f"Is multipart: {msg.is_multipart()}")
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                logger.info(f"content-type: {content_type}; content-disposition: {content_disposition}")
                try:
                    body = part.get_payload(decode=True).decode()
                except Exception:
                    pass
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    self.body = body
                    logger.info(f"Content:\n{body}")
                elif "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        folder_name = self.clean(self.subject)
                        folder = dest_dir / folder_name
                        if not folder.exists():
                            folder.mkdir()
                        filename = Path(filename)
                        self.uuid = uuid4()
                        filename_uuid = f"{filename.stem}-{self.uuid}-{filename.suffix}"
                        filepath = folder / filename_uuid
                        attachment = part.get_payload(decode=True)
                        filepath.write_bytes(attachment)
                        self.attachment_path = filepath
                        logger.info(f"attachment saved under: {filepath}")
        else:
            logger.info(f"no attachment to message {uid}")

    @staticmethod
    def clean(text):
        # clean text for creating a folder
        return "".join(c if c.isalnum() else "_" for c in text)

    def __str__(self):
        return MATCHPUB_MESSAGE_TEMPLATE.substitute(asdict(self))


def main(my_folder: str = "INBOX.matchpub"):
    with IMAPClient(IMAP_SERVER, use_uid=True) as imap_client:
        logger.info(f"checking email from {EMAIL}")
        imap_client.login(EMAIL, PASSWORD)
        logger.info("login successful")
        logger.info(f"checking email from {EMAIL}")
        logger.info(f"checking {my_folder}")
        select_response = imap_client.select_folder(my_folder, readonly=True)  # At least the b'EXISTS', b'FLAGS' and b'RECENT' keys are guaranteed to exist
        N = select_response[b'EXISTS']
        logger.info(f"{my_folder} contains {select_response[b'EXISTS']} messages, {select_response.get(b'RECENT')} recent.")
        imap_client.idle()
        logger.info("server entered idle mode.")
        while True:
            try:
                N, new_messages = monitor(N, imap_client, 30)
                if new_messages:
                    imap_client.idle_done()
                    logger.info("server left the idle mode.")
                    matchpub_messages = get_messages(imap_client)
                    for msg in matchpub_messages:
                        results = perform_analysis(msg)
                        reply_to(msg, attachments=results)
                        imap_client.set_flags(msg.uid, ANSWERED)
                    imap_client.idle()
                    logger.info("server in idle mode.")
            except KeyboardInterrupt:
                break
        imap_client.idle_done()


def monitor(current_num_messages: int, imap_client: IMAP_SERVER, timeout: int = 30) -> Tuple[int, bool]:
    responses = imap_client.idle_check(timeout=timeout)  # [(b'FLAGS', (b'$NotJunk', b'\\Draft', b'\\Answered', b'\\Flagged', b'\\Deleted', b'\\Seen', b'\\Recent')), (b'OK', b'[PERMANENTFLAGS ()] No permanent flags permitted'), (3, b'EXISTS'), (0, b'RECENT'), (2, b'FETCH', (b'FLAGS', (b'\\Answered', b'\\Seen')))]
    logger.info(f"Server sent: {responses if responses else 'nothing'}")
    new_messages = False
    for resp in responses:
        if (resp[1] == b'EXISTS') and (resp[0] > current_num_messages):  # new message(s) arrived
            logger.info("{resp[0] - N} new messages received.")
            current_num_messages = resp[0]
            new_messages = True
            break
    return current_num_messages, new_messages


def get_messages(imap_client: IMAP_SERVER) -> List[MatchPubMessage]:
    """Fetch new messages.

    Args:
        server (IMAPClien): an IMAP client connected to the email server.

    Returns:
        (List[MatchPubMessage]): the new MatchPub messages
    """
    messages = imap_client.search(criteria="UNSEEN")
    logger.info(f"{len(messages)} unseen messages.")
    msg_dict = imap_client.fetch(messages, "RFC822")  # A dictionary is returned, indexed by message number. Each item in this dictionary is also a dictionary, with an entry corresponding to each item in data.
    matchpub_messages = []
    for uid, m in msg_dict.items():
        logger.info(f"msg {uid} has flags {imap_client.get_flags(uid)}")
        matchpub_messages.append(MatchPubMessage(uid=uid, msg_data=m))
        imap_client.set_flags(uid, SEEN, silent=False)
    return matchpub_messages


def perform_analysis(msg: MatchPubMessage) -> List[Path]:
    ejp_report = EJPReport(msg.attachment_path)
    dest_basename = msg.attachment_path.stem
    scanner = Scanner(
        ejp_report,
        dest_basename
    )
    filepaths = scanner.run()
    return filepaths


def reply_to(msg: MatchPubMessage, attachments: List[Path]):
    # after: https://www.tutorialspoint.com/send-mail-with-attachment-from-your-gmail-account-using-python
    context = ssl.create_default_context()
    with SMTP_SSL(SMTP_SERVER, 465, context=context) as smtp_server:
        smtp_server.login(EMAIL, PASSWORD)  # how long does it hold?
        logger.info(f"login into smtp successful.")
        subject = f"Re: {msg.subject}"
        body = f"MatchPub results with {len(attachments)} attachments.\nYour friendly MatchPub bot.\n\n\n"
        from_address = msg.from_address
        to = msg.reply_to
        # Create a multipart message and set headers
        message = MIMEMultipart()
        message["From"] = from_address
        message["To"] = to
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        logger.info(f"created multipar message with subject {subject}, from: {from_address}; to: {to}")
        for path in attachments:
            with path.open("rb") as file:
                # Add file as application/octet-stream
                # Email client can usually download this automatically as attachment
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file.read())
                # Encode file in ASCII characters to send by email    
                encoders.encode_base64(part)
                # remove the uuid from the filename
                path = str(path).replace(f"-{msg.uuid}-", "")
                # Add header as key/value pair to attachment part
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {str(path)}",
                )
                message.attach(part)
                logger.info(f"attached {path}")
        text = message.as_string()
        smtp_server.sendmail(from_address, to, text)
        logger.info(f"sent email with subject {subject} to {to}")


if __name__ == "__main__":
    main()
