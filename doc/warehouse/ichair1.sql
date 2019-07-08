-- Generic joining of the various tables to get the data
-- into a format similar to how you discussed with Mark.

SELECT campus AS CMP
        , subject_course AS COURSE
        , course_reference_number AS CRN
        , course AS TITLE
        , section_credit_hours AS CREDHRS
        , section_capacity AS ENRLCAP
        , section AS [SESSION]
        , replace(days_of_week, '-', '') AS [DAYS], --'TR' as [DAYS]
    left(dmt.start_time, 2) + ':' + right(dmt.start_time, 2) + '-' + left(dmt.end_time, 2) + ':' +
        right(dmt.end_time, 2) AS [TIME], --'14:00-15:20' as [TIME]
    primary_df.last_name AS primary_instructor
        , --,secondary_df.last_name as secondary_instructor
    part_of_term
--		,dcs.*
FROM dw.dim_course_section dcs -- Use the course section dimension as base.
-- Meeting times
         INNER JOIN dw.fact_course_meeting fcm ON (dcs.course_section_key = fcm.course_section_key)
         LEFT OUTER JOIN dw.dim_meeting_time dmt ON (fcm.meeting_time_key = dmt.meeting_time_key)
-- Primary and Secondary Instructors
         INNER JOIN dw.fact_faculty_course primary_ffc ON (dcs.course_section_key = primary_ffc.scheduled_course_key AND
    primary_ffc.primary_instructor = 1) -- Check fact table for primary instructors
--left outer join dw.fact_faculty_course secondary_ffc on (dcs.course_section_key=secondary_ffc.scheduled_course_key and secondary_ffc.secondary_instructor=1) -- Check fact table for secondary instructors
         LEFT OUTER JOIN dw.dim_faculty primary_df ON (primary_ffc.faculty_key = primary_df.faculty_key)
-- Pull the primary name from the faculty dimension
--left outer join dw.dim_faculty secondary_df on (secondary_ffc.faculty_key=secondary_df.faculty_key) -- Pull the secondary name from the faculty dimension
