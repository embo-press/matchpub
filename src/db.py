'''
Strucutre of the database tables and API? for the database used by Matchpub

Basic suggested structure:

    #This table is to capture metadata for each analysis run by matchpub
    table 'analysis':
        Field('journal','text'),
        Field('description','text'),
        Field('analysis_date','date'),
        Field('eJPReportFile','upload',custom_retrieve=retrieve_file,requires=IS_NOT_EMPTY()),
        Field('eJPReportInfo'),
        Field('start_date', 'date'),
        Field('end_date', 'date'),
        Field('numberOfSubmissions','integer',default=0, label="Submission number"),
        Field('process_uuid',default=""))


    #the fields of this table are exactly the fields of the eJP 'Keywords Report'
    table 'submission':
        Field('analysisID','reference analysis'),
        Field('processed','string',default = 'no'),
        Field('Manuscript'),
        Field('ManuscriptType'),
        Field('Editor'),
        Field('MonitoringEditor'),
        Field('Referee'),
        Field('SubmissionDate'),
        Field('FinalDecisionDate'), 
        Field('FinalDecisionType'),
        Field('CurrentStatus'),
        Field('ManuscriptTitle'), 
        Field('Authors'),
        Field('DecisionType'),
        Field('Decision', compute = map_decision),
        Field('Abstract', default='abstract not available'))


    #this table includes the PubMed records retrieved
    table 'retrieved':
        Field('submissionID','reference submission'),
        Field('analysisID','reference analysis'),
        Field('pmid'),
        Field('doi'),
        Field('journalname'),
        Field('year'),
        Field('month'),
        Field('pubmedTitle'),
        Field('abstract','text'),
        Field('authors'),
        Field('citedByCount', 'integer'),
        Field('validated',default='unvalidated'))
'''