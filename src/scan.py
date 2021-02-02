
import logging
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
from argparse import ArgumentParser

from tqdm import tqdm
import pandas as pd

from .models import Submission, Result, Analysis
from .search import PMCService
from .ejp import EJPReport
from .match import match_by_author, match_by_title
from .scopus import citedby_count
from .viz import overview, citation_distribution, journal_distributions
from . import logger


class Scanner:
    """Scans a list of submissions and attempts to find best matching papers in PubMed Central.
    A dual search strategy is used:
    - first search using the list of authors then confirm with the title and double check with the author list again.
    - if the first strategy fails, search using the title and then confirm with the list of authors and double check with the title again.

    Args:
        ejp_report (EJPReport): the eJP report that includes the list of submissions.
        dest_path (str): the destination path to save the results.
        engine (PMCService): the search engine used to retrieve published papers.
    """

    def __init__(self, ejp_report: EJPReport, dest_path: str, engine: PMCService = PMCService()):
        self.ejp_report = ejp_report
        self.dest_path = dest_path
        self.engine = engine

    def run(self):
        """Retrieves the best matching published papers corresponding to the submissions of interest, adds citation data, 
        exports the results to time-stamped Excel files and generate summary visualization.
        """
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
        """Loops through a list of submissions and accumulates articles found and not found in PubMed Central.
        A result keeps record of both the Submission and its cognate Article if any.

        Args:
            submissions (List[Submission]): a submission as imported from the editorial system report.

        Returns:
            (List[Result]): the list of results for articles that were found.
            (List[Result]): the list of results for articles that were NOT found.
        """
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
        """Performs the dual seach to find a published article best matching the submission.

        Args:
            submission (Submission): the submission used as query for the search.

        Returns: 
            (Result): the result of the search, keeping hold of the Submission and the found Article if any.
            (bool): whether a good match was successfully found.
        """
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
        """Retrieves citation data and updates Result.article.

        Args:
            (List[Result]): the list of results to update with citation data.
        """
        logger.info(f"fetching {len(results)} scopus citations.")
        for r in tqdm(results):
            if r.article is not None:
                r.article.citations = citedby_count(r.article.pmid)

    def export(self, results: List[Result], name: str, timestamp: str) -> pd.DataFrame:
        """Exports the results to time-stamped Excel files and returns the pandas DataFrame for futher use.
        The order of the columns and header names are defined in models.Analysis

        Args:
            results (List[Result]): the list of results to be saved.
            name (str): a string that will be added to the file name (for ex to distuinguish found from not found results).
            timestamp (str): a timestamp added at the end of the file name.

        Returns:
           (pd.DataFrame): the DataFrame with the results with columns ordered as during export.
        """
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
        """Generates the charts and plots that summarize the results of the analysis.
        Plots are automatically saved in /plots with same filename stem as dest_path.

        Args:
            found (pd.DataFrame): the results for articles successfully found.
            no_found (pd.DataFrame): the results for the negative results.
        """
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
