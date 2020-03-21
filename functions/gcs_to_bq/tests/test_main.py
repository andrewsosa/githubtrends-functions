# pylint: disable=redefined-outer-name
from os import getenv, path
from google.cloud import bigquery, storage
import pytest

from .. import main

GOOGLE_CLOUD_PROJECT = getenv("GOOGLE_CLOUD_PROJECT")
TEST_BUCKET = getenv("TEST_BUCKET")
TEST_TABLE = getenv("TEST_TABLE")

assert GOOGLE_CLOUD_PROJECT is not None
assert TEST_BUCKET is not None


@pytest.fixture(scope="session")
def storage_client() -> storage.Client:
    """ GCS Client """
    yield storage.Client()


@pytest.fixture(scope="session")
def bucket_object(storage_client: storage.Client) -> storage.Bucket:
    """ GCS Bucket from .env config """
    if not storage_client.lookup_bucket(TEST_BUCKET):
        bucket = storage_client.create_bucket(TEST_BUCKET)
    else:
        bucket = storage_client.get_bucket(TEST_BUCKET)
    yield bucket


@pytest.fixture(scope="session")
def blob_path(bucket_object: storage.Bucket) -> str:
    """ Path of a file placed in the GCS Bucket for tests """
    filename = "sample_file.json"
    local_path = path.join(path.dirname(__file__), f"fixtures/{filename}")
    # remote_path = f"gs://{TEST_BUCKET}/{filename}"

    blob: storage.Blob = bucket_object.blob(filename)
    blob.upload_from_filename(local_path)
    assert blob.exists()
    # print("Created blob?", blob.exists())
    yield filename
    # print("Removing blob...")
    blob.delete()


@pytest.fixture(scope="session")
def blob_uri(blob_path: str) -> str:
    return f"gs://{TEST_BUCKET}/{blob_path}"


@pytest.fixture(scope="session")
def bigquery_client() -> bigquery.Client:
    return bigquery.Client()


@pytest.fixture(scope="session")
def bigquery_table(bigquery_client: bigquery.Client) -> bigquery.Table:
    """ Create a temporary table for the test, remove on cleanup """
    table = bigquery_client.create_table(TEST_TABLE, exists_ok=True)
    yield table
    bigquery_client.delete_table(table)


def test_verify_file(blob_path: str):
    """ Check if a file exists in GCS """
    assert main._verify_blob(blob_path=blob_path, bucket_name=TEST_BUCKET)


def test_bq_load(blob_path: str, bigquery_table: bigquery.Table):
    """ Trigger a BQ load job """

    dataset, tablename = TEST_TABLE.split(".")

    is_success = main._run_bq_load(
        source_blob_path=blob_path,
        source_bucket_name=TEST_BUCKET,
        target_dataset_name=dataset,
        target_table_name=tablename,
    )

    assert is_success is True
