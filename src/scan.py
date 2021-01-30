
from tqdm import tqdm
import pandas as pd
import logging
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
from argparse import ArgumentParser

from .models import Submission, Article, Result, ResultDict
from .search import PMCService
from .ejp import EJPReport
from .match import match_by_author, match_by_title
from .scopus import citedby_count
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
        self.export(found, not_found)

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
            match, success = match_by_title(search_res, title)
            match.strategy = 'search_by_author_match_by_title'
        else:
            success = False
        if not success:
            search_res = self.engine.search_by_title(title)
            if search_res:
                match, success = match_by_author(search_res, authors)
                match.strategy = 'search_by_title_match_by_author'
            else:
                success = False
        return Result(submission, match), success

    def add_citations(self, results: List[Result]):
        logger.info(f"fetching {len(results)} scopus citations.")
        for r in tqdm(results):
            r.article.citations = citedby_count(r.article.pmid)

    def export(self, found: List[Result], not_found: List[Result]):
        found = [ResultDict(r) for r in found]
        not_found = [ResultDict(r) for r in not_found]

        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        dest_path = Path(self.dest_path)
        neg_path = dest_path.parent / f"{dest_path.stem}-not-found-{timestamp}.xlsx"
        dest_path = dest_path.parent / f"{dest_path.stem}-{timestamp}.xlsx"

        df = pd.DataFrame(found)
        cols = found[0].cols
        df = df.sort_values(by='citations', ascending=False)
        with pd.ExcelWriter(dest_path) as writer:
            df[cols].to_excel(writer)
        logger.info(f"results saved to {dest_path}.")

        neg = pd.DataFrame(not_found)
        cols = not_found[0].cols
        with pd.ExcelWriter(neg_path) as writer:
            neg[cols].to_excel(writer)
        logger.info(f"submissions not found saved to {neg_path}.")


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
    report_path = args.report
    dest_path = args.dest
    if report_path:
        ejp_report = EJPReport(report_path)
        scanner = Scanner(ejp_report, dest_path)
        scanner.run()
    else:
        self_test()
