from pyspark.sql import SparkSession
from pyspark.sql import functions as F

KAFKA_SERVERS = "kafka:9092"
TOPIC = "telemetry.raw"
BRONZE_PATH = "/app/data/lake/bronze/telemetry"
CHECKPOINT = "/app/data/lake/_checkpoints/bronze_telemetry"

spark = (
    SparkSession.builder.appName("bronze_telemetry")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .config("spark.jars.ivy", "/tmp/.ivy")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

raw = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_SERVERS)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "earliest")
    .load()
)

bronze = raw.select(
    F.col("key").cast("string").alias("kafka_key"),
    F.col("value").cast("string").alias("raw_json"),
    F.col("topic"),
    F.col("partition"),
    F.col("offset"),
    F.col("timestamp").alias("kafka_ts"),
    F.current_timestamp().alias("ingested_at"),
)

query = (
    bronze.writeStream.format("delta")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT)
    .trigger(availableNow=True)
    .start(BRONZE_PATH)
)
query.awaitTermination()
print("Bronze ingestion finished")