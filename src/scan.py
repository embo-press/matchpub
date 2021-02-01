
from tqdm import tqdm
import pandas as pd
import logging
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
from argparse import ArgumentParser

from .models import Submission, Result, Analysis
from .search import PMCService
from .ejp import EJPReport
from .match import match_by_author, match_by_title
from .scopus import citedby_count
from .viz import overview, citation_distribution, journal_distributions
from . import logger


class Scanner:

    def __init__(self, ejp_report: EJPReport, dest_path: str, engine: PMCService = PMCService()):
        self.ejp_report = ejp_report
        self.engine = engine
        self.dest_path = dest_path

    def run(self):
        N = len(self.ejp_report.articles)
        logger.info(f"scanning {N} submissions {self.ejp_report.metadata['time_window']}.")
        found, not_found = self.retrieve(self.ejp_report.articles)
        self.add_citations(found)
        self.add_citations(not_found)
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        logger.info(f"exporting results with timestamp {timestamp}")
        df_found = self.export(found, 'found', timestamp)
        df_not_found = self.export(not_found, 'not_found', timestamp)
        self.viz(df_found, df_not_found)

    def retrieve(self, submissions: List[Submission]) -> Tuple[List[Result], List[Result]]:
        found = []
        not_found = []
        for submission in tqdm(submissions):
            result, success = self.search(submission)
            if success:
                found.append(result)
            else:
                not_found.append(result)
        logger.info(f"found {len(found)} / {len(submissions)} results.")
        return found, not_found

    def search(self, submission: Submission) -> Result:
        title = submission.title
        authors = submission.expanded_author_list
        logger.debug(f"Looking for {submission.title} by {submission.author_list}.")
        search_res = self.engine.search_by_author(authors)
        match = None
        if search_res:
            match, success = match_by_title(search_res, authors, title)
            match.strategy = 'search_by_author_match_by_title'
        else:
            success = False
        if not success:
            search_res = self.engine.search_by_title(title)
            if search_res:
                match, success = match_by_author(search_res, authors, title)
                match.strategy = 'search_by_title_match_by_author'
            else:
                success = False
        return Result(submission, match), success

    def add_citations(self, results: List[Result]):
        logger.info(f"fetching {len(results)} scopus citations.")
        for r in tqdm(results):
            if r.article is not None:
                r.article.citations = citedby_count(r.article.pmid)

    def export(self, results: List[Result], name: str, timestamp: str) -> pd.DataFrame:
        analysis = Analysis(results)

        dest_path = Path(self.dest_path)
        dest_path = dest_path.parent / f"{dest_path.stem}-{name}-{timestamp}.xlsx"

        df = pd.DataFrame(analysis)
        df = df.sort_values(by='citations', ascending=False)
        with pd.ExcelWriter(dest_path) as writer:
            df[analysis.cols].to_excel(writer)
        logger.info(f"results {name} saved to {dest_path}")

        return df

    def viz(self, found: pd.DataFrame, not_found: pd.DataFrame):
        overview(found, not_found, dest_path)
        citation_distribution(found, self.dest_path)
        journal_distributions(found, self.dest_path)


def self_test():
    ejp_report = EJPReport('/data/test_file.xls')
    scanner = Scanner(ejp_report, '/results/test_results.xlsx')
    scanner.run()


if __name__ == "__main__":
    parser = ArgumentParser(description="MatchPub scanner.")
    parser.add_argument("report", nargs="?", help="Path to the report with the list of submissions.")
    parser.add_argument("dest", nargs="?", default="results/results.xlsx", help="Path to results file.")
    parser.add_argument("-D", "--debug", action="store_true", help="Debug mode.")
    args = parser.parse_args()
    debug = args.debug
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    report_path = args.report
    dest_path = args.dest
    if report_path:
        ejp_report = EJPReport(report_path)
        scanner = Scanner(ejp_report, dest_path)
        scanner.run()
    else:
        self_test()
