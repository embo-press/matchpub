import logging
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()
SCOPUS_API_KEY = os.getenv('SCOPUS_API_KEY')

EMAIL = os.getenv('EMAIL')
IMAP_SERVER = os.getenv('IMAP_SERVER')
SMTP_SERVER = os.getenv('SMTP_SERVER')
PASSWORD = os.getenv('PASSWORD')

DATA = os.getenv('DATA')
RESULTS = os.getenv('RESULTS')
REPORTS = os.getenv('REPORTS')

logger = logging.getLogger('matchpub logger')
logger.setLevel(logging.DEBUG)
log_dir = Path('/log')
log_file = Path('matchpub.log')
if not log_dir.exists():
    log_dir.mkdir()
log_path = log_dir / log_file
fh = logging.FileHandler(log_path)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
logger.addHandler(sh)


