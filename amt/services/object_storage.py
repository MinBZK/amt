import os
from collections.abc import Iterable
from datetime import UTC, datetime

from fastapi import UploadFile
from minio import Minio
from minio.datatypes import Object
from ulid import ULID
from urllib3 import BaseHTTPResponse

from amt.core.config import get_settings
from amt.core.exceptions import AMTStorageError

BUCKET_NAME = "amt"


class ObjectStorageService:
    def __init__(
        self,
        url: str = get_settings().OBJECT_STORE_URL,
        username: str = get_settings().OBJECT_STORE_USER,
        password: str = get_settings().OBJECT_STORE_PASSWORD,
        bucket_name: str = BUCKET_NAME,
    ) -> None:
        self.client = Minio(url, username, password, secure=False)
        self.bucket_name = bucket_name
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """
        Validate bucket existence, raising an error if not found.
        """
        if not self.client.bucket_exists(self.bucket_name):
            raise AMTStorageError()

    def _extract_file_metadata(
        self, file: UploadFile, algorithm_id: str, user_id: str
    ) -> dict[str, str | list[str] | tuple[str]]:
        """
        Exctract metadata for the uploaded file.
        """
        filename, ext = os.path.splitext(file.filename) if file.filename else ("", "")
        return {
            "algorithm_id": str(algorithm_id),
            "user_id": user_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "filename": filename,
            "ext": ext,
        }

    def _generate_destination_path(
        self, organization_id: str | int, algorithm_id: str | int, ulid: ULID | None = None
    ) -> str:
        """
        Generate a unique desitnation path for file to upload.
        """
        organization_id = str(organization_id)
        algorithm_id = str(algorithm_id)
        ulid = ulid if ulid else ULID()
        return f"uploads/org/{organization_id}/algorithm/{algorithm_id}/{ulid}"

    def upload_file(
        self,
        organization_id: str | int,
        algorithm_id: str | int,
        user_id: str,
        file: UploadFile,
    ) -> str:
        """
        Uploads a single file to the object storage and returns the path (object name)
        where the file is stored.
        """
        if not file.size:
            raise AMTStorageError()

        destination_path = self._generate_destination_path(organization_id, algorithm_id)
        metadata = self._extract_file_metadata(file, str(algorithm_id), user_id)

        try:
            self.client.put_object(self.bucket_name, destination_path, file.file, file.size, metadata=metadata)
        except Exception as err:
            raise AMTStorageError() from err

        return destination_path

    def upload_files(
        self, organization_id: str | int, algorithm_id: str | int, user_id: str, files: Iterable[UploadFile]
    ) -> list[str]:
        """
        Uploads multiple files to the object storage and returns the paths (object names)
        where the files are stored.
        """
        return [self.upload_file(organization_id, algorithm_id, user_id, file) for file in files]

    def delete_file(self, organization_id: str | int, algorithm_id: str | int, ulid: ULID) -> None:
        """
        Deletes a file from the object storage.
        """

        path = self._generate_destination_path(organization_id, algorithm_id, ulid)
        try:
            self.client.remove_object(self.bucket_name, path)
        except Exception as err:
            raise AMTStorageError() from err

    def get_file(self, organization_id: str | int, algorithm_id: str | int, ulid: ULID) -> BaseHTTPResponse:
        """
        Gets a file from the object storage.
        """
        path = self._generate_destination_path(organization_id, algorithm_id, ulid)
        try:
            file = self.client.get_object(self.bucket_name, path)
        except Exception as err:
            raise AMTStorageError() from err
        return file

    def get_file_filename_and_ext(self, name: str) -> str:
        """
        Gets filename and extension from a file from the object storage without downloading its
        contents.
        """
        try:
            stats = self.client.stat_object(self.bucket_name, name)
        except Exception as err:
            raise AMTStorageError() from err

        name = stats.metadata["X-Amz-Meta-Filename"] if stats.metadata else ""
        ext = stats.metadata["X-Amz-Meta-Ext"] if stats.metadata else ""
        return f"{name}{ext}"
