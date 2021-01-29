
from collections import UserDict, OrderedDict
from tqdm import tqdm
import pandas as pd
import logging
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
from argparse import ArgumentParser

from .ejp import EJPReport, EJPArticle
from .search import PMCService, PMCArticle
from .match import best_match_by_author, best_match_by_title
from .scopus import citedby_count
from . import logger


class Result(UserDict):

    def __init__(self, query: EJPArticle, match: PMCArticle, method: str):
        # use an OrderedDict so that the order of the keys can be used to order the columns of the result table
        self.data = OrderedDict([
            ('manuscript_nm', query.manuscript_nm),
            ('editor', query.editor),
            ('submitted_title', query.title),
            ('retrieved_title', match.title),
            ('decision', query.decision),
            ('journal_name', match.journal_name),
            ('citations', None),
            ('submitted_author_list', query.author_list),
            ('retrieved_author_list', match.author_list),
            ('pmid', match.pmid),
            ('doi', match.doi),
            ('year', match.year),
            ('month', match.month),
            ('retrieved_abstract', match.abstract),
            ('found_by', method),
        ])

    def keys(self):
        return self.data.keys()


class Scanner:

    def __init__(self, ejp_report: EJPReport, dest_path: str, engine: PMCService = PMCService()):
        self.ejp_report = ejp_report
        self.engine = engine
        self.dest_path = dest_path

    def run(self):
        results = []
        not_found = []
        N = len(self.ejp_report.articles)
        logger.info(f"scanning {N} submissions {self.ejp_report.metadata['time_window']}.")
        for submission in tqdm(self.ejp_report.articles):
            match, method = self.search(submission)
            if match is not None:
                results.append(Result(submission, match, method))
            else:
                not_found.append(submission)
        logger.info(f"found {len(results)} / {N} results search by title first")
        self.citations(results)
        self.save(results, not_found)

    def search(self, article: EJPArticle) -> Tuple[PMCArticle, PMCArticle]:
        title = article.title
        authors = article.expanded_author_list
        match = best_match_by_title(self.engine.search_by_author(authors), title, authors)
        method = 'by_title_first'
        if match is None:
            match = best_match_by_author(self.engine.search_by_title(title), title, authors)
            method = 'by_author_first'
        return match, method

    def citations(self, results: List[Result]):
        logger.info(f"fetching {len(results)} scopus citations.")
        for r in tqdm(results):
            r['citations'] = citedby_count(r['pmid'])

    def save(self, results: Result, not_found: List[EJPArticle]):
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        dest_path = Path(self.dest_path)
        neg_path = dest_path.parent / f"{dest_path.stem}-not-found-{timestamp}.xlsx"
        dest_path = dest_path.parent / f"{dest_path.stem}-{timestamp}.xlsx"
        df = pd.DataFrame.from_dict(results)
        df = df.sort_values(by='citations', ascending=False)
        cols = list(results[0].keys())  # the name of the columns in the desired order
        with pd.ExcelWriter(dest_path) as writer:
            df[cols].to_excel(writer)
        logger.info(f"results saved to {dest_path}.")
        neg = pd.DataFrame(not_found)
        with pd.ExcelWriter(neg_path) as writer:
            neg[['manuscript_nm', 'editor', 'title', 'decision', 'author_list']].to_excel(writer)
        logger.info(f"articles not found saved to {neg_path}.")


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
