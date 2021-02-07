from imapclient import IMAPClient, ANSWERED
from smtplib import SMTP, SMTP_SSL
import ssl

from .ejp import EJPReport
from .scan import Scanner
from .email import check, answer
from . import IMAP_SERVER, SMTP_SERVER


def main():
    with IMAPClient(IMAP_SERVER, use_uid=True) as imap_client:
        requests = check(imap_client)
        for msg in requests:
            ejp_report = EJPReport(msg.attachment_path)
            dest_basename = msg.attachment_path.stem
            scanner = Scanner(
                ejp_report,
                dest_basename
            )
            filepaths = scanner.run()
            context = ssl.create_default_context()
            with SMTP_SSL(SMTP_SERVER, 465, context=context) as smtp_server:
                answer(smtp_server, msg, attachments=filepaths)
            imap_client.set_flags(msg.uid, ANSWERED)

if __name__ == "__main__":
    main()
