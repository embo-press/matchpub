import logging
from pathlib import Path

logger = logging.getLogger('matchpub logger')
logger.setLevel(logging.DEBUG)
log_dir = Path('./log')
log_file = Path('matchpub.log')
if not log_dir.exists():
    log_dir.mkdir()
log_path = log_dir / log_file
fh = logging.FileHandler(log_path)
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
logger.addHandler(sh)
