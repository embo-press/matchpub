import requests
import argparse

from . import logger

SCOPUS = 'https://api.elsevier.com/content/search/scopus'
API_KEY = '22920558ed72ad0eb2f46cce0d2e3cc8'
# https://api.elsevier.com/content/search/scopus?query=all(gene)&apiKey=7f59af901d2d86f78a1fd60c1bf9426a
# https://dev.elsevier.com/tecdoc_cited_by_in_scopus.html


def citedby_count(pmid):
    citation_count = None
    if pmid:
        params = {"apiKey": API_KEY, "query": f"PMID({str(pmid)})", "field": "citedby-count"}
        try:
            r = requests.post(SCOPUS, data=params)
            data = r.json()
            matches = int(data['search-results']['opensearch:totalResults'])
            if matches == 1:
                citation_count = int(data['search-results']['entry'][0]['citedby-count'])
        except Exception:
            logger.error('Something went wrong with {pmid}')
    return citation_count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="searches SCOPUS for matching PMID and retuns citedby count")
    parser.add_argument('pmid', nargs="?", default="29088127", help="The pmid of the article to be searched for (test it with 16729048).")
    args = parser.parse_args()
    pmid = args.pmid
    print(citedby_count(pmid))
