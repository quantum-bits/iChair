-- Join and select data to make it appear in an associative table.
-- Just shows that it's doable.

-- Pull back term, course, instructor, instuctor_type in an associative table structure
SELECT dcs.term_code,
    dcs.course_reference_number,
    pidm AS instructor_pidm,
    CASE WHEN primary_instructor = 1
             THEN 'Primary'
         ELSE 'Secondary' END AS instructor_type
--*
FROM dw.fact_faculty_course ff
    -- Same joins as ichair 1, just reduced to hide other fields and make it appear as an associative table.
         INNER JOIN dw.dim_faculty df ON ff.faculty_key = df.faculty_key
         INNER JOIN dw.dim_course_section dcs ON (dcs.course_section_key = ff.scheduled_course_key)
