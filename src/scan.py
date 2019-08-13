# © Thomas Lemberger, thomas.lemberger@embo.org

import requests
from unidecode import unidecode
import urllib
import datetime
import time
import re
import argparse
from xml.etree.ElementTree import XMLParser , parse, ParseError, fromstring
from nltk import stem, tokenize
from nltk.metrics import distance
from html.entities import entitydefs, name2codepoint
import string
#from fuzzywuzzy import fuzz, process
from src.citations import citedby_count
from src.load import ImportEJPReport


def a_preprint(xml):
    preprint = False
    try:
        preprint = xml.findtext('.//pubType').lower() == 'preprint'
    except Exception:
        pass
    return preprint

class EuropePMCArticle:

    def __init__(self,a):
        self.pmid = a.findtext('./pmid') or ''
        if a_preprint(a):
            self.journal_name = a.findtext('.//publisher') or ''
        else:
            self.journal_name = a.findtext('./journalInfo/journal/title') or ''
        self.year = a.findtext('./journalInfo/yearOfPublication') or ''
        self.month = a.findtext('./journalInfo/monthOfPublication') or '' #not sure, have to check
        self.title = a.findtext('./title') or ''
        self.doi = a.findtext('./doi') or ''
        self.abstract = a.findtext('./abstractText') or ''
        self.author_list = [au.text for au in a.findall('./authorList/author/lastName')] or ''

class EuropePMCSearch:

    REST_URL='https://www.ebi.ac.uk/europepmc/webservices/rest/searchPOST'
    HEADER = {'Content-type': 'application/x-www-form-urlencoded'}

    def __init__(self, min_date=1970, max_date=3000, include_preprint=False):
        self.dateRange = f"PUB_YEAR:[{str(min_date)} TO {str(max_date)}]"
        self.include_preprint = include_preprint

    def search_by_author(self,authorList):
        names = ' AND '.join(['(' + ' OR '.join([f'AUTH:"{au}"' for au in alternatives]) + ')' for alternatives in authorList])
        query = f"({names}) AND {self.dateRange}"
        # query = urllib.parse.quote(query) # apparently not needed
        articleList = self.search_PMC(query)
        return articleList

    def search_by_title(self,title):
        query = f'TITLE:"{title}" AND {self.dateRange}'
        # query = urllib.parse.quote(query)
        articleList = self.search_PMC(query)
        return articleList

    def search_PMC(self, query):
        articleList = []
        params = {
            'resultType': 'core',
            'query': query,
            'format': 'xml'
        }
        try:
            response = requests.post(self.REST_URL, data=params, headers=self.HEADER)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                try:
                    xml = fromstring(response.text)
                    articles = xml.findall('.//result')
                    articleList = [EuropePMCArticle(a) for a in articles if self.include_preprint or not a_preprint(a)]
                except ParseError:
                    print(f"XML parse error with: {params['query']}")
            else:
                print(f"query failed (status_code={response.status_code}) with {params['query']}")
        except Exception as e:
            print(f"query failed with {params['query']}")
            print(e)
        return articleList

##
# from http://effbot.org/zone/re-sub.htm#unescape-html
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.
def unescape(text):
	def fixup(m):
		text = m.group(0)
		if text[:2] == "&#":
			# character reference
			try:
				if text[:3] == "&#x":
					return chr(int(text[3:-1], 16))
				else:
					return chr(int(text[2:-1]))
			except ValueError:
				pass
		else:
			# named entity
			try:
				text = chr(name2codepoint[text[1:-1]])
			except KeyError:
				pass
		return text # leave as is
	return re.sub(r"&#?\w+;", fixup, text)


#modified from http://streamhacker.com/2011/10/31/fuzzy-string-matching-python/
def normalize(s):
	#remove punctuation
	s = re.sub(f"[{string.punctuation}]", " ", s)
	stemmer = stem.PorterStemmer()
	#words = tokenize.word_tokenize(s.lower().strip())
	words = tokenize.wordpunct_tokenize(s.lower().strip())
	return ' '.join([stemmer.stem(w) for w in words])

def fuzzy_match(s1, s2):
	dist = float(distance.edit_distance(normalize(s1), normalize(s2)))
	return 100*(1-dist/max(len(s1),len(s2)))

def argmax(l):
	# https://towardsdatascience.com/there-is-no-argmax-function-for-python-list-cd0659b05e49
	return max(range(len(l)), key=lambda i: l[i])

def fuzzy_best_match(query, alternatives):
	score_list = [fuzzy_match(query, title) for title in alternatives]
	i = argmax(score_list)
	return i, score_list[i]

def split_author_list(author_list):
    l = author_list.split(', ')
    l = [re.sub('-corr', '', n).strip() for n in l] # corresponding authors are flagged with '-corr' by eJP
    l = list(set(l)) # remove duplicated names
    return l

def parse_composed_names(last_name):
    sub_names = last_name.split('-')
    alternatives = [last_name]
    if len(sub_names) == 2:
        alternatives.append(sub_names[0])
        alternatives.append(sub_names[1])
        alternatives.append(sub_names[1] + '-' + sub_names[0]) # inverse the order in case there are variations
    return alternatives

def process_authors(author_list):
    unique_authors = list(set(author_list))
    authors = []
    for author in unique_authors:
        # deal with particles van von vanden de Mc etc...
        last_name = re.search(r"(van der |van den |van |von |de |del |mac |mc )?\S+$", author.lower().strip()).group(0)
        # remove HTML/XML escaped entities that encode special characters
        last_name = unescape(last_name)
        # try to remove all accents both in submitted and pubmed with unidecode?
        # last_name = unidecode.unidecode(last_name) # not sure it works better when used as query; use when comparing
        # deal with composed names such as Jones-Jonhson or Johnson-Jones
        alternatives = parse_composed_names(last_name)
        authors.append(alternatives)
    return authors

def cleanup_title(title):
    title = title.strip().lower()
    title = unescape(title)
    title = re.sub("[\u2212\u2013\u2014]", "-", title) # remove minus en-dashes em-dashes
    title = re.sub("[\u00A0]", " ", title) # remove nonbreaking spaces
    title = title.replace(':', ' ') #need to remove ':' from title otherwise PMC REST API chokes!
    # title = unidecode(title) # better?
    return title
                     
def best_match_by_title(articles, submitted_title, submitting_authors, threshold=39, pubmed_vs_submitted=3):
    if articles:
        titles = [cleanup_title(a.title) for a in articles]
        if titles:
            index_of_best_matching_title, score = fuzzy_best_match(submitted_title, titles)
            # score > 45 is more inclusive; 80 much more specific
            if score > threshold:
                best_matching_article = articles[index_of_best_matching_title]
                pubmed_authors = best_matching_article.author_list
                diff = len(pubmed_authors) - len(submitting_authors)
                #if there are three times more authors on the pubmed retrieved paper than on the submission, it is unlikely to be correct
                if diff <= pubmed_vs_submitted:
                    return best_matching_article
    return False

def best_match_by_author(articles, submitted_title, submitting_authors, threshold=60):
    if articles: 
        best_match = articles[0] # pmc returns results sorted by relevance
        if best_match is not None:
            title = cleanup_title(best_match.title)
            score = fuzzy_match(title, submitted_title)
            pubmed_authors = best_match.author_list
            pubmed_authors = list(set(pubmed_authors))
            pubmed_authors = process_authors(pubmed_authors)
            # alternatives included ; list needs to be flattened first
            s1 = set([au for alternatives in pubmed_authors for au in alternatives])
            s2 = set([au for alternatives in submitting_authors for au in alternatives])
            author_overlap = len(s1 & s2)
            #at least one author should be in the submitting authors
            #and check on title similarity other can get irrelevant stuff
            if author_overlap > 0 and score >= threshold:
                return best_match
    return False

class Retriever:

    def __init__(self, db, submissions, analysisID, min_date='1994', max_date='3000'):
        #the database
        self.db=db
        #the table where submissions are stored
        self.submissions=submissions
        #the ID that allows to select the submissions belonging to the current analysis
        self.analysisID=analysisID
        self.max_date = max_date
        self.min_date = min_date
        self.pmc = EuropePMCSearch(self.min_date, self.max_date, include_preprint=False)

    def retrieve(self, record):
            result = []
            best_match = False
            submitted_title = record['ManuscriptTitle']
            submitted_title = cleanup_title(submitted_title)
            submitting_authors = record['Authors']
            submitting_authors = split_author_list(submitting_authors)
            submitting_authors = process_authors(submitting_authors)
            # search by author first
            articles = self.pmc.search_by_author(submitting_authors)
            # from those returned by pmc, find then best match based on title
            best_match = best_match_by_title(articles, submitted_title, submitting_authors) 
            if not best_match: 
                # search by title first
                articles = self.pmc.search_by_title(submitted_title)
                # from those returned by pmc, find the best match based on authors
                best_match = best_match_by_author(articles, submitted_title, submitting_authors)
 
            if best_match:
                citations = citedby_count(best_match.pmid)
                result = {
                    'submissionID': int(record['id']),
                    'analysisID': self.analysisID,
                    'pmid':  best_match.pmid,
                    'doi': best_match.doi,
                    'journalname': best_match.journal_name,
                    'year':  best_match.year,
                    'month': best_match.month,
                    'pubmedTitle': best_match.title,
                     #TODO: append all .//AbstractText
                     #' '.join(e.text for e in a.findall('.//AbstractText'))
                    'abstract': best_match.abstract,\
                    'authors':', '.join(best_match.author_list),
                    'citedByCount': citations
                }
            time.sleep(0.1) # hundred milliseconds delay to make sure not to saturate the webservice
            return result

    def scan_from_db(self):

        #if for some reason the analysis was interrupted, it continues only with the rows that were not yet processed
        unprocessed_rows = self.db(
            (self.submissions.analysisID == self.analysisID) & 
            (self.submissions.processed == 'no') #&
            #(self.submissions.Decision in ['accept', 'reject post-review', 'reject pre-review'])
        ).select()
        n = 0
        for row in unprocessed_rows:
            match = self.retrieve(row)
            if match:
                self.db.retrieved.insert(**match)
                n += 1
            self.submissions[row.id] = dict(processed='yes')
            self.db.commit()
        return n
    
    def scan_from_file(self):
        results = []
        for row in self.submissions:
            match = self.retrieve(row)
            if match:
                results.append(match)
        return results


def main():
    parser = argparse.ArgumentParser( description="searches EuropePMC")
    parser.add_argument('title', nargs="?", help="The title of the article to be searched for.")
    parser.add_argument('authors', nargs="?", help="the comma-separated list of authors' last names")
    parser.add_argument('-f', '--file', default="", help="path to an ejp report")
    args = parser.parse_args()
    filepath = args.file
    title = args.title
    authors = args.authors
    if filepath:
        metadata, submissions = ImportEJPReport().load(0, filepath)
        submissions = [{'id': i, **s} for i, s in enumerate(submissions)]
        retriever = Retriever(None, submissions, 0)
        results = retriever.scan_from_file()
        print(metadata)
        for r in results:
            print("="*40)
            for k in r:
                print(f"{k}:")
                print(r[k])
                print()
        print("="*40)
        print(f"retrieved {len(results)} results out of {len(submissions)} submissions.")
        print("="*40)
    elif authors is not None:
        retriever = Retriever(None, None, 0)
        record = {'id': '0', 'ManuscriptTitle': title, 'Authors': authors}
        results = retriever.retrieve(record)
        for k in results:
            print(f"{k}:")
            print(results[k])
            print()
    else:
        rep = EuropePMCSearch()
        articles = rep.search_by_title(title)
        a = articles[0]
        print(a.doi)
        print(a.title)
        print(a.journal_name)
        print(a.author_list)
        print(a.abstract)
        print(a.year)

if __name__ == '__main__':
    main()
    
