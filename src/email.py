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
    """Parses an email message and saves its attached file.
    Assumes that a single file is attached.

    Args:
        uid (int): the identifier of the message on the imap server.
        msg_data (Dict[ByteString, Union[int, ByteString]]): the data to be parsed.

    Fields:
        from_address (str): the address from which the message was sent.
        reply_to (str): the address to which the reply will be sent.
        subject (str) the email subject line.
        body (str): the text of the body of the message.
        attachment_path (Path): the full path to the attachment
        uuid (str): a uuid that is attached to the attachement file name before saving to disk.
        dest_dir (Path): the directory where the attachment should be saved.

        uid (int): the message id on the imap server.
        msg_data ([Dict[ByteString, Union[int, ByteString]]): the original data to be parsed.
    """
    from_address: str = field(default="")
    reply_to: str = field(default="")
    subject: str = field(default="")
    body: str = field(default="")
    attachment_path: Path = field(default=None)
    uuid: str = field(default="")
    dest_dir: Path = field(default=Path(DATA))

    uid: InitVar[int] = None
    msg_data: InitVar[Dict[ByteString, Union[int, ByteString]]] = None

    def __post_init__(self, uid: int, msg_data: Dict[ByteString, Union[int, ByteString]]):
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
                    self.get_attachment(part)
        else:
            logger.info(f"no attachment to message {uid}")

    def get_attachment(self, part):
        filename = part.get_filename()
        if filename:
            filename = Path(filename)
            self.uuid = uuid4()
            filename_uuid = f"{filename.stem}-{self.uuid}{filename.suffix}"
            filepath = self.dest_dir / filename_uuid
            attachment = part.get_payload(decode=True)
            filepath.write_bytes(attachment)
            self.attachment_path = filepath
            logger.info(f"attachment saved under: {filepath}")

    def __str__(self):
        return MATCHPUB_MESSAGE_TEMPLATE.substitute(asdict(self))


def main(my_folder: str = "INBOX.matchpub", iterations: int = None, timeout: int = 30):
    """Main email loop that monitors a folder, initiate new analysis when new requests are retrieved by email,
    and send results as attachments by return email.
    my_folder folder is monitored in idle mode for a duration set by timeout (in seconds).
    As soon as an incoming message is detected, an analysis is initiated and a reply email is sent with the results.
    After the specified number of iteration, the idle mode is terminated and the application leaves.
    If iterations is set to None, the email my_folder is checked immediately and only once.

    Args:
        my_folder (str): the email folder where incoming requests are expected to arrive.
        iterations (int): the number of cycles of monitoring to perform in idle mode before leaving the loop.
        timeout (int): the duration in seconds of each idle mode monitoring cycle.
    """
    with IMAPClient(IMAP_SERVER, use_uid=True) as imap_client:
        logger.info(f"checking email from {EMAIL}")
        imap_client.login(EMAIL, PASSWORD)
        logger.info("login successful")
        logger.info(f"checking email from {EMAIL}")
        logger.info(f"checking {my_folder}")
        select_response = imap_client.select_folder(my_folder, readonly=True)  # At least the b'EXISTS', b'FLAGS' and b'RECENT' keys are guaranteed to exist
        N = select_response[b'EXISTS']
        logger.info(f"{my_folder} contains {select_response[b'EXISTS']} messages, {select_response.get(b'RECENT')} recent.")
        if iterations is not None:
            imap_client.idle()
            logger.info("server entered idle mode.")
            for i in range(iterations):
                logger.info(f"iteration No {i+1} of {iterations} with duration {timeout}s.")
                try:
                    N, new_messages = monitor(N, imap_client, timeout)
                    if new_messages:
                        imap_client.idle_done()
                        logger.info("server left the idle mode.")
                        get_analyze_reply(imap_client)
                        imap_client.idle()
                        logger.info("server entered idle mode.")
                except KeyboardInterrupt:
                    break
        else:  # no iterations means we just check email once and leave
            logger.info("no iterations: checking now once.")
            get_analyze_reply(imap_client)


def get_analyze_reply(imap_client: IMAP_SERVER):
    """Retrieves any unread messages, performs the analysis and sends a reply with the results and reports.
    """
    matchpub_messages = get_messages(imap_client)
    for msg in matchpub_messages:
        results = perform_analysis(msg)
        reply_to(msg, attachments=results)
        curr_flags = imap_client.get_flags(msg.uid)
        curr_flags = curr_flags[msg.uid]
        imap_client.set_flags(msg.uid, curr_flags + (ANSWERED,))


def monitor(current_num_messages: int, imap_client: IMAP_SERVER, timeout: int = 30) -> Tuple[int, bool]:
    """Checkt if any new messages has arrived in the inbox while in idle mode.

    Args:
        current_num_messages (int): the current number of messages before checking.
        imap_client (IMAP_SERVER): the imap client.
        timeout (int): the duration in idle checking mode.

    Returns:
        (int): the new current number of messages.
        (bool): whether any new messages were detected.
    """
    responses = imap_client.idle_check(timeout=timeout)  # [(b'FLAGS', (b'$NotJunk', b'\\Draft', b'\\Answered', b'\\Flagged', b'\\Deleted', b'\\Seen', b'\\Recent')), (b'OK', b'[PERMANENTFLAGS ()] No permanent flags permitted'), (3, b'EXISTS'), (0, b'RECENT'), (2, b'FETCH', (b'FLAGS', (b'\\Answered', b'\\Seen')))]
    logger.info(f"Server sent: {responses if responses else 'nothing'}")
    new_messages = False
    for resp in responses:
        if (resp[1] == b'EXISTS') and (resp[0] > current_num_messages):  # new message(s) arrived
            logger.info(f"{resp[0] - current_num_messages} new messages received.")
            current_num_messages = resp[0]
            new_messages = True
            break
    return current_num_messages, new_messages


def get_messages(imap_client: IMAP_SERVER) -> List[MatchPubMessage]:
    """Fetches new messages.

    Args:
        server (IMAPClient): an IMAP client connected to the email server.

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
        imap_client.set_flags(uid, SEEN)
    return matchpub_messages


def perform_analysis(msg: MatchPubMessage) -> List[Path]:
    """Performs the MatchPub analysis using the attached file as input and returns the paths to the analysis results.

    Args:
        msg (MatchPubMessage): the message retrieved by email.

    Returns:
        (List[Path]): the paths to the results and reports.
    """
    ejp_report = EJPReport(msg.attachment_path)
    dest_basename = msg.attachment_path.stem
    scanner = Scanner(
        ejp_report,
        dest_basename
    )
    filepaths = scanner.run()
    return filepaths


def reply_to(msg: MatchPubMessage, attachments: List[Path]):
    """Replies to a request retrieved by email and atttaches the result files.

    Args:
        msg (MatchPubMessage): the message retrieved by email.
        attachments (List[Path]): the paths to the files to attach to the reply.
    """
    # after: https://www.tutorialspoint.com/send-mail-with-attachment-from-your-gmail-account-using-python
    context = ssl.create_default_context()
    with SMTP_SSL(SMTP_SERVER, 465, context=context) as smtp_server:
        smtp_server.login(EMAIL, PASSWORD)  # how long does it hold?
        logger.info("login into smtp successful.")
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
        logger.info(f"created multipart message with subject {subject}, from: {from_address}; to: {to}")
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
    parser = ArgumentParser(description="Email monitoring loop.")
    parser.add_argument('--iterations', default=None, type=int, help="Number of iterations in idle mode.")
    parser.add_argument('--timeout', default=30, type=int, help="Duration between each email checking iteration.")
    parser.add_argument('--my_folder', default='INBOX.matchpub', help="Email folder to monitor.")
    args = parser.parse_args()
    my_folder = args.my_folder
    timeout = args.timeout
    iterations = args.iterations
    logger.info(f"Application will leave after {iterations} iterations of {timeout}s each.")
    main(my_folder=my_folder, timeout=timeout, iterations=iterations)
