Matchpub scans the literature to retrieve papers that were handled by a journal and analyze their fate (where they were published) and citation distribution as a function of the editorial decision made by the journal (accept, reject, ...).

As input, MatchPub ingests the eJP report entitled "Editor Track Record Report" in Excel .xls format.

Content of published papers is retrieved from EuropePMC.

Citations data are obtained from Scopus.

Clone the repository.

Before building the application, install docker and docker-compose (https://www.docker.com/get-started).

Build the application:

    docker-compose build

Download the eJP report into the `data/` directory.

Run:

    docker-compose run --rm matchpub
    python -m src.scan /data/to/ejp_report.xls> /results/to/result/>

In addition to the specified `<result>.xlsx` file, MatchPub will save a `<result>-not-found.xlsx> file` with the list of papers that could not be matched.
