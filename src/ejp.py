import re
import pandas as pd
from dateutil import parser
from typing import List, Dict
from collections import UserDict

from .models import Submission
from . import logger


class Metadata(UserDict):

    def __init__(self, keys: List[str]):
        self.data = {k: '' for k in keys}


class EJPReport:

    def __init__(
        self,
        filepath: str,
        metadata_keys: List[str] = [
            "report_name", "editors", "time_window", "article_types", "creation_date"
        ],
        header_signature: List[str] = [
            r"manu", r"manu", r"ed", r".*editor|colleague", r"reviewer|referee",
            r"sub", r".*decision", r".*decision", r".*status", r".*title",
            r"auth", r".*decision"
        ],
        feature_index: Dict[str, int] = {
            "manuscript_nm": 0,
            "editor": 2,
            "decision": 7,
            "title": 9,
            "authors": 10,
        }
    ):
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
        self._guess_time_window(self.metadata['time_window'])

    def _guess_time_window(self, text: str):
        fragments = re.search(r"between(.*)and(.*)", text)
        start = ''
        end = ''
        try:
            first = fragments.group(1)
            second = fragments.group(2)
        except Exception:
            raise ValueError(f"Could not find the required 'between <date> and <date>' statement in '{text}'")
        try:
            start, _ = parser.parse(first, fuzzy_with_tokens=True)
        except Exception:
            raise ValueError(f"Cannot parse this '{first}' as a date.")
        try:
            end, _ = parser.parse(second, fuzzy_with_tokens=True)
        except Exception:
            raise ValueError(f"Cannot parse this '{second}' as a date.")
        self.metadata['time_range'] = {}
        self.metadata['time_range']['start'] = start
        self.metadata['time_range']['end'] = end

    def _load_data(self, sheet: pd.DataFrame):
        start = self._guess_start(sheet)  # where does the actual table start?
        data = sheet[start:].copy()  # select the relevant rows of the data frame
        self._cleanup(data)  # remove 'paraiste' rows that repeat the header
        reduced_data = pd.DataFrame()
        for feature_name, idx in self.feature_index.items():
            reduced_data[feature_name] = data[idx]  # pick only the columns we need
        mask = reduced_data['decision'].apply(lambda x: re.match(r"(.*reject)|(.*accept)", x, re.IGNORECASE) is not None)
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
                raise ValueError(f"Could not find the begining of the table with headers {self.header_signature}")
            putative_header = row.to_list()
            if len(putative_header) == len(self.header_signature) and all([isinstance(e, str) for e in putative_header]):
                if all([re.match(expected, putative, re.IGNORECASE) for expected, putative in zip(self.header_signature, putative_header)]):
                    self.actual_header = putative_header
                    start = i + 1  # success!
                    logger.debug(f"Found start of the table at position {start}")
                    return start
        raise ValueError(f"Could not find the begining of the table with headers {self.header_signature}")

    def _cleanup(self, data: pd.DataFrame):
        for i, row in data.iterrows():
            elements = row.to_list()
            if elements == self.actual_header:
                data.drop(index=i, inplace=True)
        data.reset_index(drop=True, inplace=True)

    def __str__(self):
        return str(self.data)


def self_test():
    ejp_report = EJPReport('/data/msb_test_100.xls')
    print(ejp_report)
    for a in ejp_report.articles:
        print(a)


if __name__ == "__main__":
    self_test()
