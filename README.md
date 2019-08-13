Matchpub scans the literature to retrieve papers that were handled by a journal and analyze their fate (where they were published) and citation distribution as a function of the editorial decision made by the journal (accept, reject, ...).

Components:

- load and parse the list of a manuscripts handeled by the journal, including title, author list and decision type.
- manage the data in a (local?) relational database.
- retrieve asynchronously best matching papers from EuropePMC using their webservice.
- retrieve citation data from Scopus through their public API.
- analyze the distribution of journals where manuscripts were published.
- analyze the distribution of citations of the retrieved papers.
- visualize the results.

