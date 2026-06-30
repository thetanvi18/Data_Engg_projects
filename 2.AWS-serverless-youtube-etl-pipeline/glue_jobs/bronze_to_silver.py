"""
AWS Glue ETL Job

Transforms raw YouTube trending data (Bronze JSON) stored in Amazon S3
into a cleaned, flattened Parquet dataset (Silver layer) using PySpark.
"""


from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, col

# Create Spark Session
spark = SparkSession.builder.appName("YouTube Bronze to Silver ETL").getOrCreate()

# Read Bronze JSON data
df = spark.read.option("multiline", "true").json(
    "s3://tanvi-retail-lakehouse-2026/bronze/trending/"
)

# Flatten the nested items array
videos_df = df.select(explode(col("items")).alias("video"))

# Select useful columns
silver_df = videos_df.select(
    col("video.id").alias("video_id"),
    col("video.snippet.title").alias("title"),
    col("video.snippet.channelTitle").alias("channel_title"),
    col("video.snippet.publishedAt").alias("published_at"),
    col("video.statistics.viewCount").cast("long").alias("view_count"),
    col("video.statistics.likeCount").cast("long").alias("like_count"),
    col("video.statistics.commentCount").cast("long").alias("comment_count"),
    col("video.snippet.categoryId").alias("category_id")
)

# Write to Silver layer as Parquet
silver_df.write.mode("overwrite").parquet(
    "s3://tanvi-retail-lakehouse-2026/silver/trending/"
)

print("Bronze to Silver ETL completed successfully.")