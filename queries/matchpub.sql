SELECT DISTINCT
-- Report ingested by MatchPub2 to analyze the fate of manuscript.
-- Only research article, reports, resources and methods are analyzed.
-- 
    sub.cmpt_ms_nm AS manuscript_nm,
    pEditor.last_nm AS editor,
    sub.qc_complete_dt AS sub_date,
    final.journal_decision_txt AS journal_decision, -- this will allow filtering and aggreg by regex
    CAST(final.ms_title AS NVARCHAR(4000)) AS title,
    author_list.last_names AS authors,
    CAST(final.abstract AS NVARCHAR(4000)) AS abstract,
    review_data.avg_time_to_secure_rev AS avg_time_to_secure_rev,
    review_data.min_time_to_secure_rev AS min_time_to_secure_rev,
    review_data.referee_number AS referee_number

FROM
    Journal jou
        JOIN Manuscript sub ON
            sub.j_id = jou.j_id 
            AND sub.ms_rev_no = 0  -- initial submission
            AND sub.current_stage_id NOT IN (840, 850)
        JOIN Manuscript final ON
            final.j_id = jou.j_id
            AND final.ms_id = sub.ms_id
            -- limit to accepted papers only
            -- AND final.final_decision_ind = 1
            -- alternative: limit to manu with a final decision
            AND final.final_decision_ind in (1, 4)  -- has a decision accept or reject
            AND final.current_stage_id NOT IN (840, 850)  -- not halted not withdrawn, probably dispensable
        JOIN Person pEditor ON pEditor.p_id = sub.primary_ed_p_id
        -- all of the following gynmastics is to avoid duplicate last names 
        -- DISTINCT in STRING_AGG() would be simpler by is not possible!!!
        JOIN (
            SELECT
                STRING_AGG(authors.last_name, ', ') AS last_names,
                authors.ms_id as ms_id,
                authors.j_id as j_id
            FROM
                (
                    SELECT DISTINCT
                        p.last_nm AS last_name,
                        ms.ms_id,
                        ms.j_id
                    FROM
                        Person p,
                        Author author,
                        Manuscript ms
                    WHERE
                        p.p_id = author.p_id
                        AND author.j_id = ms.j_id
                        AND author.ms_id = ms.ms_id
                ) authors
            GROUP BY
            authors.ms_id,
            authors.j_id
        ) author_list ON author_list.ms_id = sub.ms_id AND author_list.j_id = jou.j_id
        -- aggregate data on review per manuscript when available (hence LEFT JOIN)
        LEFT JOIN (
            SELECT
                ms.j_id AS j_id,
                ms.ms_id AS ms_id,
                AVG(CAST(DATEDIFF(day, ms.qc_complete_dt, r.rev_start_dt) AS FLOAT)) AS avg_time_to_secure_rev,
                MIN(DATEDIFF(day, ms.qc_complete_dt, r.rev_start_dt)) AS min_time_to_secure_rev,
                COUNT(DISTINCT r.p_id) AS referee_number
            FROM 
                Reviewer r,
                Manuscript ms
            WHERE
                r.j_id = ms.j_id AND r.ms_id = ms.ms_id AND r.ms_rev_no = 0 AND ms.ms_rev_no = 0  -- review data only on initial submission
            GROUP BY
                ms.j_id, ms.ms_id
        ) review_data ON review_data.j_id = jou.j_id AND review_data.ms_id = sub.ms_id

WHERE
    -- pick the journal of interst or use all of them
    jou.j_abbrev = 'msb' -- IN ('emboj', 'embor', 'msb', 'embomolmed')  'lsa', 'reviewcommons
    -- include only research articles, reports, methods
    AND
    -- selecting for research papers using the manuscript type of the final (important!) manu
    (
        (jou.j_abbrev = 'emboj' AND final.ms_type_cde IN (1, 19))  -- articles, resources
        OR
        (jou.j_abbrev = 'embor' AND final.ms_type_cde IN (1, 29, 36))  -- articles, reports, resources
        OR
        (jou.j_abbrev = 'msb' AND final.ms_type_cde IN (1, 2, 19))  -- articles, reports, method
        OR
        (jou.j_abbrev = 'embomolmed' AND final.ms_type_cde IN (10, 13, 28))  -- articles, reports
        OR
        (jou.j_abbrev = 'reviewcommons' AND final.ms_type_cde = 1)  -- articles
        OR
        (jou.j_abbrev = 'lsa' AND final.ms_type_cde IN (1, 2, 3, 13, 16, 19, 20, 29))  -- articles, methods, Resource, not used, not used, not used, 
    )
    -- time interval based on QC
    AND sub.qc_complete_dt BETWEEN '2019-01-01' AND '2019-12-31'
    -- time interval based on final decision date
    -- AND final.final_decision_dt BETWEEN '2019-01-01' AND '2021-07-31'

ORDER BY
    manuscript_nm