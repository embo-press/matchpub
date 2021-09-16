
from typing import Dict, List
from time import sleep

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from lxml.etree import fromstring, ParseError

from .models import Article
from . import logger, SCOPUS_API_KEY


def requests_retry_session(
    retries=4,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    """Creates a resilient session that will retry several times when a query fails.
    from  https://www.peterbe.com/plog/best-practice-with-retries-with-requests

    Usage:
        session_retry = self.requests_retry_session()
        session_retry.headers.update({
            "Accept": "application/json",
            "From": "thomas.lemberger@embo.org"
        })
        response = session_retry.post(url, data=params, timeout=30)
    """
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class Service:

    REST_URL: str = ''
    HEADERS: Dict[str, str] = {}

    def __init__(self):
        self.retry_request = requests_retry_session()
        self.retry_request.headers.update(self.HEADERS)


class EuropePMCService(Service):

    REST_URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/searchPOST'
    HEADERS = {
        "From": "thomas.lemberger@embo.org",
        "Content-type": "application/x-www-form-urlencoded"
    }

    def search(self, query: str, limit: int = 5) -> List[Article]:
        article_list = []
        params = {
            'query': query,
            'resultType': 'core',
            'format': 'xml',
            'pageSize': limit,
        }
        response = self.retry_request.post(self.REST_URL, data=params, headers=self.HEADERS)
        if response.status_code == 200:
            try:
                xml = fromstring(response.content)
                articles_xml = xml.xpath('.//result')
                article_list = [Article(xml=x) for x in articles_xml]
                logger.debug(f"{len(article_list)} results found.")
            except ParseError:
                logger.error(f"XML parse error with: {params}")
        else:
            logger.error(f"failed query ({response.status_code}) with: {params}")
        return article_list


class BioRxivService(Service):

    REST_URL = "https://api.biorxiv.org/details"
    HEADERS = {
        "From": "thomas.lemberger@embo.org",
        "Accept": "application/json",
    }

    def preprint_publication_status(self, doi: str) -> str:
        for server in ['biorxiv', 'medrxiv']:
            url = f"{self.REST_URL}/{server}/{doi}"
            response = self.retry_request.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('messages', [{}])[0].get('status', '') == 'ok':
                    journal_doi = data.get('collection', [{}])[0].get('published', '')
                    if journal_doi != "NA":  # need to return None when no doi so that DataFrame cell is null
                        return journal_doi
            else:
                logger.debug(f"problem with biorxiv api ({response.status_code}) with doi {doi}")
        return None


class ScopusService(Service):

    REST_URL = 'https://api.elsevier.com/content/search/scopus'
    API_KEY = SCOPUS_API_KEY

    def citedby_count(self, pmid):
        sleep(0.33)  # 3 requests / sec max
        citation_count = None
        if pmid:
            params = {"apiKey": self.API_KEY, "query": f"PMID({str(pmid)})", "field": "citedby-count"}
            response = self.retry_request.post(self.REST_URL, data=params)
            if response.status_code == 200:
                remaining_queries = response.headers.get('X-RateLimit-Remaining')
                if int(remaining_queries) < 10_000:
                    logger.warning(f"more than half of queries consumed. Only {remaining_queries} left!")
                    # raise RuntimeError(f"quota half consumed. Remaining: {remaining_queries}.")
                data = response.json()
                matches = int(data['search-results']['opensearch:totalResults'])
                if matches == 1:
                    citation_count = int(data['search-results']['entry'][0]['citedby-count'])
            else:
                logger.error(f"Something went wrong ({response.status_code}) with pmid:{pmid}:\n{str(response.content)}\n{response.headers}")
        return citation_count
