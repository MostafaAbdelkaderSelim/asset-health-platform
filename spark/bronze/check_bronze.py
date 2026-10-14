from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("check_bronze")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .config("spark.jars.ivy", "/tmp/.ivy")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

df = spark.read.format("delta").load("/app/data/lake/bronze/telemetry")
print("Row count:", df.count())
df.groupBy("partition").count().orderBy("partition").show()
df.select("kafka_key", "offset", "raw_json").show(3, truncate=60)