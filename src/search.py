
from typing import List

from .models import Article
from .net import EuropePMCService
from .utils import normalize
from .config import PreprintInclusion, config
from . import logger


class EuropePMCEngine:
    """The EuropePMC search engine used to search published articles and preprints.

    Args:
        preprint_inclusion (PreprintInclusion): level of inclusion of preprints.
    """
    europe_pmc_service = EuropePMCService()

    def __init__(self, preprint_inclusion: PreprintInclusion = PreprintInclusion.NO_PREPRINT):
        self.preprint_inclusion = preprint_inclusion

    def search_by_author(self, author_list: List[List[str]], min_pub_date: str = '1970-01-01', max_pub_date: str = '3000-01-01') -> List[Article]:
        """Search using the expanded author list.

        Args:
            author_list (List[List[str]]): the expanded list of authors with for each name alternatives.
            min_pub_date (int): the earliest publication date to consider in the search.
            max_pub_date (int): the latest publication date to consider in the search.

        Returns:
            (List[Article]): the list of articles retrieved
            """
        if author_list:
            # consider alternatives of same name and use OR construct
            or_statements = []
            for alternatives in author_list:
                statement = " OR ".join([f'AUTH:"{au}"' for au in alternatives])
                or_statements.append(f"({statement})")
            and_names = ' AND '.join(or_statements)
            query = f"{and_names} AND FIRST_PDATE:[{min_pub_date} TO {max_pub_date}]"
            query = self._preprint_inclusion_decoration(query)
            article_list = self._search(query)
        else:
            article_list = []
        return article_list

    def search_by_title(self, title: str, min_pub_date: str = '1970-01-01', max_pub_date: str = '3000-01-01') -> List[Article]:
        """Search using the title.

        Args:
            title (str): the title of the paper.
            min_pub_date (int): the earliest publication date to consider in the search.
            max_pub_date (int): the latest publication date to consider in the search.

        Returns:
            (List[Article]): the list of articles retrieved
        """
        if title:
            # total recall on positives is best with unquoted title, do_not_remove='+', do=['ctrl', 'punctuation', 'html_tags', 'html_unescape']
            title = normalize(title, do_not_remove='+', do=['ctrl', 'punctuation', 'html_tags', 'html_unescape'])
            query = f'TITLE:{title} AND FIRST_PDATE:[{min_pub_date} TO {max_pub_date}]'
            query = self._preprint_inclusion_decoration(query)
            article_list = self._search(query)
        else:
            article_list = []
        return article_list

    def _preprint_inclusion_decoration(self, query: str):
        if self.preprint_inclusion == PreprintInclusion.NO_PREPRINT:
            query += ' AND NOT (SRC:"PPR")'
        elif self.preprint_inclusion == PreprintInclusion.ONLY_PREPRINT:
            query += ' AND (SRC:"PPR")'
        return query

    def _search(self, query: str) -> List[Article]:
        logger.debug(f"EuropPMC query: '{query}'")
        articles = self.europe_pmc_service.search(query)
        return articles


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
