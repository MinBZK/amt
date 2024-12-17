from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import Mock

import pytest
from amt.core.exceptions import AMTStorageError
from amt.services.object_storage import (
    MinioMetadataExtractor,
    ObjectMetadata,
    ObjectStorageService,
)
from fastapi import UploadFile
from minio import Minio
from minio.datatypes import Object
from pytest_mock import MockerFixture
from ulid import ULID
from urllib3 import BaseHTTPResponse


@pytest.fixture
def mock_minio_client(mocker: MockerFixture) -> Mock:
    client = mocker.Mock(spec=Minio)
    client.bucket_exists.return_value = True
    return client


@pytest.fixture
def mock_upload_file():
    file_content = b"test file content"
    file = UploadFile(filename="test.txt", file=BytesIO(file_content))
    file.size = len(file_content)
    return file


def test_object_metadata_creation():
    metadata = ObjectMetadata(
        algorithm_id="test_algo",
        user_id="test_user",
        measure_urn="test_urn",
        timestamp="2023-01-01T00:00:00+00:00",
        filename="test_file",
        ext="txt",
    )

    assert metadata.algorithm_id == "test_algo"
    assert metadata.user_id == "test_user"
    assert metadata.measure_urn == "test_urn"
    assert metadata.filename == "test_file"
    assert metadata.ext == "txt"


def test_minio_metadata_extractor_from_file_upload(mocker: MockerFixture):
    extractor = MinioMetadataExtractor()

    mock_now = datetime(2024, 12, 11, 10, 0, 0, tzinfo=UTC)
    mock_datetime = mocker.patch("amt.services.object_storage.datetime")
    mock_datetime.now.return_value = mock_now

    metadata = extractor.from_file_upload(
        "example.txt", algorithm_id="test_algo", measure_urn="test_urn", user_id="test_user"
    )

    assert metadata.filename == "example"
    assert metadata.ext == "txt"
    assert metadata.algorithm_id == "test_algo"
    assert metadata.measure_urn == "test_urn"
    assert metadata.user_id == "test_user"
    assert metadata.timestamp == mock_now.isoformat()


def test_minio_metadata_extractor_from_object():
    mock_object = Object(
        bucket_name="test",
        object_name="test",
        metadata={
            "X-Amz-Meta-Algorithm_id": "test_algo",
            "X-Amz-Meta-User_id": "test_user",
            "X-Amz-Meta-Measure_urn": "test_urn",
            "X-Amz-Meta-Timestamp": "2023-01-01T00:00:00+00:00",
            "X-Amz-Meta-Filename": "test_file",
            "X-Amz-Meta-Ext": "txt",
        },
    )

    extractor = MinioMetadataExtractor()
    metadata = extractor.from_object(mock_object)

    assert metadata.algorithm_id == "test_algo"
    assert metadata.user_id == "test_user"
    assert metadata.measure_urn == "test_urn"
    assert metadata.filename == "test_file"
    assert metadata.ext == "txt"
    assert metadata.timestamp == "2023-01-01T00:00:00+00:00"


def test_object_storage_service_initialization(mock_minio_client: Mock):
    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_minio_client, metadata_extractor, "test_bucket")

    assert service.client == mock_minio_client
    assert service.bucket_name == "test_bucket"


def test_object_storage_service_bucket_not_exists(mocker: MockerFixture):
    mock_client = mocker.Mock(spec=Minio)
    mock_client.bucket_exists.return_value = False

    metadata_extractor = MinioMetadataExtractor()

    with pytest.raises(AMTStorageError):
        ObjectStorageService(mock_client, metadata_extractor, "test_bucket")


def test_generate_destination_path(mocker: MockerFixture):
    mock_client = mocker.Mock(spec=Minio)
    mock_client.bucket_exists.return_value = True

    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_client, metadata_extractor, "test_bucket")

    path1 = service._generate_destination_path("org1", "algo1")  # type: ignore
    assert path1.startswith("uploads/org/org1/algorithm/algo1/")

    test_ulid = ULID()
    path2 = service._generate_destination_path("org1", "algo1", test_ulid)  # type: ignore
    assert path2 == f"uploads/org/org1/algorithm/algo1/{test_ulid}"


def test_upload_file_success(mock_minio_client: Mock, mock_upload_file: UploadFile):
    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_minio_client, metadata_extractor, "test_bucket")

    mock_minio_client.put_object.return_value = None

    path = service.upload_file("org1", "algo1", "test_urn", "user1", mock_upload_file)

    assert path.startswith("uploads/org/org1/algorithm/algo1/")
    mock_minio_client.put_object.assert_called_once()


def test_upload_file_error(mock_minio_client: Mock, mock_upload_file: UploadFile):
    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_minio_client, metadata_extractor, "test_bucket")

    mock_minio_client.put_object.side_effect = Exception("S3 Error")

    with pytest.raises(AMTStorageError):
        service.upload_file("org1", "algo1", "test_urn", "user1", mock_upload_file)


def test_upload_file_empty_file(mock_minio_client: Mock):
    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_minio_client, metadata_extractor, "test_bucket")

    empty_file = UploadFile(filename="empty.txt", file=BytesIO(b""))
    empty_file.size = 0

    with pytest.raises(AMTStorageError):
        service.upload_file("org1", "algo1", "test_urn", "user1", empty_file)


def test_upload_files_success(mock_minio_client: Mock, mock_upload_file: UploadFile):
    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_minio_client, metadata_extractor, "test_bucket")

    mock_minio_client.put_object.return_value = None

    files = [mock_upload_file, mock_upload_file]
    paths = service.upload_files("org1", "algo1", "test_urn", "user1", files)

    assert len(paths) == 2
    assert all(path.startswith("uploads/org/org1/algorithm/algo1/") for path in paths)
    assert mock_minio_client.put_object.call_count == 2


def test_upload_files_error(mock_minio_client: Mock, mock_upload_file: UploadFile):
    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_minio_client, metadata_extractor, "test_bucket")

    mock_minio_client.put_object.side_effect = Exception("S3 Error")

    files = [mock_upload_file, mock_upload_file]
    with pytest.raises(AMTStorageError):
        service.upload_files("org1", "algo1", "test_urn", "user1", files)


def test_get_files_success(mock_minio_client: Mock):
    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_minio_client, metadata_extractor, "test_bucket")

    mock_minio_client.get_object.return_value = BaseHTTPResponse(
        request_url="", status=200, version=1, version_string="1", reason=None, decode_content=False
    )

    response = service.get_file("org1", "algo1", ULID())

    assert mock_minio_client.get_object.call_count == 1
    assert response.status == 200


def test_get_files_error(mock_minio_client: Mock):
    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_minio_client, metadata_extractor, "test_bucket")

    mock_minio_client.get_object.side_effect = Exception("S3 Error")

    with pytest.raises(AMTStorageError):
        service.get_file("org1", "algo1", ULID())


def test_get_file_metadata_from_object_name(mock_minio_client: Mock):
    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_minio_client, metadata_extractor, "test_bucket")

    mock_object = Object(
        bucket_name="test_bucket",
        object_name="test_object",
        metadata={
            "X-Amz-Meta-Algorithm_id": "test_algo",
            "X-Amz-Meta-User_id": "test_user",
            "X-Amz-Meta-Measure_urn": "test_urn",
            "X-Amz-Meta-Timestamp": "2023-01-01T00:00:00+00:00",
            "X-Amz-Meta-Filename": "test_file",
            "X-Amz-Meta-Ext": "txt",
        },
    )
    mock_minio_client.stat_object.return_value = mock_object

    metadata = service.get_file_metadata_from_object_name("test_path")

    assert metadata.algorithm_id == "test_algo"
    mock_minio_client.stat_object.assert_called_with("test_bucket", "test_path")


def test_get_file_metadata_error(mock_minio_client: Mock):
    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_minio_client, metadata_extractor, "test_bucket")

    mock_minio_client.stat_object.side_effect = Exception("S3 Error")

    with pytest.raises(AMTStorageError):
        service.get_file_metadata_from_object_name("test_path")


def test_delete_file_success(mock_minio_client: Mock):
    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_minio_client, metadata_extractor, "test_bucket")

    path = service.delete_file("org1", "algo1", ULID())

    assert path.startswith("uploads/org/org1/algorithm/algo1/")
    mock_minio_client.remove_object.assert_called_once()


def test_delete_file_error(mock_minio_client: Mock):
    metadata_extractor = MinioMetadataExtractor()
    service = ObjectStorageService(mock_minio_client, metadata_extractor, "test_bucket")

    mock_minio_client.remove_object.side_effect = Exception("S3 Error")

    with pytest.raises(AMTStorageError):
        service.delete_file("org1", "algo1", ULID())
