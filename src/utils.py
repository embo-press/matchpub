import string
import re
import html
import unicodedata
from typing import List, Set

from bs4 import BeautifulSoup


def normalize(
    s: str,
    do_not_remove: str = '',
    do: List[str] = [
        'ctrl', 'strip', 'lower', 'html_unescape', 'html_tags',
        'punctuation', 'unicode'
    ]
) -> str:
    """Normalizes a string, setting to remove control characters, set to lower case, removing special characters, punctuations and html tags.

    Args:
        s (str): the string to normalize.
        do_not_remove (List[str]): a list of single characters that should NOT be removed when punctuation is removed. Useful to keep hyphens or apostrophies
        do (List[str]): the list of cleanup steps to do from 'ctrl', 'strip', 'lower', 'html_unescape', 'html_tags', 'punctuation', 'unicode'
    """
    def remove_control_characters(s: str, excluded: List[str] = ["Cc", "Cf"]) -> str:
        # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
        clean = "".join([ch for ch in s if unicodedata.category(ch) not in excluded])
        return clean

    # https://towardsdatascience.com/nlp-building-text-cleanup-and-preprocessing-pipeline-eba4095245a0
    # remove control characters
    if 'ctrl' in do:
        s = remove_control_characters(s)
    # strip white space
    if 'strip' in do:
        s = s.strip()
    # lower case
    if 'lower' in do:
        s = s.lower()
    # remove html entities
    if 'html_unescape' in do:
        s = html.unescape(s)
    # remove html tags, <i> or <sup> are not rare in titles
    if 'html_tags' in do:
        s = BeautifulSoup(s, 'html.parser').get_text()
    # remove punctuation
    if 'punctuation' in do:
        punctuation = string.punctuation
        for c in do_not_remove:
            punctuation = punctuation.replace(c, ' ')
        s = re.sub(f"[{punctuation}]", " ", s)
        s = re.sub(r" +", " ", s)  # remove runs of spaces if any
    # remove accents, non breaking spaces, en-dash, em-dash, minus, special characters,
    if 'unicode' in do:
        s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    return s


def last_name(name: str) -> str:
    """Extracts the last name from a <first names last name> string. Includes particles such as von, del, saint, mac, ...

    Args:
        name (str): a string with first names last names in this order.

    Returns:
        (str): the last name including its particle
    """
    match = re.search(r"((?<= )|(?<=^))(mc |mac |van ?der |van ?den |van |van't |von ?der |von |de |de la |del |della |dell'|st |saint |t'|n')?\S+$", name)
    try:
        last_name = match.group(0)
    except Exception:
        import pdb; pdb.set_trace()
    return last_name


def process_authors(authors: List[str]) -> List[List[str]]:
    """The list of author last names is processed to remove special chacaters and deal with composed names and names with particles.
    Composed names are expanded into a list of alternatives.
    Args:
        authors (List[str]): the list of author last names.

    Returns:
        (List[List[str]]): a list of possible alternatives for each cleaned up last name.
    """
    authors = [normalize(au, do_not_remove="-'") for au in authors]  # tremove punctuation exluing hyphens; beneficial
    # authors = [re.sub(r"^(van der |vander |van den |vanden |van |von |de |de la |del |della |dell' |st |saint )", r'', au) for au in authors]
    # authors = [re.sub(r"^(mac|mc) ", r"\1", au) for au in authors]  # mc intosh mc mahon
    authors = set(authors)  # unique normalized names
    authors = split_composed_names(authors)  # this is beneficial on recall on positives
    # generates alternatives with mc mac
    return authors


def split_composed_names(authors: List[str]) -> List[List[str]]:
    """Composed last names, eg 'Villanueva-Meyer', are split and expanded into four alternatives:
    'Villanueva-Meyer' 'Meyer-Villanueva', 'Meyer', 'Villanueva' to maximize chance to retrieve papers.
    For composed names including very short name, for exampl El-Baradei, the 1 or 2 character long names are dropped as it may generates noise in search results.

    Args:
        authors (List[str]): the list of last names

    Returns:
        (List[List[str]]): a list of list of alternatives.
    """
    expanded_author_list = []
    for last_name in authors:
        alternatives = [last_name]  # original name
        if '-' in last_name:
            sub_names = last_name.split('-')  # split composed name)
            sub_names = list(filter(lambda name: len(name) > 2, sub_names))  # remove super short subnames like El- Al- or A-
            alternatives.extend(sub_names)  # individual names
            if len(sub_names) == 2:
                alternatives.append('-'.join([sub_names[1], sub_names[0]]))  # invert composed name
        expanded_author_list.append(alternatives)
    return expanded_author_list


def flat_unique_set(x: List[List[str]]) -> Set[str]:
    """Flattens a list of list and remove duplicates.

    Args:
       x (List[List[str]]): the list of lists.

    Returns:
       (Set[str]): the flattened deduplicated set.
    """
    flattened = [element for alt in x for element in alt]
    return set(flattened)


ed_rej_matcher = re.compile(
    r"(reject before.*)|(reject and refer.*)|(reject with.*)|(editorial rej.*)",
    re.IGNORECASE
)
post_review_rej_matcher = re.compile(
    r"(reject post.*)|(rejection$)|(reject$)|(.*border line reject)",
    re.IGNORECASE
)
accept_matcher = re.compile(r"accept", re.IGNORECASE)
