import logging
import os
from collections.abc import Iterable
from datetime import UTC, datetime

from fastapi import UploadFile
from minio import Minio  # pyright: ignore[reportMissingTypeStubs]
from minio.datatypes import Object  # pyright: ignore[reportMissingTypeStubs]
from ulid import ULID
from urllib3 import BaseHTTPResponse

from amt.core.config import get_settings
from amt.core.exceptions import AMTStorageError
from amt.schema.shared import BaseModel

logger = logging.getLogger(__name__)


class ObjectMetadata(BaseModel):
    """
    Metadata for files in the object storage.
    """

    algorithm_id: str
    user_id: str
    measure_urn: str
    timestamp: str
    filename: str
    ext: str


class MinioMetadataExtractor:
    @staticmethod
    def from_file_upload(filename: str, algorithm_id: str, measure_urn: str, user_id: str) -> ObjectMetadata:
        """
        Extract metadata for a file.
        """
        filename, ext = os.path.splitext(filename) if filename else ("", "")
        ext = ext.replace(".", "")
        return ObjectMetadata(
            algorithm_id=algorithm_id,
            user_id=user_id,
            measure_urn=measure_urn,
            timestamp=datetime.now(UTC).isoformat(),
            filename=filename,
            ext=ext,
        )

    @staticmethod
    def from_object(object: Object) -> ObjectMetadata:
        """
        Extract metadata from a Minio object.
        """
        return ObjectMetadata(
            algorithm_id=object.metadata["X-Amz-Meta-Algorithm_id"] if object.metadata else "",
            user_id=object.metadata["X-Amz-Meta-User_id"] if object.metadata else "",
            measure_urn=object.metadata["X-Amz-Meta-Measure_urn"] if object.metadata else "",
            timestamp=object.metadata["X-Amz-Meta-Timestamp"] if object.metadata else "",
            filename=object.metadata["X-Amz-Meta-Filename"] if object.metadata else "",
            ext=object.metadata["X-Amz-Meta-Ext"] if object.metadata else "",
        )


class ObjectStorageService:
    def __init__(
        self,
        minio_client: Minio,
        metadata_extractor: MinioMetadataExtractor,
        bucket_name: str,
    ) -> None:
        self.client = minio_client
        self.bucket_name = bucket_name
        self._ensure_bucket_exists()
        self.metadata_extractor = metadata_extractor

    def _ensure_bucket_exists(self) -> None:
        """
        Validate bucket existence, raising an error if not found.
        """
        if not self.client.bucket_exists(self.bucket_name):
            logger.exception("Bucket in object storage does not exist.")
            raise AMTStorageError()

    def _generate_destination_path(
        self, organization_id: str | int, algorithm_id: str | int, ulid: ULID | None = None
    ) -> str:
        """
        Generate a unique destination path for file to upload if no ULID is passed.
        Returns the destination path of a file with given ULID if a ULID is passed.
        """
        ulid = ulid if ulid else ULID()
        return f"uploads/org/{organization_id}/algorithm/{algorithm_id}/{ulid}"

    def get_file_metadata_from_object_name(self, object_name: str) -> ObjectMetadata:
        """
        Gets the object metadata for a file stored under object_name.
        """
        try:
            stats = self.client.stat_object(self.bucket_name, object_name)
        except Exception as err:
            logger.exception("Could not retrieve file metadata from object store")
            raise AMTStorageError() from err

        return self.metadata_extractor.from_object(stats)

    def get_file_metadata(self, organization_id: str | int, algorithm_id: str | int, ulid: ULID) -> ObjectMetadata:
        """
        Gets the object metadata for a file with given organization_id, algorithm_id and ULID.
        """
        path = self._generate_destination_path(organization_id, algorithm_id, ulid)
        return self.get_file_metadata_from_object_name(path)

    def upload_file(
        self,
        organization_id: str | int,
        algorithm_id: str | int,
        measure_urn: str,
        user_id: str,
        file: UploadFile,
    ) -> str:
        """
        Uploads a single file to the object storage and returns the path (object name)
        where the file is stored.
        """
        if not file.size:
            logger.exception("User provided upload file is empty.")
            raise AMTStorageError()

        destination_path = self._generate_destination_path(organization_id, algorithm_id)
        filename = file.filename if file.filename else "unnamed.unknown"
        metadata = self.metadata_extractor.from_file_upload(filename, str(algorithm_id), measure_urn, user_id)

        try:
            self.client.put_object(
                self.bucket_name, destination_path, file.file, file.size, metadata=metadata.model_dump()
            )
        except Exception as err:
            logger.exception("Cannot upload file to object storage.")
            raise AMTStorageError() from err

        return destination_path

    def upload_files(
        self,
        organization_id: str | int,
        algorithm_id: str | int,
        measure_urn: str,
        user_id: str,
        files: Iterable[UploadFile],
    ) -> list[str]:
        """
        Uploads multiple files to the object storage and returns the paths (object names)
        where the files are stored.
        """
        return [self.upload_file(organization_id, algorithm_id, measure_urn, user_id, file) for file in files]

    def get_file(self, organization_id: str | int, algorithm_id: str | int, ulid: ULID) -> BaseHTTPResponse:
        """
        Gets a file from the object storage.
        """
        path = self._generate_destination_path(organization_id, algorithm_id, ulid)
        try:
            file = self.client.get_object(self.bucket_name, path)
        except Exception as err:
            logger.exception("Cannot get file from object storage.")
            raise AMTStorageError() from err
        return file

    def delete_file(self, organization_id: str | int, algorithm_id: str | int, ulid: ULID) -> str:
        """
        Deletes a file from the object storage.
        """

        path = self._generate_destination_path(organization_id, algorithm_id, ulid)
        try:
            self.client.remove_object(self.bucket_name, path)
        except Exception as err:
            logger.exception("Cannot delete file from object storage.")
            raise AMTStorageError() from err
        return path


def create_object_storage_service(
    url: str = get_settings().OBJECT_STORE_URL,
    username: str = get_settings().OBJECT_STORE_USER,
    password: str = get_settings().OBJECT_STORE_PASSWORD,
    bucket_name: str = get_settings().OBJECT_STORE_BUCKET_NAME,
    secure: bool = False,
) -> ObjectStorageService:
    """
    Creates an instance of the ObjectStorageService.
    """
    metadata_extractor = MinioMetadataExtractor()
    client = Minio(endpoint=url, access_key=username, secret_key=password, secure=secure)
    return ObjectStorageService(client, metadata_extractor, bucket_name=bucket_name)
