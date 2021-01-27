import string
import re
import html
import unicodedata


def normalize(s: str) -> str:
    # strip white space
    s = s.strip()
    # lower case
    s = s.lower()
    # remove html entities
    s = html.unescape(s)
    # remove punctuation
    s = re.sub(f"[{string.punctuation}]", " ", s)  # Note: this removes hyphens as well
    # remove accents, non breaking spaces, en-dash, em-dash, minus, special characters, 
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    return s


def binarize(v, bin_number, bin_size):
    bins = [[i * bin_size, (i + 1) * bin_size] for i in range(0, bin_number)]
    return bins, [len([e for e in v if e >= bin[0] and e < bin[1]]) for bin in bins]
