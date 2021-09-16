# Intro

MatchPub2 scans the literature to retrieve papers that were handled by a journal and analyzes their fate (where they were published) and citation distribution as a function of the editorial decision made by the journal (accept, reject, ...).

As input, MatchPub2 ingests the data produced with the eJP SQL query `queries/matchpub.sql` in `.xls` format.

Content of published papers is retrieved from EuropePMC.

Citations data are obtained from Scopus.

## To install the application:

Clone this repository.

Update `.env.example` with your user id (`id -u`) and group id (`id -g`), your Scopus API_Key (register at https://dev.elsevier.com/).
If MatchPub2 is intendended to answer automatically email requests, include imap, smtp, email crendentials as well.
Save under `.env`

Install `docker` and `docker-compose` (https://www.docker.com/get-started).

Build the application:

    docker-compose build

Download the eJP report into the `data/` directory (or `/data` from within the container since `data/` is bind mounted to the container's `/data` volume).

## Run a scan

Run a scan from the command line. It can be convenient to do this from a tmux session:

    docker-compose run --rm matchpub bash
    python -m src.scan /data/to/ejp_report.xls> /results/to/result/> # use --no_citations to prevent inclusion of citation data.

To obtain debug-level information run the scan with `-D` option.

In addition to the specified `<result>.xlsx` file, MatchPub will save a `<result>-not-found.xlsx> file` with the list of papers that could not be matched. Graphical reports will be saved in `/reports`.

To rune the visualization in a Jupyter notebook:

    docker run --rm -p 0.0.0.0:8888:8888 -v $PWD/data:/data -v $PWD/results:/results  -v $PWD/reports:/reports -v $PWD/:/app  matchpub


## Experimental

Alternatively, send eJP reports by email and monitor email account to send back results:

Start the app to scan an email account and to reply automatically to incoming emails with the eJP report delivered as attachment:

    docker-compose run --rm matchpub

The application enters the 'idle' mode and monitors incoming emails:

    Starting matchpub2_matchpub_1 ... done
    Attaching to matchpub2_matchpub_1
    matchpub_1  | INFO - checking email from lemberge@embl.de
    matchpub_1  | INFO - login successful
    matchpub_1  | INFO - checking email from lemberge@embl.de
    matchpub_1  | INFO - checking INBOX.matchpub
    matchpub_1  | INFO - INBOX.matchpub contains 4 messages, 0 recent.
    matchpub_1  | INFO - server entered idle mode.


## Settings

Some settings can be changed in `src/config.py`. 

To scan only preprints, set `preprint_inclusion` to `PreprintInclusion.ONLY_PREPRINT`.

To avoid the inclusion of citation data, set `include_citations` to `False` or invoke the src.scan with the `--no_citations` option.

The path to a customized description of the format of the input file can be specified with `input_description_file`.

The input description file is expected to be a Python dictionary. The default description and its documentation is provided in `src/description.py`.


