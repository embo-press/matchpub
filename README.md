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

To run the interactive visualization in a Jupyter notebook:

    docker-compose up
    # use link: http://127.0.0.1:8888/?token=<...> to access the notebook

Shut down with Ctrl-C

## Settings

Some settings can be changed in `src/config.py`. 

To scan only preprints, set `preprint_inclusion` to `PreprintInclusion.ONLY_PREPRINT`.

To avoid the inclusion of citation data, set `include_citations` to `False` or invoke the src.scan with the `--no_citations` option.

The path to a customized description of the format of the input file can be specified with `input_description_file`.

The input description file is expected to be a Python dictionary. The default description and its documentation is provided in `src/description.py`.


