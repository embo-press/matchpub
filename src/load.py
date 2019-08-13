import xlrd
import re


class ImportEJPReport:
    def __init__(self):
        self.metadata_rows = ['report_name', 'editors', 'time_window', 'article_types', 'creation_date']
        self.headers =  [
            'Manuscript',
            'Manuscript Type',
            'Editor',
            'Monitoring Editor',
            'Referee',
            'Submission Date',
            'Final Decision Date',
            'Final Decision Type',
            'Current Status',
            'Manuscript Title', 
            'Author(s)',
            'Decision Type'
        ]
        self.fields = [
            'Manuscript',
            'ManuscriptType',
            'Editor',
            'MonitoringEditor',
            'Referee',
            'SubmissionDate',
            'FinalDecisionDate',
            'FinalDecisionType',
            'CurrentStatus',
            'ManuscriptTitle', 
            'Authors',
            'DecisionType'
        ]

    def find_start(self, sheet):
        start = False
        for i in range(len(self.metadata_rows), sheet.nrows):
            row = [cell.value for cell in sheet.row(i)]
            # the reports do not have very standardized headers, so check first 3 ones
            # and the proper number of headers
            if (len(row) == 12) and (row[:3]  == self.headers[:3]):
                start = i+1
                break
        return start

    def open(self, filepath):
        excelfile = xlrd.open_workbook(filepath)
        sheet = excelfile.sheet_by_index(0)
        return sheet

    def read_metadata(self, sheet):
        metadata = {m: sheet.row(i)[0].value for i, m in enumerate(self.metadata_rows)}
        return metadata

    def load(self, analysisID, filepath):
        sheet = self.open(filepath)
        metadata = self.read_metadata(sheet)
        starting_row = self.find_start(sheet)
        submissions = []
        for i in range(starting_row, sheet.nrows):
            row = sheet.row(i)
            manu = {f: row[j].value for j, f in enumerate(self.fields)}
            manu['analysisID'] = analysisID
            submissions.append(manu)
        return metadata, submissions
