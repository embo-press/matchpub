
import logging
from pathlib import Path
from typing import List, Tuple, Callable
from datetime import datetime
from argparse import ArgumentParser

from tqdm import tqdm
import pandas as pd

from .config import PreprintInclusion, config
from .models import Submission, Result, Analysis
from .search import EuropePMCEngine
from .ejp import EJPReport
from .match import match_by_author, match_by_title
from .net import BioRxivService, ScopusService
from .decision import normalize_decision
from .reports import (
    Overview, CitationDistribution, TimeToPublish,
    CorrelCitationTimeToSecureReview,
    JournalDistributionPie, JournalDistributionTreeMap,
    PreprintOverview, UnlinkedPreprints,
)
from . import logger, RESULTS


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

    def __init__(
        self,
        ejp_report: EJPReport,
        dest_basename: str,
        SearchEngine: Callable = EuropePMCEngine,
        CitationEngine: Callable = ScopusService,
        preprint_inclusion: PreprintInclusion = config.preprint_inclusion,
        include_citations: bool = config.include_citations
    ):
        self.ejp_report = ejp_report
        self.dest_basename = dest_basename
        self.search_engine = SearchEngine(preprint_inclusion=preprint_inclusion)
        self.citation_engine = CitationEngine()
        self.biorxiv_service = BioRxivService()
        self.preprint_inclusion = preprint_inclusion
        self.include_preprints = self.preprint_inclusion in [PreprintInclusion.ONLY_PREPRINT, PreprintInclusion.WITH_PREPRINT]
        self.include_citations = include_citations

    def run(self) -> List[Path]:
        """Retrieves the best matching published papers corresponding to the submissions of interest, adds citation data,
        exports the results to time-stamped Excel files and generate summary visualization.
        """
        N = len(self.ejp_report.articles)
        logger.info(f"scanning {N} submissions from {self.ejp_report.filepath}.")
        found, not_found = self.retrieve(self.ejp_report.articles)
        if self.include_citations:
            self.add_citations(found)
            self.add_citations(not_found)
        if self.include_preprints:
            self.update_preprint_status(found)
        found = self.filter_preprints(found)
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        logger.info(f"exporting results with timestamp {timestamp}")
        df_found, found_path = self.export(found, 'found', timestamp)
        df_not_found, not_found_path = self.export(not_found, 'not_found', timestamp)
        report_paths = self.reporting(df_found, df_not_found)
        return [found_path, not_found_path] + report_paths

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

    def search(self, submission: Submission) -> Tuple[Result, bool]:
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
        search_res = self.search_engine.search_by_author(authors)
        match = None
        if search_res:
            match, success = match_by_title(search_res, authors, title)
            match.strategy = 'search_by_author_match_by_title'
        else:
            success = False
        if not success:
            search_res = self.search_engine.search_by_title(title)
            if search_res:
                match, success = match_by_author(search_res, authors, title)
                match.strategy = 'search_by_title_match_by_author'
            else:
                success = False
        result = Result(submission, match)
        return result, success

    def add_citations(self, results: List[Result]):
        """Retrieves citation data and updates in place result.article.

        Args:
            (List[Result]): the list of results to update with citation data.
        """
        logger.info(f"fetching {len(results)} scopus citations.")
        for r in tqdm(results):
            if r.article is not None:
                r.article.citations = self.citation_engine.citedby_count(r.article.pmid)

    def update_preprint_status(self, results: List[Result]):
        """If a preprint was retrieved, check its publication status and add in place the doi of the published paper.

        Args:
            results (List[Result]): list of results to update
        """
        logger.info("Updating publication status of preprints.")
        for result in tqdm(results):
            if result.article.is_preprint:
                published_doi = self.biorxiv_service.preprint_publication_status(result.article.doi)
                result.article.preprint_published_doi = published_doi
                logger.debug(f"article '{result.article.doi}' is a preprint. Published doi: '{result.article.preprint_published_doi}'.")

    def filter_preprints(self, results: List[Result]) -> List[Result]:
        """Loops through the results to keep preprints or not depending on the preprint_inclusion setting.

        Args:
            results (List[Result]): list of results to filter.

        Returns:
            (List[Result]): filtered list of results.
        """
        if self.preprint_inclusion == PreprintInclusion.NO_PREPRINT:
            filtered = [r for r in results if not r.article.is_preprint]
        elif self.preprint_inclusion == PreprintInclusion.ONLY_PREPRINT:
            filtered = [r for r in results if r.article.is_preprint]
        elif self.preprint_inclusion == PreprintInclusion.WITH_PREPRINT:
            filtered = results
        else:
            raise ValueError(f"not a valid preprint_inclusion member: {self.preprint_inclusion}")
        logger.info(f"Filtered {len(results) - len(filtered)} out of {len(results)}.")
        return filtered

    def export(self, results: List[Result], name: str, timestamp: str) -> Tuple[pd.DataFrame, Path]:
        """Exports the results to time-stamped Excel files and returns the pandas DataFrame for futher use.
        The order of the columns and header names are defined in models.Analysis

        Args:
            results (List[Result]): the list of results to be saved.
            name (str): a string that will be added to the file name (for ex to distuinguish found from not found results).
            timestamp (str): a timestamp added at the end of the file name.

        Returns:
           (pd.DataFrame): the DataFrame with the results with columns ordered as during export.
           (Path): the path to the saved excel file.
        """

        if results:
            analysis = Analysis(results)
            dest_path = Path(RESULTS) / f"{self.dest_basename}-{name}-{timestamp}.xlsx"  # change this to Path(RESULTS) / f"{dest_basename}-{name}-{timestamp}.xlsx"
            df = pd.DataFrame(analysis)
            normalize_decision(df)
            df = df.sort_values(by='citations', ascending=False)
            df = df[analysis[0].cols]  # order the columns
            with pd.ExcelWriter(dest_path) as writer:
                try:
                    df.to_excel(writer, encoding='utf-8')
                except Exception as e:
                    logger.error(f"error ({str(e)}) when exporting {name} to Excel file {dest_path}")
            logger.info(f"results {name} saved to {dest_path}")
        else:
            logger.info(f"no results to be saved for {name} to {dest_path}.")
        return df, dest_path

    def reporting(self, found: pd.DataFrame, not_found: pd.DataFrame) -> List[Path]:
        """Generates the charts and reports that summarize the results of the analysis.
        Plots and reports are automatically saved in REPORTS with same file basename as the results files.

        Args:
            found (pd.DataFrame): the results for articles successfully found.
            no_found (pd.DataFrame): the results for the negative results.

        Returns:
            (List[Path]): the list of path to the saved reports.
        """

        reports = [
            Overview(found, not_found, self.dest_basename),
            TimeToPublish(found, self.dest_basename),
            CorrelCitationTimeToSecureReview(found, self.dest_basename),
            JournalDistributionPie(found, self.dest_basename),
            JournalDistributionTreeMap(found, self.dest_basename)
        ]
        if self.include_citations:
            reports.append(CitationDistribution(found, self.dest_basename))
        if self.include_preprints:
            reports.append(PreprintOverview(found, self.dest_basename))
            reports.append(UnlinkedPreprints(found, self.dest_basename))
        filepaths = [rep.path for rep in reports if rep.path is not None]
        return filepaths


def self_test():
    ejp_report = EJPReport('/data/test_file.xls')
    scanner = Scanner(ejp_report, '/results/test_results.xlsx', EuropePMCEngine, ScopusService, config.preprint_inclusion)
    scanner.run()


if __name__ == "__main__":
    parser = ArgumentParser(description="MatchPub scanner.")
    parser.add_argument("report", nargs="?", help="Path to the report with the list of submissions.")
    parser.add_argument("dest", nargs="?", default="results", help="Basename of the result files, without extension.")
    parser.add_argument("-D", "--debug", action="store_true", help="Debug mode.")
    parser.add_argument("--no_citations", action="store_true", help="Flag to prevent queries to citation data.")
    args = parser.parse_args()
    debug = args.debug
    include_citations = config.include_citations and not args.no_citations
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    report_path = args.report
    dest_basename = args.dest
    if report_path:
        ejp_report = EJPReport(report_path)
        logger.info(f"Analysis of {len(ejp_report)} submissions with settings: include_citations: {include_citations}, preprint_inclusion: {config.preprint_inclusion}.")
        logger.info(f"Results will be saved in {dest_basename}.")
        scanner = Scanner(
            ejp_report,
            dest_basename,
            EuropePMCEngine,
            ScopusService,
            config.preprint_inclusion,
            include_citations
        )
        scanner.run()
    else:
        self_test()
