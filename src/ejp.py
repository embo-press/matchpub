import pandas as pd
from typing import List, Dict
# import re


class EJPReport:

    def __init__(
        self,
        metadata_keys: List[str] = ["report_name", "editors", "time_window", "article_types", "creation_date"],
        header_map: Dict[str, str] = {
            "Manuscript": "manuscript",
            "Manuscript Type": "manuscript_type",
            "Editor": "editor",
            "Monitoring Editor": "monitoring_editor",
            "Referee": "referee",
            "Submission Date": "submission_date",
            "Final Decision Date": "final_decision_date",
            "Final Decision Type": "final_decision_type",
            "Current Status": "current_status",
            "Manuscript Title": "manuscript_title",
            "Author(s)": "author_list",
            "Decision Type": "decision_type"
        }
    ):
        self.metadata = {k: None for k in metadata_keys}
        self.header_map = header_map  # signature to find the begning of the table
        self.data = None

    def read_excel(self, filepath):
        sheet = pd.read_excel(filepath, sheet_name="Sheet1")
        import pdb; pdb.set_trace()
        # metadata = self.read_metadata(sheet)
        # starting_row = self.find_start(sheet)
        # submissions = []
        # for i in range(starting_row, sheet.nrows):
        #     row = sheet.row(i)
        #     manu = {f: row[j].value) for j, f in enumerate(self.fields)}
        #     submissions.append(manu)

    # def read_metadata(self, sheet):
    #     metadata = {}
    #     for i, m in enumerate(self.metadata_rows):
    #         print(m)
    #         metadata[m] = sheet.row(i)[0].value
    #         print("read_metadata", m, metadata[m])
    #     # pattern = re.compile(r"For Papers with a final decision between (\d+).* +(\w+) +(\d+)  00:00:00 and (\d+).* +(\w+) +(\d+)  00:00:00")
    #     # m = pattern.match(metadata["time_window"])
        
    #     # start_date = datetime.strptime(" ".join([m.group(1), m.group(2), m.group(3)]), "%d %b %y")
    #     # start_date = "{:%Y-%m-%d}".format(start_date)
    #     # end_date   = datetime.strptime(" ".join([m.group(4), m.group(5), m.group(6)]), "%d %b %y")
    #     # end_date = "{:%Y-%m-%d}".format(end_date)
    #     return metadata

    # def find_start(self, sheet):
    #     start = False
    #     for i in range(len(self.metadata_rows), sheet.nrows):
    #         row = [cell.value for cell in sheet.row(i)]
    #         # the reports do not have very standardized headers, so check first 3 ones
    #         # and the proper number of headers
    #         if (len(row) == 12) and (row[:3]  == self.headers[:3]):
    #             start = i+1
    #             break
    #     return start


def self_test():
    ejp_report = EJPReport()
    ejp_report.read_excel('data/test_file.xls')

if __name__ == "__main__":
    self_test()
