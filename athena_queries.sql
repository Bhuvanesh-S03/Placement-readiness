-- Run in Athena after the Glue crawler has created placement_db.student_data
-- (set the query result location to s3://analytics-results-bucket-yourname/ first)

-- 1. Top 3 students by readiness score
SELECT studentid, name,
       ROUND(aptitude*0.30 + coding*0.45 + interview*0.25, 2) AS readiness_score
FROM placement_db.student_data
ORDER BY readiness_score DESC
LIMIT 3;

-- 2. Average readiness score
SELECT ROUND(AVG(aptitude*0.30 + coding*0.45 + interview*0.25), 2) AS avg_readiness
FROM placement_db.student_data;

-- 3. Placement-ready students (score >= 70)
SELECT studentid, name,
       ROUND(aptitude*0.30 + coding*0.45 + interview*0.25, 2) AS readiness_score
FROM placement_db.student_data
WHERE aptitude*0.30 + coding*0.45 + interview*0.25 >= 70
ORDER BY readiness_score DESC;

-- 4. Category-wise distribution
SELECT CASE
         WHEN s >= 85 THEN 'Excellent'
         WHEN s >= 70 THEN 'Good'
         WHEN s >= 50 THEN 'Needs Improvement'
         ELSE 'Critical' END AS category,
       COUNT(*) AS students
FROM (SELECT aptitude*0.30 + coding*0.45 + interview*0.25 AS s FROM placement_db.student_data)
GROUP BY 1
ORDER BY students DESC;
