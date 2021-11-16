"""The input report is expected to start with a series of rows that include metadata about the report.
The expected order of the metadata rows is given in the argument metadata_keys.
Metadata rows should be strings, with no particular format except for the only mandatory row: 'time_window".
The 'time_window' row should include a statement of the form 'between <date> and <date>' (the format of the date will be guessed).
After the metadata row, the start of the actual data table will be search automatically by searching for a header row.
The regex provided in 'header_signature' should match the begining of every header column in the same order. 
At the minimum, columns should be provided to specify 'manuscript_nm', 'editor', 'decision', 'title', 'authors' for each submission.
This information is manadory and the position index of these columns must be provided in 'feature_index.'
"""
ejp_editor_track_report = {
    # names given to metadata info provided in first lines
    "metadata_keys": [
        "report_name",
        "editors",
        "time_window",  # only mendatory field
        "article_types",
        "creation_date"
    ],
    "feature_index": {
        # these fields are all mendatory
        "manuscript_nm": 0,
        "editor": 2,
        "sub_date": 5,
        "decision": 7,
        "title": 9,
        "authors": 10
    },
    "header_signature": [
        #  regex should be designed to be used with re.match() to detect header line of data table
        # examples:
        # Manuscript number	Manuscript Type	Managing Editor	Reviewing Editor	Reviewers	Submission date	Decision date	Decision Type	Decision Status	Manuscript Title	Author(s)	Decision Type
        # Manuscript	Manuscript Type	Editor	Colleague / EAB	Referee	Submission Date	Final Decision Date	Final Decision Type	Current Status	Manuscript Title	Author(s)	Decision Type
        # Manuscript	Manuscript Type	Editor	Monitoring Editor	Reviewer	Submission Date	Final Decision Date	Final Decision Type	Current Status	Manuscript Title	Author(s)	Decision Type
        # Manuscript	Manuscript Type	Editor	Monitoring Editor	Referee	Submission Date	Final Decision Date	Final Decision Type	Current Status	Manuscript Title	Author(s)	Decision Type
        # Manuscript	Manuscript Type	Editor	Monitoring Editor	Referee	Submission Date	Final Decision Date	Final Decision Type	Current Status	Manuscript Title	Author(s)	Decision Type
        r"manu", r"manu", r".*ed", r".*editor|colleague", r"reviewer|referee",
        r"sub", r".*decision", r".*decision", r".*status", r".*title",
        r"auth", r".*decision"
    ],
    # regex to filter rows to include only decisions to be considered
    "decisions_considered": r"(accept)|(reject)|(suggest posting of reviews)"
}


ejp_query_tool_matchpub_report = {
    # names given to metadata info provided in first lines
    "metadata_keys": [],
    "feature_index": {
        # these fields are all mandatory
        "manuscript_nm": 0,
        "editor": 1,
        "sub_date": 2,
        "journal_decision": 3,
        "title": 4,
        "authors": 5,
        "abstract": 6,
        "avg_time_to_secure_rev": 7,
        "min_time_to_secure_rev": 8,
        "referee_number": 9,
        "ping_response": 10,
    },
    #  regex should be designed to be used with re.match() to detect header line of data table
    "header_signature": [
        r"manuscript_nm", r"editor", r"sub_date", r"journal_decision", r"title",
        r"authors", r"abstract",
        r"avg_time_to_secure_rev", r"min_time_to_secure_rev", r"referee_number",
        r"ping_response",
    ],
    # regex to filter rows to include only decisions to be considered
    "decisions_considered":
        r"(accept)|(reject)|(suggest posting of reviews)",
}
