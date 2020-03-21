from pprint import pprint
import re

from google.cloud import bigquery, storage

BQ_JOB_CONFIG = bigquery.LoadJobConfig(
    schema=[
        bigquery.SchemaField("author_email", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("author_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("body", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("date", "STRING", mode="NULLABLE"),
        bigquery.SchemaField(
            "diff",
            "RECORD",
            mode="NULLABLE",
            fields=[
                # bigquery.SchemaField("files", "RECORD", mode="NULLABLE"),
                bigquery.SchemaField("insertions", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("deletions", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("changed", "INTEGER", mode="NULLABLE"),
            ],
        ),
        bigquery.SchemaField("hash", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("message", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("refs", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("repo", "STRING", mode="NULLABLE"),
    ],
    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    ignore_unknown_values=True,
    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    # time_partitioning=bigquery.TimePartitioning(
    #     type_=bigquery.TimePartitioningType.DAY,
    #     field="timestamp",  # Name of the column to use for partitioning.
    #     expiration_ms=7776000000,  # 90 days.
    # ),
)


def _verify_blob(blob_path: str, bucket_name: str = "ghtrends") -> bool:
    """
    Make sure the requested file is present in GCS
    """

    storage_client = storage.Client()
    blob = storage_client.bucket(bucket_name).blob(blob_path)
    return blob.exists()


def _run_bq_load(
    source_blob_path: str,
    source_bucket_name: str = "ghtrends",
    target_dataset_name: str = "ghtrends",
    target_table_name: str = "gitlog_records",
    job_config: bigquery.LoadJobConfig = BQ_JOB_CONFIG,
) -> bool:
    """
    Load the contents of the file
    """
    assert _verify_blob(blob_path=source_blob_path, bucket_name=source_bucket_name)
    source_uri = f"gs://{source_bucket_name}/{source_blob_path}"

    # Instantiate BQ Client for data inserts
    bigquery_client = bigquery.Client()
    dataset_ref = bigquery_client.dataset(target_dataset_name)
    destination_table = dataset_ref.table(target_table_name)

    load_job = bigquery_client.load_table_from_uri(
        source_uri, destination_table, job_config=job_config,
    )

    print("Starting job {}".format(load_job.job_id))
    load_job.result()  # Waits for table load to complete.
    print("Job finished.")

    if load_job.error_result:
        print("Job errors:")
        pprint(load_job.error_result)
        return False
    return True


def gcs_to_bq(data, context):
    """Background Cloud Function to be triggered by Cloud Storage.
       This generic function logs relevant data when a file is changed.

    Args:
        data (dict): The Cloud Functions event payload.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to Stackdriver Logging
    """

    print("Event ID: {}".format(context.event_id))
    print("Event type: {}".format(context.event_type))
    print("Bucket: {}".format(data["bucket"]))
    print("File: {}".format(data["name"]))
    print("Metageneration: {}".format(data["metageneration"]))
    print("Created: {}".format(data["timeCreated"]))
    print("Updated: {}".format(data["updated"]))

    # Identify the repo this event was triggered for
    repo = re.search(r"gitlog/(.+)\.json", data["name"]).groups()[0]
    print("Repo: {}".format(repo))

    # Load data into BQ
    _run_bq_load(source_blob_path=data["name"])

    # Download the JSON file so we can parse it
    # storage_client = storage.Client()
    # bucket = storage_client.get_bucket("ghtrends")
    # blob = bucket.get_blob(data["name"])
    # contents = blob.download_as_string()
    # jsn = json.loads(contents)

    # Now trigger the function which will generate the log histogram
    # publish_client = pubsub.PublisherClient()
    # topic = "projects/githubtrends-255020/topics/ghtrends_bqload"
    # publish_client.publish(topic, json.dumps({"repo": repo}))
