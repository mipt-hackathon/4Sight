/*
Purpose:
  Build histogram-ready CV buckets for the corrected ABC/XYZ notebook analysis.

Expected inputs:
  - mart.abc_xyz

Expected outputs:
  - mart.abc_xyz_cv_distribution

Grain:
  - one row per cv bucket
*/

DROP TABLE IF EXISTS mart.abc_xyz_cv_distribution;

CREATE TABLE mart.abc_xyz_cv_distribution AS
WITH bucketed AS (
    SELECT
        (FLOOR(COALESCE(cv_percent, 0) / 5.0) * 5)::INT AS bucket_start
    FROM mart.abc_xyz
)
SELECT
    bucket_start,
    CONCAT(
        LPAD(bucket_start::TEXT, 2, '0'),
        '-',
        LPAD((bucket_start + 5)::TEXT, 2, '0'),
        '%%'
    ) AS cv_bucket,
    COUNT(*) AS object_count
FROM bucketed
GROUP BY bucket_start
ORDER BY bucket_start;
