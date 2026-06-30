//Bronze Layer: Trending Table
SELECT *
FROM trending;

//Silver Layer: Trending Table
//Query 1:
SELECT *
FROM silver_trending;

//Query 2:
SELECT
    title,
    channel_title,
    view_count
FROM silver_trending
ORDER BY view_count DESC
LIMIT 5;