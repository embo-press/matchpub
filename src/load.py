import re
import pandas as pd
from dateutil import parser
from typing import List, Dict, Tuple
from collections import UserDict, OrderedDict
from . import logger


class Metadata(UserDict):

    def __init__(self, keys: List[str]):
        self.data = {k: '' for k in keys}


class EJPReport:

    def __init__(
        self,
        metadata_keys: List[str] = ["report_name", "editors", "time_window", "article_types", "creation_date"],
        header_signature: List[str] = [
            "Manuscript", "Manuscript Type", "Editor", "Monitoring Editor", r"Reviewer|Referee",
            "Submission Date", "Final Decision Date", "Final Decision Type", "Current Status", "Manuscript Title",
            "Author\(s\)", "Decision Type"
        ],
        feature_index: Dict[str, int] = {
            "manuscript_nm": 0,
            "editor": 2,
            "decision": 7,
        }
    ):
        self.metadata: Metadata = Metadata(metadata_keys)
        self.skip_lines = len(metadata_keys)
        self.header_signature = header_signature  # signature to find the begning of the table
        self.actual_header = []  # the actual header found in the file
        self.feature_index = feature_index  # the index of the features that need to be extracted
        self.data: pd.DataFrame = None

    def read_excel(self, filepath):
        # sheet = xlrd.open_workbook(filepath).sheet_by_index(0)
        sheet = pd.read_excel(filepath, header=None)
        self.read_metadata(sheet)
        self.read_data(sheet)

    def read_metadata(self, sheet):
        for i, k in enumerate(self.metadata):
            row = sheet[0][i]
            if isinstance(row, str):
                self.metadata[k] = row
                logger.info(f"Imported metadata '{k}'")
            else:
                logger.info(f"The row #{i} supposed to include info on '{k}' is not a string. Ignored.")
        self.guess_time_window(self.metadata['time_window'])

    def guess_time_window(self, text: str):
        fragments = re.search(r"between(.*)and(.*)", text)
        start = ''
        end = ''
        try:
            first = fragments.group(1)
            second = fragments.group(2)
        except Exception:
            raise ValueError("Could not find the required 'between <date> and <date>' statement in '{text}'")
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

    def read_data(self, sheet: pd.DataFrame):
        start = self.guess_start(sheet)
        data = sheet[start:].copy()  # select the relevant part of the data frame
        self.cleanup(data)
        reduced_data = pd.DataFrame()
        for feature_name, idx in self.feature_index.items():
            reduced_data[feature_name] = data[idx]
        self.data = reduced_data

    def guess_start(self, sheet: pd.DataFrame, max_rows: int = 100) -> int:
        start = None
        num_rows, num_cols = sheet.shape
        for i, row in sheet.iterrows():
            logger.debug(f"scanning row {row.to_list()}")
            if i > max_rows:
                raise ValueError(f"Could not find the begining of the table with headers {self.header_map.keys()}")
            putative_header = row.to_list()
            if len(putative_header) == len(self.header_signature) and all([isinstance(e, str) for e in putative_header]):
                import pdb; pdb.set_trace()
                if all([re.match(expected, putative, re.IGNORECASE) for expected, putative in zip(self.header_signature, putative_header)]):
                    logger.info(f"Found start of the table at position {start}")
                    self.actual_header = putative_header
                    start = i + 1  # success!
                    return start
        raise ValueError(f"Could not find the begining of the table with headers {self.header_signature}")

    def cleanup(self, data: pd.DataFrame):
        for i, row in data.iterrows():
            elements = row.to_list()
            if elements == self.actual_header:
                data.drop(index=i, inplace=True)
        data.reset_index(drop=True, inplace=True)

    def __str__(self):
        return str(self.data)


def self_test():
    ejp_report = EJPReport()
    ejp_report.read_excel('data/msb_test_100.xls')
    print(ejp_report)

if __name__ == "__main__":
    self_test()
