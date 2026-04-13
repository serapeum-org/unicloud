"""AWS S3 implementation of the unicloud storage contract.

This module provides :class:`S3`, a :class:`CloudStorageFactory` built on top of ``boto3``, and a
companion :class:`Bucket` class that implements :class:`AbstractBucket` for per-object operations
(upload, download, delete, list, exists, rename) against a single S3 bucket.

Credentials are read from the standard AWS environment variables (``AWS_ACCESS_KEY_ID``,
``AWS_SECRET_ACCESS_KEY``, ``AWS_DEFAULT_REGION``). Additional ``boto3.client`` keyword arguments
(for example a custom ``botocore.config.Config``) can be passed through :class:`S3` via the
``configs`` parameter.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

from unicloud.abstract_class import AbstractBucket, CloudStorageFactory

logger = logging.getLogger(__name__)


class S3(CloudStorageFactory):
    """AWS S3 client — the :class:`CloudStorageFactory` implementation for Amazon S3.

    Instantiating the class constructs a ``boto3`` S3 client using credentials pulled from the
    environment. Additional keyword arguments that you would otherwise pass to ``boto3.client``
    (for example a custom ``botocore.config.Config``, or a different ``region_name``) can be
    forwarded via the ``configs`` parameter.

    Examples:
        - Create a client from environment variables only:
            ```python
            >>> s3 = S3()  # doctest: +SKIP

            ```
        - Create a client with a custom botocore config and region override:
            ```python
            >>> from botocore.config import Config
            >>> s3 = S3(configs={
            ...     "config": Config(signature_version="s3v4"),
            ...     "region_name": "us-west-2",
            ... })  # doctest: +SKIP

            ```

    See Also:
        unicloud.google_cloud.gcs.GCS: The matching Google Cloud Storage implementation.
    """

    def __init__(
        self,
        configs: Optional[Dict] = None,
    ):
        """Initialize the S3 client.

        Credentials are read from the standard AWS environment variables. Any extra keyword
        arguments you want passed to ``boto3.client("s3", ...)`` can be supplied via ``configs``
        — they override the defaults that this class sets for ``service_name``, ``region_name``,
        ``aws_access_key_id``, and ``aws_secret_access_key``.

        Args:
            configs: Optional dictionary of extra keyword arguments to forward to ``boto3.client``.
                Useful for passing a ``botocore.config.Config`` (``{"config": Config(...)}``), a
                non-default region (``{"region_name": "us-west-2"}``), or for swapping the
                service name in tests.

        Raises:
            ValueError: If any of ``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``, or
                ``AWS_DEFAULT_REGION`` is not set in the environment.
            NoCredentialsError: Propagated from ``boto3`` when it cannot find credentials to sign
                requests with.
            PartialCredentialsError: Propagated from ``boto3`` when only some of the required
                credentials are present.

        Examples:
            - Default construction reading every credential from the environment:
                ```python
                >>> s3 = S3()  # doctest: +SKIP

                ```
            - Pass a custom botocore Config to override the signature version:
                ```python
                >>> from botocore.config import Config
                >>> s3 = S3(configs={
                ...     "config": Config(signature_version="s3v4"),
                ...     "region_name": "us-west-2",
                ... })  # doctest: +SKIP

                ```

        See Also:
            https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html: Canonical
                list of the AWS environment variables this class honors.
        """
        self._client = self.create_client(configs)

    @property
    def client(self):
        """Return the cached ``boto3`` S3 client.

        Returns:
            boto3.client: The S3 client instance produced by :meth:`create_client`.
        """
        return self._client

    def create_client(self, configs: Optional[Dict] = None) -> boto3.client:
        """Build a ``boto3`` S3 client from environment credentials plus optional overrides.

        This is the hook used internally by :meth:`__init__` and re-exposed publicly so callers
        can rebuild the client (for example after rotating a signing config) without re-creating
        the :class:`S3` instance. Alternative authentication paths — IAM roles on EC2/ECS/Lambda,
        the shared credentials file written by ``aws configure``, AWS SSO — are all picked up by
        ``boto3`` itself when the corresponding env vars happen to be set to dummy values.

        Args:
            configs: Optional dictionary of extra keyword arguments to merge into the
                ``boto3.client`` call. For example, unsigned requests:
                ``{"config": Config(signature_version=botocore.UNSIGNED)}``. Keys in this dict
                override the defaults the method sets.

        Returns:
            boto3.client: A configured S3 client ready for ``upload_file`` / ``download_file`` /
            etc. calls.

        Raises:
            ValueError: If any of ``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``, or
                ``AWS_DEFAULT_REGION`` is not set in the environment.
            NoCredentialsError: Raised by ``boto3`` if it cannot resolve credentials.
            PartialCredentialsError: Raised by ``boto3`` if only some credentials are resolvable.

        Examples:
            - Build a client with a custom signature version and inspect the region:
                ```python
                >>> from botocore.config import Config
                >>> s3 = S3(configs={
                ...     "config": Config(signature_version="s3v4"),
                ...     "region_name": "us-west-2",
                ... })  # doctest: +SKIP
                >>> s3.client.meta.region_name  # doctest: +SKIP
                'us-west-2'

                ```
        """
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        if aws_access_key_id is None:
            raise ValueError("AWS_ACCESS_KEY_ID is not set.")

        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        if aws_secret_access_key is None:
            raise ValueError("AWS_SECRET_ACCESS_KEY is not set.")

        region = os.getenv("AWS_DEFAULT_REGION")
        if region is None:
            raise ValueError("AWS_DEFAULT_REGION is not set.")

        # Set defaults and allow overrides through client_configs
        client_params = {
            "service_name": "s3",
            "region_name": region,
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
        }
        if configs:
            client_params.update(configs)

        try:
            return boto3.client(**client_params)
        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error("AWS credentials not found.")
            raise e

    def upload(self, local_path: Union[str, Path], bucket_path: str):
        """Upload a single file to S3 via the factory-level shortcut.

        Prefer :meth:`get_bucket` followed by :meth:`Bucket.upload` for anything beyond a
        one-shot file push — the bucket-level API supports recursive directory uploads and
        ``overwrite`` handling.

        Args:
            local_path: Path to the local file to upload.
            bucket_path: Destination path in the form ``"<bucket_name>/<object_key>"``. Split on
                the first ``/``.

        Raises:
            Exception: Any ``boto3.client.upload_file`` error is re-raised unchanged after being
                logged.

        Examples:
            - Upload a local file to a bucket under a named key:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> s3.upload("local/file.txt", "my-bucket/folder/file.txt")  # doctest: +SKIP

                ```
        """
        bucket_name, object_name = bucket_path.split("/", 1)
        try:
            self.client.upload_file(local_path, bucket_name, object_name)
            logger.info(f"File {local_path} uploaded to {bucket_path}.")
        except Exception as e:
            logger.error("Error uploading file to S3:", exc_info=True)
            raise e

    def download(self, bucket_path: str, local_path: Union[str, Path]):
        """Download a single object from S3 via the factory-level shortcut.

        Args:
            bucket_path: Source path in the form ``"<bucket_name>/<object_key>"``.
            local_path: Local destination path for the downloaded file.

        Raises:
            Exception: Any ``boto3.client.download_file`` error is re-raised unchanged after
                being logged.

        Examples:
            - Download a single object to a local path:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> s3.download("my-bucket/folder/file.txt", "local/file.txt")  # doctest: +SKIP

                ```
        """
        bucket_name, object_name = bucket_path.split("/", 1)
        try:
            self.client.download_file(bucket_name, object_name, local_path)
            logger.info(f"File {bucket_path} downloaded to {local_path}.")
        except Exception as e:
            logger.error("Error downloading file from S3:", exc_info=True)
            raise e

    def get_bucket(self, bucket_name: str) -> "Bucket":
        """Return a :class:`Bucket` handle for per-object operations on ``bucket_name``.

        The returned object wraps a ``boto3.resources.factory.s3.Bucket`` resource (which is a
        richer interface than the flat client) and exposes the unicloud :class:`AbstractBucket`
        surface on top of it.

        Args:
            bucket_name: The AWS S3 bucket name to look up. The method does *not* verify that
                the bucket exists; that error surfaces on the first actual operation.

        Returns:
            Bucket: A :class:`Bucket` wrapper for the named S3 bucket.

        Examples:
            - Get a bucket and list its contents:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.list_files()  # doctest: +SKIP
                ['file1.txt', 'folder/file2.txt']

                ```
        """
        s3 = boto3.resource(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION"),
        )
        bucket = s3.Bucket(bucket_name)
        return Bucket(bucket)


class Bucket(AbstractBucket):
    """AWS S3 bucket handle — the :class:`AbstractBucket` implementation for S3.

    Instances wrap a ``boto3.resources.factory.s3.Bucket`` and expose the unicloud contract on top
    of it: upload/download (files and directories), delete, list, existence-check, and rename.

    Examples:
        - Prefer :meth:`S3.get_bucket` over constructing directly, then probe the bucket:
            ```python
            >>> s3 = S3()  # doctest: +SKIP
            >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
            >>> bucket.file_exists("folder/file.txt")  # doctest: +SKIP
            True

            ```
    """

    def __init__(self, bucket):  # :boto3.resources("s3").Bucket
        """Wrap a ``boto3`` S3 Bucket resource.

        Args:
            bucket: A ``boto3.resources.factory.s3.Bucket`` instance — typically produced by
                ``boto3.resource("s3").Bucket(name)``.

        Examples:
            - Instantiate directly from a boto3 resource:
                ```python
                >>> import boto3
                >>> resource = boto3.resource("s3")  # doctest: +SKIP
                >>> bucket = Bucket(resource.Bucket("my-bucket"))  # doctest: +SKIP

                ```
            - Or let S3.get_bucket build it for you (preferred):
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP

                ```
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
    def bucket(self):
        """Return the underlying ``boto3`` S3 Bucket resource.

        Exposed as an escape hatch for callers that need to drop down to the native SDK
        (for example to set lifecycle policies, which unicloud does not wrap).

        Returns:
            boto3.resources.factory.s3.Bucket: The wrapped boto3 resource.
        """
        return self._bucket

    @property
    def name(self):
        """Return the bucket name.

        Returns:
            str: The name of the wrapped S3 bucket.
        """
        return self.bucket.name

    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        """List object keys in the bucket, optionally filtered by a key prefix.

        Args:
            prefix: Optional key prefix to filter the listing. Passing ``"folder/"`` lists every
                object whose key starts with ``"folder/"``. When ``None`` (the default), every
                object in the bucket is returned.

        Returns:
            List[str]: Object keys matching the prefix, in the order the SDK returns them.

        Examples:
            - List every object in the bucket:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.list_files()  # doctest: +SKIP
                ['file1.txt', 'folder/file2.txt']

                ```
            - List only objects under a folder:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.list_files(prefix="folder/")  # doctest: +SKIP
                ['folder/file2.txt']

                ```
        """
        if prefix is None:
            prefix = ""

        return [obj.key for obj in self.bucket.objects.filter(Prefix=prefix)]

    def upload(
        self, local_path: Union[str, Path], bucket_path: str, overwrite: bool = False
    ):
        """Upload a file or directory to the bucket.

        When ``local_path`` is a directory, every file beneath it is uploaded recursively and the
        relative tree under ``bucket_path`` is preserved. Empty directories raise a
        ``ValueError`` because S3 has no concept of an empty directory.

        Args:
            local_path: Path to the local file or directory to upload.
            bucket_path: Destination key (for a single file) or destination prefix (for a
                directory). Trailing ``/`` is tolerated.
            overwrite: If ``False`` (the default), uploading to a key that already exists raises
                ``ValueError``. If ``True``, the existing object is replaced silently.

        Raises:
            FileNotFoundError: If ``local_path`` does not exist.
            ValueError: If ``local_path`` is an empty directory, neither a file nor a directory,
                or already exists in the bucket while ``overwrite=False``.

        Examples:
            - Upload a single file:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.upload("local/file.txt", "folder/file.txt", overwrite=False)  # doctest: +SKIP

                ```
            - Upload a directory recursively, overwriting any conflicts:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.upload("local/dir", "remote/dir", overwrite=True)  # doctest: +SKIP

                ```
        """
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Path {local_path} does not exist.")

        if local_path.is_file():
            self._upload_file(local_path, bucket_path, overwrite)
        elif local_path.is_dir():
            self._upload_directory(local_path, bucket_path, overwrite)
        else:
            raise ValueError(
                f"Invalid path type: {local_path} is neither a file nor a directory."
            )

    def _upload_file(self, local_path: Path, bucket_path: str, overwrite: bool):
        """Upload a single file, honoring the ``overwrite`` flag.

        Args:
            local_path: Local file to upload.
            bucket_path: Destination object key in the bucket.
            overwrite: When ``False``, raises if ``bucket_path`` already exists.

        Raises:
            ValueError: If ``bucket_path`` already exists and ``overwrite=False``.
        """
        if not overwrite and self.file_exists(bucket_path):
            raise ValueError(f"File {bucket_path} already exists in the bucket.")
        self.bucket.upload_file(Filename=str(local_path), Key=bucket_path)
        logger.info(f"File {local_path} uploaded to {bucket_path}.")

    def _upload_directory(self, local_path: Path, bucket_path: str, overwrite: bool):
        """Upload every file under ``local_path`` recursively.

        Args:
            local_path: Local directory to walk.
            bucket_path: Destination prefix in the bucket.
            overwrite: Forwarded to :meth:`_upload_file` for each uploaded file.

        Raises:
            ValueError: If ``local_path`` is empty.
        """
        if local_path.is_dir() and not any(local_path.iterdir()):
            raise ValueError(f"Directory {local_path} is empty.")

        for root, _, files in os.walk(local_path):
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(local_path)
                s3_path = f"{bucket_path.rstrip('/')}/{relative_path.as_posix()}"
                self._upload_file(file_path, s3_path, overwrite)

    def download(
        self, bucket_path: str, local_path: Union[str, Path], overwrite: bool = False
    ):
        """Download a file or a directory from the bucket.

        A trailing ``/`` on ``bucket_path`` triggers the recursive-directory code path; anything
        else is treated as a single-object download.

        Args:
            bucket_path: Path inside the bucket to download. Trailing ``/`` means "directory".
            local_path: Local destination. For a single file this is the full filename; for a
                directory it is the directory root (created if missing).
            overwrite: If ``False`` (the default), existing local files raise ``ValueError``. If
                ``True``, they are overwritten.

        Raises:
            ValueError: If the local destination already exists with ``overwrite=False``, or if
                the bucket directory is empty.

        Examples:
            - Download a single object:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.download("folder/file.txt", "local/file.txt", overwrite=False)  # doctest: +SKIP

                ```
            - Download a directory recursively with overwrites:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.download("folder/", "local/folder/", overwrite=True)  # doctest: +SKIP

                ```
        """
        local_path = Path(local_path)
        if bucket_path.endswith("/"):
            self._download_directory(bucket_path, local_path, overwrite)
        else:
            self._download_file(bucket_path, local_path, overwrite)

    def _download_file(self, bucket_path: str, local_path: Path, overwrite: bool):
        """Download a single object, honoring the ``overwrite`` flag.

        Args:
            bucket_path: Source object key in the bucket.
            local_path: Local destination filename. Parent directories are created if missing.
            overwrite: When ``False``, raises if ``local_path`` already exists.

        Raises:
            ValueError: If ``local_path`` already exists and ``overwrite=False``.
        """
        if local_path.exists() and not overwrite:
            raise ValueError(f"File {local_path} already exists locally.")

        local_path.parent.mkdir(parents=True, exist_ok=True)

        self.bucket.download_file(Key=bucket_path, Filename=str(local_path))
        logger.info(f"File {bucket_path} downloaded to {local_path}.")

    def _download_directory(self, bucket_path: str, local_path: Path, overwrite: bool):
        """Download every object under the prefix ``bucket_path`` recursively.

        Args:
            bucket_path: Source prefix in the bucket (should end with ``/``).
            local_path: Local root directory to write into; created if missing.
            overwrite: Forwarded to :meth:`_download_file` for each file.

        Raises:
            ValueError: If the prefix yields no objects.
        """
        if not any(self.list_files(bucket_path)):
            raise ValueError(f"Directory {bucket_path} is empty.")

        local_path.mkdir(parents=True, exist_ok=True)
        for obj in self.bucket.objects.filter(Prefix=bucket_path):
            if obj.key.endswith("/"):
                continue
            relative_path = Path(obj.key).relative_to(bucket_path)
            self._download_file(obj.key, local_path / relative_path, overwrite)

    def delete(self, bucket_path: str):
        """Delete a single object or a directory (recursively) from the bucket.

        A trailing ``/`` on ``bucket_path`` triggers the recursive delete; anything else is
        treated as a single-object delete.

        Args:
            bucket_path: Object key or directory prefix to delete. Trailing ``/`` means
                "directory".

        Raises:
            ValueError: If the key does not exist (for single files) or the prefix matches
                nothing (for directories).

        Examples:
            - Delete a single file:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.delete("folder/file.txt")  # doctest: +SKIP

                ```
            - Delete every object under a prefix:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.delete("folder/")  # doctest: +SKIP

                ```
        """
        if bucket_path.endswith("/"):
            self._delete_directory(bucket_path)
        else:
            self._delete_file(bucket_path)

    def _delete_file(self, bucket_path: str):
        """Delete a single object, raising if it does not exist.

        Args:
            bucket_path: Exact object key to delete.

        Raises:
            ValueError: If no object with that exact key exists.
        """
        objects = list(self.bucket.objects.filter(Prefix=bucket_path))
        if not objects or objects[0].key != bucket_path:
            raise ValueError(f"File {bucket_path} not found in the bucket.")
        self.bucket.Object(bucket_path).delete()
        logger.info(f"Deleted: {bucket_path}")

    def _delete_directory(self, bucket_path: str):
        """Delete every object matching the prefix ``bucket_path``.

        Args:
            bucket_path: Prefix of the directory to delete (should end with ``/``).

        Raises:
            ValueError: If the prefix yields no objects.
        """
        objects = list(self.bucket.objects.filter(Prefix=bucket_path))
        if not objects:
            raise ValueError(f"No files found in the directory: {bucket_path}")

        for obj in objects:
            obj.delete()
            print(f"Deleted {obj.key}.")

    def file_exists(self, file_name: str) -> bool:
        """Return whether an exact object key exists in the bucket.

        Implemented as a ``list_objects`` prefix filter followed by an exact-match check, so it
        is safe against the common "prefix match" pitfall where ``"file"`` would also match
        ``"file-backup"``.

        Args:
            file_name: Exact object key to check.

        Returns:
            bool: ``True`` if an object with that exact key exists, ``False`` otherwise.

        Examples:
            - Check for an existing object:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.file_exists("folder/file.txt")  # doctest: +SKIP
                True

                ```
            - Check for a missing object:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.file_exists("folder/missing.txt")  # doctest: +SKIP
                False

                ```
        """
        objs = list(self.bucket.objects.filter(Prefix=file_name))
        return len(objs) > 0 and objs[0].key == file_name

    def rename(self, old_path: str, new_path: str):
        """Rename an object or directory by copy-then-delete.

        S3 has no native rename, so this method copies each matching object to the new key and
        then deletes the original. For a single object the operation is effectively atomic; for
        a directory it is *not* — a crash mid-rename leaves partial state.

        Args:
            old_path: Current object key or directory prefix. Trailing ``/`` signals a directory
                rename.
            new_path: New object key or directory prefix to rename to.

        Raises:
            ValueError: If ``old_path`` does not exist, or if ``new_path`` already exists.

        Examples:
            - Rename a single object:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.rename("old_file.txt", "new_file.txt")  # doctest: +SKIP

                ```
            - Rename a directory recursively:
                ```python
                >>> s3 = S3()  # doctest: +SKIP
                >>> bucket = s3.get_bucket("my-bucket")  # doctest: +SKIP
                >>> bucket.rename("old_dir/", "new_dir/")  # doctest: +SKIP

                ```
        """
        # Check if the old path exists
        objects = list(self.bucket.objects.filter(Prefix=old_path))
        if not objects:
            raise ValueError(f"The path '{old_path}' does not exist in the bucket.")

        # Check if the new path already exists
        if any(self.bucket.objects.filter(Prefix=new_path)):
            raise ValueError(f"The destination path '{new_path}' already exists.")

        # Perform the rename
        for obj in objects:
            old_object_name = obj.key
            if old_path.endswith("/") and not old_object_name.startswith(old_path):
                continue  # Skip unrelated files
            new_object_name = old_object_name.replace(old_path, new_path, 1)
            # create a copy of the object to the new path
            self.bucket.Object(new_object_name).copy_from(
                CopySource={"Bucket": self.bucket.name, "Key": old_object_name}
            )
            # delete the original object
            obj.delete()

        logger.info(f"Renamed '{old_path}' to '{new_path}'.")
