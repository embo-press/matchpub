Matchpub scans the literature to retrieve papers that were handled by a journal and analyze their fate (where they were published) and citation distribution as a function of the editorial decision made by the journal (accept, reject, ...).

Components:

- load and parse the list of a manuscripts handeled by the journal, including title, author list and decision type.
- manage the data in a (local?) relational database.
- retrieve asynchronously best matching papers from EuropePMC using their webservice.
- retrieve citation data from Scopus through their public API.
- analyze the distribution of journals where manuscripts were published.
- analyze the distribution of citations of the retrieved papers.
- visualize the results.


Create, activate and install environment:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Scan EuropPMC by title authors or with a list of submissions:


    python -m src.scan --help


Obtain citation data from scopus for given article with PMID:

    python -m src.citations --help


Example:
 
    python -m src.scan -f data/msb_test_100.xls
    python -m src.scan "Mammoth genomes hold recipe for Arctic elephants"
    python -m src.scan "deep learning" "theis"
    python -m src.citations 30971806

