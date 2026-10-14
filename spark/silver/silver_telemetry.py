from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

BRONZE_PATH = "/app/data/lake/bronze/telemetry"
SILVER_PATH = "/app/data/lake/silver/telemetry"
QUARANTINE_PATH = "/app/data/lake/silver/telemetry_quarantine"

METRICS = [
    "temperature_c", "cpu_pct", "latency_ms",
    "packet_loss_pct", "vibration_mm_s", "load_pct",
]

schema = StructType(
    [
        StructField("event_id", StringType()),
        StructField("asset_id", StringType()),
        StructField("event_ts", StringType()),
    ]
    + [StructField(m, DoubleType()) for m in METRICS]
)

spark = (
    SparkSession.builder.appName("silver_telemetry")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .config("spark.sql.session.timeZone", "UTC")
    .config("spark.jars.ivy", "/tmp/.ivy")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

bronze = spark.read.format("delta").load(BRONZE_PATH)

# 1) فك الـ JSON وتحويل التوقيت
parsed = (
    bronze.select(
        "raw_json", "partition", "offset", "ingested_at",
        F.from_json("raw_json", schema).alias("d"),
    )
    .select("raw_json", "partition", "offset", "ingested_at", "d.*")
    .withColumn("event_ts", F.to_timestamp("event_ts"))
)

# 2) فصل الصالح عن البايظ
is_valid = (
    F.col("event_id").isNotNull()
    & F.col("asset_id").isNotNull()
    & F.col("event_ts").isNotNull()
)
valid = parsed.filter(is_valid)
invalid = parsed.filter(~is_valid)

(
    invalid.select("raw_json", "partition", "offset", "ingested_at")
    .write.format("delta").mode("overwrite").save(QUARANTINE_PATH)
)

# 3) إزالة المكرر
deduped = valid.dropDuplicates(["event_id"])

# 4) القراءات الغلط: علّم عليها وبعدين حوّلها لـ null
has_sentinel = F.lit(False)
for m in METRICS:
    has_sentinel = has_sentinel | (F.col(m) == -999.0)

silver = deduped.withColumn("has_sensor_error", has_sentinel)
for m in METRICS:
    silver = silver.withColumn(
        m, F.when(F.col(m) == -999.0, F.lit(None)).otherwise(F.col(m))
    )

silver = silver.select(
    "event_id", "asset_id", "event_ts", *METRICS,
    "has_sensor_error", "ingested_at",
)
silver.write.format("delta").mode("overwrite").save(SILVER_PATH)

# 5) تقرير الجودة
n_bronze = bronze.count()
n_invalid = invalid.count()
n_valid = valid.count()
n_silver = silver.count()
print("========== SILVER QUALITY REPORT ==========")
print(f"Bronze rows           : {n_bronze}")
print(f"Quarantined (invalid) : {n_invalid}")
print(f"Duplicates removed    : {n_valid - n_silver}")
print(f"Silver rows           : {n_silver}")
print(f"Rows with sensor error: {silver.filter('has_sensor_error').count()}")
print("Nulls per metric:")
silver.select(
    [F.sum(F.col(m).isNull().cast("int")).alias(m) for m in METRICS]
).show()