import requests
import json
import argparse

SCOPUS = 'https://api.elsevier.com/content/search/scopus'
API_KEY = '22920558ed72ad0eb2f46cce0d2e3cc8'
# https://api.elsevier.com/content/search/scopus?query=all(gene)&apiKey=7f59af901d2d86f78a1fd60c1bf9426a
# http://api.elsevier.com/content/search/scopus?query=PMID(22136928)&field=citedby-count
# https://dev.elsevier.com/tecdoc_cited_by_in_scopus.html

def citedby_count(pmid):
	citation_count = None
	if pmid: 
		params = {"apiKey": API_KEY, "query": "PMID({})".format(str(pmid)), "field": "citedby-count"}
		try:
			r = requests.post(SCOPUS, data=params)
			data = r.json()
			matches = int(data['search-results']['opensearch:totalResults'])
			if matches == 1:
				citation_count = int(data['search-results']['entry'][0]['citedby-count'])
		except Exception as e:
			print('Something went wrong with {}'.format(pmid))
			print(e)
	return citation_count
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser( description="searches SCOPUS for matching PMID and retuns citedby count" )
    parser.add_argument('pmid', help="The pmid of the article to be searched for (test it with 16729048).")
    args = parser.parse_args()
    pmid = args.pmid
    print(citedby_count(pmid))
