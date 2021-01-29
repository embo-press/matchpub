import string
import re
import html
import unicodedata
from bs4 import BeautifulSoup
from typing import List, Set


def normalize(s: str, do_not_remove: List[str] = []) -> str:
    """Normalizes a string but setting to lowcase, removing special characters, punctuations and html tags.

    Args:
        s (str): the string to normalize.
        do_not_remove (List[str]): a list of single characters that should not be removed when punctuation is removed. Useful to keep hyphens or apostrophies
    """
    # https://towardsdatascience.com/nlp-building-text-cleanup-and-preprocessing-pipeline-eba4095245a0
    # strip white space
    s = s.strip()
    # lower case
    s = s.lower()
    # remove html entities
    s = html.unescape(s)
    # remove html tags, <i> or <sup> are not rare in titles
    s = BeautifulSoup(s, 'html.parser').get_text()
    # remove punctuation
    punctuation = string.punctuation
    for c in do_not_remove:
        punctuation.replace(c, '')
    s = re.sub(f"[{punctuation}]", " ", s)  # Note: hyphens are NOT removed
    # remove accents, non breaking spaces, en-dash, em-dash, minus, special characters,
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    return s


def process_authors(authors: List[str]) -> List[List[str]]:
    authors = [normalize(au, do_not_remove=['-', "'"]) for au in authors]  # tremove punctuation exluding hyphens
    authors = [re.sub(r"^(van der |vander |van den |vanden |van |von |de |de la |del |della |dell')", r'', au) for au in authors]  # pPMCArticles
    authors = [re.sub(r"^(mac|mc) ", r"\1", au) for au in authors]  # mc intosh mc mahon
    authors = set(authors)  # unique normalized names
    authors = split_composed_names(authors)  # needs to be done first since hyphens would be removed by normalization
    return authors


def split_composed_names(authors: List[List[str]]):
    expanded_author_list = []
    for last_name in authors:
        alternatives = [last_name]
        if '-' in last_name:  # composed name
            sub_names = last_name.split('-')
            alternatives.extend(sub_names)  # store individual names
            alternatives.append('-'.join([sub_names[1], sub_names[0]]))  # invert composed name
        expanded_author_list.append(alternatives)
    return expanded_author_list


def flat_unique_set(x: List[List[str]]) -> Set[str]:
    flattened = [element for alt in x for element in alt]
    return set(flattened)


def binarize(v, bin_number, bin_size):
    bins = [[i * bin_size, (i + 1) * bin_size] for i in range(0, bin_number)]
    return bins, [len([e for e in v if e >= bin[0] and e < bin[1]]) for bin in bins]
