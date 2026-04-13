"""Google Cloud Storage implementation of the unicloud storage contract.

This module provides :class:`GCS`, a :class:`CloudStorageFactory` built on top of
``google-cloud-storage``, and a companion :class:`Bucket` class that implements
:class:`AbstractBucket` for per-object operations (upload, download, delete, list, exists, rename,
per-file glob filtering) against a single GCS bucket.

Authentication supports three modes:

1. An explicit path to a service-account JSON file, passed as ``service_key_path``.
2. The ``GOOGLE_APPLICATION_CREDENTIALS`` environment variable pointing at the same JSON file.
3. A ``SERVICE_KEY_CONTENT`` environment variable containing the base64-encoded contents of the
   JSON file (use :func:`unicloud.utils.encode` to produce the value).
"""

import fnmatch
import logging
import os
from pathlib import Path
from typing import List, Optional, Union

from google.cloud import storage
from google.oauth2 import service_account

from unicloud.abstract_class import AbstractBucket, CloudStorageFactory
from unicloud.utils import decode

logger = logging.getLogger(__name__)


class GCS(CloudStorageFactory):
    """Google Cloud Storage client — the :class:`CloudStorageFactory` implementation for GCS.

    Construction requires a ``project_id`` and resolves credentials through one of three paths
    (service-account file path, ``GOOGLE_APPLICATION_CREDENTIALS`` env var, or the base64-encoded
    ``SERVICE_KEY_CONTENT`` env var).

    Examples:
        - Instantiate from a service-account JSON file:
            ```python
            >>> gcs = GCS("my-project-id", service_key_path="path/to/service-account.json")  # doctest: +SKIP

            ```
        - Instantiate using GOOGLE_APPLICATION_CREDENTIALS in the environment:
            ```python
            >>> gcs = GCS("my-project-id")  # doctest: +SKIP

            ```
        - Instantiate using SERVICE_KEY_CONTENT (encoded via unicloud.utils.encode):
            ```python
            >>> import os
            >>> os.environ["SERVICE_KEY_CONTENT"] = "<base64>"  # doctest: +SKIP
            >>> gcs = GCS("my-project-id")  # doctest: +SKIP

            ```

    See Also:
        unicloud.aws.aws.S3: The matching AWS S3 implementation.
        unicloud.utils.encode: Produces the value for ``SERVICE_KEY_CONTENT``.
    """

    def __init__(self, project_id: str, service_key_path: Optional[str] = None):
        """Initialize the GCS client.

        Args:
            project_id: The Google Cloud project name that owns (or can access) the buckets you
                intend to use.
            service_key_path: Optional filesystem path to a service-account JSON file. When
                ``None`` (the default), the client falls back to ``GOOGLE_APPLICATION_CREDENTIALS``
                and then to ``SERVICE_KEY_CONTENT``.

        Raises:
            FileNotFoundError: If ``service_key_path`` is provided but the file does not exist.
            ValueError: If none of the three credential paths resolves (no ``service_key_path``,
                no ``GOOGLE_APPLICATION_CREDENTIALS``, no ``SERVICE_KEY_CONTENT``).

        Examples:
            - Authenticate with a service-account JSON file path:
                ```python
                >>> gcs = GCS("my-project-id", service_key_path="path/to/service-account.json")  # doctest: +SKIP

                ```
            - Authenticate via GOOGLE_APPLICATION_CREDENTIALS:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP

                ```
        """
        self._project_id = project_id
        if service_key_path is not None and not Path(service_key_path).exists():
            raise FileNotFoundError(
                f"The service key file {service_key_path} does not exist"
            )

        self.service_key = service_key_path
        self._client = self.create_client()

    @property
    def project_id(self) -> str:
        """Return the Google Cloud project ID associated with this client.

        Returns:
            str: The project ID that was passed to :meth:`__init__`.
        """
        return self._project_id

    @property
    def client(self) -> storage.client.Client:
        """Return the cached ``google.cloud.storage`` client.

        Returns:
            google.cloud.storage.client.Client: The client instance produced by
            :meth:`create_client`.
        """
        return self._client

    def __str__(self) -> str:
        """Return a human-readable description of the client.

        Returns:
            str: Multiline string containing the project ID and the client scopes.

        Examples:
            - Inspect the client via print():
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> print(gcs)  # doctest: +SKIP
                project_id: my-project-id,
                Client Scope=(...)

                ```
        """
        return f"""
        project_id: {self.project_id},
        Client Scope={self.client.SCOPE})
        """

    def __repr__(self) -> str:
        """Return a developer-facing representation of the client.

        Returns:
            str: Same content as :meth:`__str__`.

        Examples:
            - Inspect the client via repr():
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> print(repr(gcs))  # doctest: +SKIP
                project_id: my-project-id,
                Client Scope=(...)

                ```
        """
        return f"""
        project_id: {self.project_id},
        Client Scope={self.client.SCOPE})
        """

    @property
    def bucket_list(self) -> List[str]:
        """List every bucket name visible to the current project.

        Returns:
            List[str]: Bucket names accessible under :attr:`project_id`.

        Examples:
            - Enumerate every visible bucket:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> gcs.bucket_list  # doctest: +SKIP
                ['bucket1', 'bucket2', 'bucket3']

                ```
        """
        return [bucket.name for bucket in self.client.list_buckets()]

    def create_client(self) -> storage.client.Client:
        """Build a ``google.cloud.storage`` client from one of the three credential sources.

        The selection order is:

        1. An explicit ``service_key_path`` passed to :meth:`__init__`.
        2. The ``GOOGLE_APPLICATION_CREDENTIALS`` environment variable pointing at a
           service-account JSON file.
        3. The ``SERVICE_KEY_CONTENT`` environment variable — base64-encoded contents of a
           service-account JSON file, decoded via :func:`unicloud.utils.decode`.

        When unicloud code runs on Google Cloud infrastructure (Compute Engine, Cloud Run, ...)
        the environment's default service account may already be available; in that case none of
        the three explicit paths is needed, but this method does not try to detect the default —
        caller is expected to set one of the credential sources above.

        Returns:
            google.cloud.storage.client.Client: The initialized storage client.

        Raises:
            ValueError: If neither ``service_key_path`` nor ``GOOGLE_APPLICATION_CREDENTIALS``
                nor ``SERVICE_KEY_CONTENT`` provide credentials.
        """
        if self.service_key:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_key
            )
            client = storage.Client(project=self.project_id, credentials=credentials)
        elif "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            credentials = service_account.Credentials.from_service_account_file(
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
            )
            client = storage.Client(project=self.project_id, credentials=credentials)
        elif "SERVICE_KEY_CONTENT" in os.environ:
            # key need to be decoded into a dict/json object
            service_key_content = decode(os.environ["SERVICE_KEY_CONTENT"])
            client = storage.Client.from_service_account_info(service_key_content)
        else:
            raise ValueError(
                "Since the GOOGLE_APPLICATION_CREDENTIALS and the SERVICE_KEY_CONTENT are not in your env variables "
                "you have to provide a path to your service account"
            )

        return client

    def upload(self, local_path: str, bucket_path: str):
        """Upload a single file via the factory-level shortcut.

        Prefer :meth:`get_bucket` followed by :meth:`Bucket.upload` for directory uploads and
        overwrite handling.

        Args:
            local_path: Path to the local file to upload.
            bucket_path: Destination path in the form ``"<bucket_id>/<object_name>"``. Split on
                the first ``/``.

        Examples:
            - Push a local file into a bucket:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> gcs.upload("local/file.txt", "my-bucket/folder/file.txt")  # doctest: +SKIP

                ```
        """
        bucket_name, object_name = bucket_path.split("/", 1)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_filename(local_path)
        logger.info(f"File {local_path} uploaded to {bucket_path}.")

    def download(self, cloud_path, local_path):
        """Download a single object via the factory-level shortcut.

        Args:
            cloud_path: Source path in the form ``"<bucket_id>/<object_name>"``.
            local_path: Local destination path for the downloaded file.

        Examples:
            - Fetch an object to a local file:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> gcs.download("my-bucket/folder/file.txt", "local/file.txt")  # doctest: +SKIP

                ```
        """
        bucket_name, object_name = cloud_path.split("/", 1)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.download_to_filename(local_path)
        logger.info(f"File {cloud_path} downloaded to {local_path}.")

    def get_bucket(self, bucket_id: str) -> "Bucket":
        """Return a :class:`Bucket` handle for per-object operations on ``bucket_id``.

        The wrapped ``storage.Bucket`` uses the client's project as the billing project
        (``user_project=self.project_id``), which is required for requester-pays buckets and
        harmless otherwise.

        Args:
            bucket_id: The GCS bucket ID to look up. The method does *not* verify that the bucket
                exists; errors surface on the first actual operation.

        Returns:
            Bucket: A :class:`Bucket` wrapper for the named GCS bucket.

        Examples:
            - Get a bucket handle and list files:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket-id")  # doctest: +SKIP
                >>> bucket.list_files()  # doctest: +SKIP
                ['file1.txt', 'folder/file2.txt']

                ```
        """
        bucket = storage.Bucket(self.client, bucket_id, user_project=self.project_id)
        return Bucket(bucket)


class Bucket(AbstractBucket):
    """GCS bucket handle — the :class:`AbstractBucket` implementation for Google Cloud Storage.

    Instances wrap a ``google.cloud.storage.bucket.Bucket`` and expose the unicloud contract on
    top of it: upload/download (files and directories), delete, list (with optional prefix and
    glob pattern), existence-check, rename, and raw blob access.

    Examples:
        - Prefer :meth:`GCS.get_bucket` over constructing directly:
            ```python
            >>> gcs = GCS("my-project-id")  # doctest: +SKIP
            >>> bucket = gcs.get_bucket("my-bucket-id")  # doctest: +SKIP
            >>> bucket.file_exists("folder/file.txt")  # doctest: +SKIP
            True

            ```
    """

    def __init__(self, bucket: storage.bucket.Bucket):
        """Wrap a ``google.cloud.storage`` Bucket object.

        Args:
            bucket: A ``google.cloud.storage.bucket.Bucket`` instance — typically produced by
                :meth:`GCS.get_bucket`.
        """
        self._bucket = bucket

    def __str__(self):
        """Return ``"Bucket: <name>"``.

        Returns:
            str: Human-readable representation including the bucket name.
        """
        return f"Bucket: {self.name}"

    def __repr__(self):
        """Return ``"Bucket: <name>"`` — same as :meth:`__str__`.

        Returns:
            str: Developer-facing representation.
        """
        return f"Bucket: {self.name}"

    @property
    def name(self):
        """Return the bucket name.

        Returns:
            str: The name of the wrapped GCS bucket.
        """
        return self.bucket.name

    @property
    def bucket(self) -> storage.bucket.Bucket:
        """Return the underlying ``google.cloud.storage`` Bucket object.

        Exposed as an escape hatch for callers that need to drop down to the native SDK.

        Returns:
            google.cloud.storage.bucket.Bucket: The wrapped GCS bucket object.
        """
        return self._bucket

    def list_files(
        self,
        prefix: Optional[str] = None,
        max_results: Optional[int] = None,
        pattern: Optional[str] = None,
    ) -> List[str]:
        """List objects in the bucket with optional prefix, limit, and glob filtering.

        Filtering happens server-side for ``prefix`` and ``max_results`` (cheap) and client-side
        for ``pattern`` (after the listing is retrieved), so a restrictive ``prefix`` plus a
        loose ``pattern`` is the efficient combination.

        Args:
            prefix: Optional object-name prefix, e.g. ``"data/"`` to list only objects under
                ``data/``. Server-side filter.
            max_results: Optional hard cap on the number of objects returned. Server-side filter.
            pattern: Optional glob pattern applied with :func:`fnmatch.fnmatch`, e.g. ``"*.txt"``
                or ``"data/*.csv"``. Client-side filter.

        Returns:
            List[str]: Matching object names in the order the SDK returns them.

        Examples:
            - List every object in the bucket:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.list_files()  # doctest: +SKIP
                ['file1.txt', 'data/file2.csv']

                ```
            - List objects under a prefix only:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.list_files(prefix="data/")  # doctest: +SKIP
                ['data/file2.csv']

                ```
            - Cap the listing at 10 results:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.list_files(max_results=10)  # doctest: +SKIP

                ```
        """
        blobs = self.bucket.list_blobs(prefix=prefix, max_results=max_results)
        file_names = [blob.name for blob in blobs]

        # Apply pattern matching if a pattern is provided
        if pattern:
            file_names = [name for name in file_names if fnmatch.fnmatch(name, pattern)]

        return file_names

    def get_file(self, blob_id) -> storage.blob.Blob:
        """Return the raw ``google.cloud.storage.blob.Blob`` for ``blob_id``.

        Useful for operations that unicloud does not wrap — for example setting metadata,
        generating signed URLs, or streaming downloads. Returns ``None`` if the blob does not
        exist (via ``Bucket.get_blob``).

        Args:
            blob_id: The object name in the bucket.

        Returns:
            google.cloud.storage.blob.Blob: The blob handle, or ``None`` if missing.

        Examples:
            - Get the raw blob and inspect its name:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> blob = bucket.get_file("example.txt")  # doctest: +SKIP
                >>> blob.name  # doctest: +SKIP
                'example.txt'

                ```
        """
        return self.bucket.get_blob(blob_id)

    def file_exists(self, file_name: str) -> bool:
        """Return whether an object exists in the bucket.

        Implemented as a single ``get_blob`` call; returns ``False`` for any blob that was not
        found (including when the caller lacks read permission, so treat the return value as a
        positive signal only).

        Args:
            file_name: Exact object name to check.

        Returns:
            bool: ``True`` if the blob exists and is readable, ``False`` otherwise.

        Examples:
            - Probe for an existing file:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.file_exists("example.txt")  # doctest: +SKIP
                True

                ```
            - Probe for a missing file:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.file_exists("nonexistent.txt")  # doctest: +SKIP
                False

                ```
        """
        blob = self.bucket.get_blob(file_name)
        return False if blob is None else True

    def upload(
        self,
        local_path: Union[str, Path],
        bucket_path: Union[str, Path],
        overwrite: bool = False,
    ):
        """Upload a file or directory to the bucket.

        When ``local_path`` is a directory, every file beneath it is uploaded recursively and
        the relative tree under ``bucket_path`` is preserved.

        Args:
            local_path: Path to the local file or directory to upload.
            bucket_path: Destination object name (for a single file) or destination prefix (for a
                directory). Trailing ``/`` is tolerated.
            overwrite: If ``False`` (the default), uploading to a name that already exists raises
                ``ValueError``. If ``True``, the existing blob is replaced silently.

        Raises:
            FileNotFoundError: If ``local_path`` does not exist.
            ValueError: If ``local_path`` is an empty directory, or if a destination blob already
                exists with ``overwrite=False``.

        Examples:
            - Upload a single file:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.upload("local/file.txt", "folder/file.txt")  # doctest: +SKIP

                ```
            - Upload a directory recursively:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.upload("local/dir/", "remote/dir/")  # doctest: +SKIP

                ```

        Note:
            Directory uploads preserve the tree structure relative to ``local_path``.
        """
        local_path = Path(local_path)

        if not local_path.exists():
            raise FileNotFoundError(f"The local path {local_path} does not exist.")

        if local_path.is_file():
            self._upload_file(local_path, bucket_path, overwrite)
        elif local_path.is_dir():
            self._upload_directory(local_path, bucket_path, overwrite)
        else:
            raise ValueError(
                f"The local path {local_path} is neither a file nor a directory."
            )

    def _upload_file(
        self, local_path: Path, bucket_path: str, overwrite: bool = False
    ) -> None:
        """Upload a single file, honoring the ``overwrite`` flag.

        Args:
            local_path: Local file to upload.
            bucket_path: Destination blob name in the bucket.
            overwrite: When ``False``, raises if the blob already exists.

        Raises:
            ValueError: If the destination blob exists and ``overwrite=False``.
        """
        blob = self.bucket.blob(bucket_path)

        if not overwrite and blob.exists():
            raise ValueError(
                f"The file '{bucket_path}' already exists in the bucket and overwrite is set to False."
            )

        blob.upload_from_filename(str(local_path))
        logger.info(f"File '{local_path}' uploaded to '{bucket_path}'.")

    def _upload_directory(
        self, local_path: Path, bucket_path: str, overwrite: bool = False
    ):
        """Upload every file under ``local_path`` recursively.

        Args:
            local_path: Local directory to walk.
            bucket_path: Destination prefix in the bucket.
            overwrite: Forwarded to :meth:`_upload_file` for each uploaded file.

        Raises:
            ValueError: If ``local_path`` is an empty directory, or if any destination blob
                already exists with ``overwrite=False``.
        """
        if local_path.is_dir() and not any(local_path.iterdir()):
            raise ValueError(f"Directory {local_path} is empty.")

        for file in local_path.rglob("*"):
            if file.is_file():
                relative_path = file.relative_to(local_path)
                bucket_file_path = (
                    f"{bucket_path.rstrip('/')}/{relative_path.as_posix()}"
                )
                self._upload_file(file, bucket_file_path, overwrite)

    def download(
        self, bucket_path: str, local_path: Union[Path, str], overwrite: bool = False
    ):
        """Download a file or directory from the bucket.

        A trailing ``/`` on ``bucket_path`` triggers the recursive-directory code path; anything
        else is treated as a single-object download.

        Args:
            bucket_path: Path inside the bucket to download. Trailing ``/`` means "directory".
            local_path: Local destination. For a single file this is the full filename; for a
                directory it is the directory root (created if missing).
            overwrite: If ``False`` (the default), existing local files raise ``ValueError``. If
                ``True``, they are overwritten.

        Raises:
            FileNotFoundError: If the bucket path (file or directory) does not exist.
            ValueError: If the local destination exists with ``overwrite=False``.

        Examples:
            - Download a single file:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.download("example.txt", "local/example.txt")  # doctest: +SKIP

                ```
            - Download every object under a prefix:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.download("data/", "local/data/")  # doctest: +SKIP

                ```

        Warning:
            Ensure the destination has sufficient disk space when downloading large directories.

        See Also:
            upload: The inverse operation that pushes files into the bucket.
        """
        if bucket_path.endswith("/"):
            self._download_directory(bucket_path, local_path, overwrite)
        else:
            self._download_file(bucket_path, local_path, overwrite)

    def _download_file(
        self, bucket_path: str, local_path: Union[str, Path], overwrite: bool = False
    ) -> None:
        """Download a single blob, honoring the ``overwrite`` flag.

        Args:
            bucket_path: Source blob name in the bucket.
            local_path: Local destination filename. Parent directories are created if missing.
            overwrite: When ``False``, raises if the local file already exists.

        Raises:
            FileNotFoundError: If the source blob does not exist.
            ValueError: If the local destination exists and ``overwrite=False``.
        """
        local_path = Path(local_path)
        blob = self.bucket.blob(bucket_path)

        if not blob.exists():
            raise FileNotFoundError(
                f"The file '{bucket_path}' does not exist in the bucket."
            )

        if local_path.exists() and not overwrite:
            raise ValueError(
                f"The destination file '{local_path}' already exists and overwrite is set to False."
            )

        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(local_path))
        logger.info(f"File '{bucket_path}' downloaded to '{local_path}'.")

    def _download_directory(
        self, cloud_path: str, local_path: Union[str, Path], overwrite: bool = False
    ) -> None:
        """Download every blob under the prefix ``cloud_path`` recursively.

        Args:
            cloud_path: Source prefix in the bucket (should end with ``/``).
            local_path: Local root directory to write into; created if missing.
            overwrite: Forwarded through; when ``False`` an existing local file raises.

        Raises:
            FileNotFoundError: If the prefix yields no blobs.
            ValueError: If any local destination file exists with ``overwrite=False``.
        """
        local_path = Path(local_path)
        blobs = list(self.bucket.list_blobs(prefix=cloud_path))

        if not any(blobs):
            raise FileNotFoundError(
                f"The directory '{cloud_path}' does not exist in the bucket."
            )

        for blob in blobs:
            if blob.name.endswith("/"):
                continue  # Skip "directory" entries

            relative_path = Path(blob.name).relative_to(cloud_path)
            local_file_path = local_path / relative_path

            if local_file_path.exists() and not overwrite:
                raise ValueError(
                    f"The destination file '{local_file_path}' already exists and overwrite is set to False."
                )

            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(local_file_path)
            logger.info(f"File '{blob.name}' downloaded to '{local_file_path}'.")

    def delete(self, bucket_path: str):
        """Delete a single blob or every blob under a prefix.

        A trailing ``/`` on ``bucket_path`` triggers the recursive delete; anything else is
        treated as a single-blob delete.

        Args:
            bucket_path: Blob name or directory prefix to delete.

        Raises:
            ValueError: If the blob does not exist (single file), or the prefix matches nothing
                (directory).

        Examples:
            - Delete a single blob:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.delete("example.txt")  # doctest: +SKIP

                ```
            - Delete every blob under a prefix:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.delete("data/")  # doctest: +SKIP

                ```

        Note:
            Directory deletes are not atomic: a crash mid-delete leaves partial state.
        """
        if bucket_path.endswith("/"):
            self._delete_directory(bucket_path)
        else:
            self._delete_file(bucket_path)

    def _delete_directory(self, bucket_path: str):
        """Delete every blob matching the prefix ``bucket_path``.

        Args:
            bucket_path: Prefix of the directory to delete (should end with ``/``).

        Raises:
            ValueError: If the prefix yields no blobs.
        """
        blobs = self.bucket.list_blobs(prefix=bucket_path)
        deleted_files = []
        for blob in blobs:
            blob.delete()
            deleted_files.append(blob.name)
            logger.info(f"Deleted file: {blob.name}")

        if not deleted_files:
            raise ValueError(f"No files found in the directory: {bucket_path}")

    def _delete_file(self, bucket_path: str):
        """Delete a single blob, raising if it does not exist.

        Args:
            bucket_path: Exact blob name to delete.

        Raises:
            ValueError: If the blob does not exist.
        """
        blob = self.bucket.blob(bucket_path)
        if blob.exists():
            blob.delete()
            logger.info(f"Blob {bucket_path} deleted.")
        else:
            raise ValueError(f"File {bucket_path} not found in the bucket.")

    def rename(self, old_path: str, new_path: str):
        """Rename a blob or directory by copy-then-delete.

        GCS has a native ``Blob.rewrite`` that is used per-blob for efficiency (no download /
        upload round-trip), followed by a delete of the original. For a single blob the
        operation is effectively atomic; for a directory it is *not* — a crash mid-rename leaves
        partial state.

        Args:
            old_path: Current blob name or directory prefix. Trailing ``/`` signals a directory
                rename.
            new_path: New blob name or directory prefix to rename to.

        Raises:
            ValueError: If ``old_path`` does not exist, or if ``new_path`` already exists.

        Examples:
            - Rename a single blob:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.rename("old_file.txt", "new_file.txt")  # doctest: +SKIP

                ```
            - Rename a directory recursively:
                ```python
                >>> gcs = GCS("my-project-id")  # doctest: +SKIP
                >>> bucket = gcs.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.rename("old_dir/", "new_dir/")  # doctest: +SKIP

                ```
        """
        # Check if the old path exists
        blobs = list(self.bucket.list_blobs(prefix=old_path))
        if not blobs:
            raise ValueError(f"The path '{old_path}' does not exist in the bucket.")

        # Check if the new path already exists
        if any(self.bucket.list_blobs(prefix=new_path)):
            raise ValueError(f"The destination path '{new_path}' already exists.")

        # Perform the rename
        for blob in blobs:
            old_blob_name = blob.name
            if old_path.endswith("/") and not old_blob_name.startswith(old_path):
                continue  # Skip unrelated files
            new_blob_name = old_blob_name.replace(old_path, new_path, 1)
            # create a copy of the blob to the new path
            new_blob = self.bucket.blob(new_blob_name)
            new_blob.rewrite(blob)
            # delete the original blob
            blob.delete()

        logger.info(f"Renamed '{old_path}' to '{new_path}'.")
