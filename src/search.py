from typing import List, Union
from datetime import datetime

from .models import PubMedArticle, EuropePMCArticle
from .net import EuropePMCService, PubMedService
from .utils import normalize
from .config import PreprintInclusion, config
from . import logger


class SearchEngine:
    """Abstract class for search eninge used to search published articles and preprints"""

    search_service = None

    def __init__(self, preprint_inclusion: PreprintInclusion = PreprintInclusion.NO_PREPRINT):
        self.preprint_inclusion = preprint_inclusion

    def search_by_author_query_builder(self, author_list: List[List[str]], min_pub_date: str, max_pub_date: str) -> str:
        raise NotImplementedError

    def search_by_author(self, author_list: List[List[str]], min_pub_date: str = '1970-01-01', max_pub_date: str = '3000-01-01') -> List[Union[PubMedArticle, EuropePMCArticle]]:
        """Search using the expanded author list.

        Args:
            author_list (List[List[str]]): the expanded list of authors with for each name alternatives.
            min_pub_date (int): the earliest publication date to consider in the search.
            max_pub_date (int): the latest publication date to consider in the search.

        Returns:
            (List[Union[PubMedArticle, EuropePMCArticle]]): the list of articles retrieved
            """
        article_list = []
        if author_list:
            query = self.search_by_author_query_builder(author_list, min_pub_date, max_pub_date)
            query = self._preprint_inclusion_decoration(query)
            article_list = self._search(query)
        return article_list

    def search_by_title_query_builder(self, title: str, min_pub_date: str, max_pub_date: str) -> str:
        raise NotImplementedError

    def search_by_title(self, title: str, min_pub_date: str = '1970-01-01', max_pub_date: str = '3000-01-01') -> List[Union[PubMedArticle, EuropePMCArticle]]:
        """Search using the title.

        Args:
            title (str): the title of the paper.
            min_pub_date (int): the earliest publication date to consider in the search.
            max_pub_date (int): the latest publication date to consider in the search.

        Returns:
            (List[Union[PubMedArticle, EuropePMCArticle]): the list of articles retrieved
        """
        article_list = []
        if title:
            query = self.search_by_title_query_builder(title, min_pub_date, max_pub_date)
            query = self._preprint_inclusion_decoration(query)
            article_list = self._search(query)
        return article_list

    def _preprint_inclusion_decoration(self, query: str):
        raise NotImplementedError

    def _search(self, query: str) -> List[Union[PubMedArticle, EuropePMCArticle]]:
        logger.debug(f"query: '{query}'")
        articles = self.search_service.search(query)
        return articles


class EuropePMCEngine(SearchEngine):
    """The EuropePMC search engine used to search published articles and preprints.

    Args:
        preprint_inclusion (PreprintInclusion): level of inclusion of preprints.
    """
    search_service = EuropePMCService()

    def search_by_author_query_builder(self, author_list: List[List[str]], min_pub_date: str, max_pub_date: str) -> str:
        # consider alternatives of same name and use OR construct
        or_statements = []
        for alternatives in author_list:
            statement = " OR ".join([f'AUTH:"{au}"' for au in alternatives])
            or_statements.append(f"({statement})")
        and_names = ' AND '.join(or_statements)
        query = f"{and_names} AND FIRST_PDATE:[{min_pub_date} TO {max_pub_date}]"
        return query

    def search_by_title_query_builder(self, title, min_pub_date, max_pub_date) -> str:
        # total recall on positives is best with unquoted title, do_not_remove='+', do=['ctrl', 'punctuation', 'html_tags', 'html_unescape']
        title = normalize(title, do_not_remove='+', do=['ctrl', 'punctuation', 'html_tags', 'html_unescape'])
        query = f'TITLE:{title} AND FIRST_PDATE:[{min_pub_date} TO {max_pub_date}]'
        return query

    def _preprint_inclusion_decoration(self, query: str):
        if self.preprint_inclusion == PreprintInclusion.NO_PREPRINT:
            query += ' AND NOT (SRC:"PPR")'
        elif self.preprint_inclusion == PreprintInclusion.ONLY_PREPRINT:
            query += ' AND (SRC:"PPR")'
        return query


class PubMedEngine(SearchEngine):
    """The PubMed search engine used to search published articles and preprints.

    Args:
        preprint_inclusion (PreprintInclusion): level of inclusion of preprints.
    """
    search_service = PubMedService()

    def date_convert(self, yyyy_mm_dd: str) -> str:
        YYYY_MM_DD = datetime.strptime(yyyy_mm_dd, '%Y-%m-%d').strftime('%Y/%m/%d')
        return YYYY_MM_DD

    def search_by_author_query_builder(self, author_list: List[List[str]], min_pub_date: str, max_pub_date: str) -> str:
        # consider alternatives of same name and use OR construct
        min_pub_date = self.date_convert(min_pub_date)
        max_pub_date = self.date_convert(max_pub_date)
        or_statements = []
        for alternatives in author_list:
            statement = " OR ".join([f'{au}[AU]' for au in alternatives])
            or_statements.append(f"({statement})")
        and_names = ' AND '.join(or_statements)
        query = f"{and_names} AND {min_pub_date}:{max_pub_date}[PDAT]"
        return query

    def search_by_title_query_builder(self, title, min_pub_date, max_pub_date) -> str:
        # total recall on positives is best with unquoted title, do_not_remove='+', do=['ctrl', 'punctuation', 'html_tags', 'html_unescape']
        min_pub_date = self.date_convert(min_pub_date)
        max_pub_date = self.date_convert(max_pub_date)
        title = normalize(title, do_not_remove='+', do=['ctrl', 'punctuation', 'html_tags', 'html_unescape'])
        query = f'{title}[TI] AND {min_pub_date}:{max_pub_date}[PDAT]'
        return query

    def _preprint_inclusion_decoration(self, query: str):
        if self.preprint_inclusion == PreprintInclusion.NO_PREPRINT:
            query += ' NOT preprint[PT]'
        elif self.preprint_inclusion == PreprintInclusion.ONLY_PREPRINT:
            query += ' AND preprint[PT])'
        return query


def self_test():
    s = EuropePMCEngine(preprint_inclusion=config.preprint_inclusion)
    by_author = s.search_by_author([["Lemberger"], ["Liechti"]])
    if by_author:
        print(str(by_author))
    by_title = s.search_by_title("SourceData: a semantic platform for curating and searching figures")
    print(str(by_title))
    if by_title:
        print(by_title[0].expanded_author_list)
    empty_author = s.search_by_author([])
    print(str(empty_author))


if __name__ == "__main__":
    self_test()
