import re
import pandas as pd
from typing import List, Dict
from collections import UserDict

from .models import Submission
from .config import config
from . import logger


class Metadata(UserDict):

    def __init__(self, keys: List[str]):
        self.data = {k: '' for k in keys}


class EJPReport:
    """The representation of the EJP report 'Editor Track Report'.
    The report is expected to start with a series of rows that include metadata about the report.
    The expected order of the metadata rows is given in the argument metadata_keys.
    After the metadata row, the start of the actual data tabel will be search automatically by screening for a header row.
    The headers should all match the regex provided in header_signature.
    At the minimum, columns should be provided to specify 'manuscript_nm', 'editor', 'decision', 'title', 'authors' for each submission.
    The position index of these columns is provided in feature_index.

    Args:
        filepath (str): the path to the report excel file.
        metadata_keys (List[str]): the ordered list of metadata fields to be captured from the initial rows in the table.
        header_signature (List[str]): a list of regex that will be used to identify the header row.
        feature_index (Dict[str, int]): map the required feature ('manuscript_nm', 'editor', 'decision', 'title', 'authors') to column index (zero indexed) in the table.
    """
    def __init__(
        self,
        filepath: str,
        metadata_keys: List[str] = config.input_description['metadata_keys'],
        header_signature: List[str] = config.input_description['header_signature'],
        feature_index: Dict[str, int] = config.input_description['feature_index']
    ):
        self.filepath = filepath
        self.metadata: Metadata = Metadata(metadata_keys)  # metadata about the report
        self.header_signature = header_signature  # signature to find the begning of the table
        self.actual_header = []  # the actual header found in the file
        self.feature_index = feature_index  # the index of the features that need to be extracted
        self.data: pd.DataFrame = None  # the table with the list of manuscripts
        self.articles: List[Submission] = []  # the list of articles to retrieve
        self._read_excel(filepath)

    def _read_excel(self, filepath):
        # sheet = xlrd.open_workbook(filepath).sheet_by_index(0)
        sheet = pd.read_excel(filepath, header=None)
        logger.debug("loading ejp report metadata")
        self._load_metadata(sheet)
        logger.debug("loading data")
        self._load_data(sheet)
        logger.debug("loading ejp articles")
        self._load_articles()

    def _load_metadata(self, sheet):
        for i, k in enumerate(self.metadata):
            row = sheet[0][i]
            if isinstance(row, str):
                self.metadata[k] = row
                logger.debug(f"Imported metadata '{k}'")
            else:
                logger.error(f"The row #{i} supposed to include info on '{k}' is not a string. Ignored.")

    def _load_data(self, sheet: pd.DataFrame):
        start = self._guess_start(sheet)  # where does the actual table start?
        data = sheet[start:].copy()  # select the relevant rows of the data frame
        self._cleanup(data)  # remove 'parasite' rows that repeat the header and replace NaN with empty string
        # remove anything that is not matching an accept/reject decision
        reduced_data = pd.DataFrame()
        for feature_name, idx in self.feature_index.items():
            reduced_data[feature_name] = data[idx]  # pick only the columns we need
        # TODO: fix the data type per column
        # 
        mask = reduced_data['decision'].apply(lambda x: re.search(config.input_description['decisions_considered'], x, re.IGNORECASE) is not None)
        filtered_data = reduced_data[mask].copy()
        self.data = filtered_data

    def _load_articles(self):
        self.articles = [Submission(row=row) for i, row in self.data.iterrows()]

    def _guess_start(self, sheet: pd.DataFrame, max_rows: int = 100) -> int:
        start = None
        num_rows, num_cols = sheet.shape
        for i, row in sheet.iterrows():
            logger.debug(f"scanning row {row.to_list()}")
            if i > max_rows:
                raise ValueError(f"Error parsing {self.filepath} - Could not find the begining of the table with headers {self.header_signature}")
            putative_header = row.to_list()
            if len(putative_header) == len(self.header_signature) and all([isinstance(e, str) for e in putative_header]):
                if all([re.match(expected, putative, re.IGNORECASE) for expected, putative in zip(self.header_signature, putative_header)]):
                    self.actual_header = putative_header
                    start = i + 1  # success!
                    logger.debug(f"Found start of the table at position {start}")
                    return start
        raise ValueError(f"Error parsing {self.filepath} - Could not find the begining of the table with headers {self.header_signature}")

    def _cleanup(self, data: pd.DataFrame):
        for i, row in data.iterrows():
            elements = row.to_list()
            if elements == self.actual_header:
                data.drop(index=i, inplace=True)
        data.reset_index(drop=True, inplace=True)
        data.fillna("", inplace=True)  # replace NaN by empty string to avoid exception with re.search()

    def __str__(self):
        return str(self.data)

    def __len__(self):
        return len(self.articles)


def self_test():
    ejp_report = EJPReport('/data/msb_test_100.xls')
    print(ejp_report)
    for a in ejp_report.articles:
        print(a)


if __name__ == "__main__":
    self_test()
