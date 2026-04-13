"""Abstract base classes defining the unicloud storage contract.

This module pins down the shape every provider must implement so callers can write provider-agnostic
cloud-storage code. Two ABCs are exposed:

- :class:`CloudStorageFactory` — the provider-level client (authentication, bucket lookup, generic
  upload/download helpers).
- :class:`AbstractBucket` — a single bucket handle with per-object operations (upload, download, delete,
  list, existence check).

Concrete implementations live under :mod:`unicloud.aws.aws` (AWS S3) and
:mod:`unicloud.google_cloud.gcs` (Google Cloud Storage). Both providers ship a class literally named
``Bucket`` that subclasses :class:`AbstractBucket`; adding a new public method to one should usually be
mirrored in the other to keep the abstraction honest.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union


class CloudStorageFactory(ABC):
    """Provider-level cloud-storage client contract.

    Every concrete provider (AWS S3, Google Cloud Storage, ...) must subclass this ABC and implement
    :meth:`create_client`, :meth:`client`, :meth:`upload`, :meth:`download`, and :meth:`get_bucket`.
    Callers that want to stay provider-agnostic should accept ``CloudStorageFactory`` and only call
    the methods declared here.

    Examples:
        - Accept either provider in a type-annotated function:
            ```python
            >>> from unicloud.abstract_class import CloudStorageFactory
            >>> def sync(client: CloudStorageFactory, bucket: str, src: str, dst: str) -> None:
            ...     client.get_bucket(bucket).upload(src, dst)

            ```
    """

    @abstractmethod
    def create_client(self):
        """Construct and return the underlying provider SDK client.

        Implementations read credentials from environment variables (or accept a provider-specific
        config argument) and return the native client object — for example a ``boto3.client`` for AWS
        or a ``google.cloud.storage.Client`` for GCS.

        Returns:
            The provider-specific SDK client instance. Type varies by provider.
        """
        pass

    @property
    @abstractmethod
    def client(self):
        """Return the cached provider SDK client.

        Returns:
            The same instance that :meth:`create_client` produced. Type varies by provider.
        """
        pass

    @abstractmethod
    def upload(self, file_path, destination):
        """Upload a single local file to the provider.

        This is a convenience helper on the factory; prefer :meth:`get_bucket` + the bucket-level
        ``upload`` for anything non-trivial (overwrite handling, directory uploads, etc.).

        Args:
            file_path: Path to the local file to upload.
            destination: Destination in the provider. The convention used by both shipped providers
                is ``"<bucket_name>/<object_key>"``.
        """
        pass

    @abstractmethod
    def download(self, source, file_path):
        """Download a single object to a local path.

        Args:
            source: Provider-side path. Both shipped providers use ``"<bucket_name>/<object_key>"``.
            file_path: Local destination path for the downloaded file.
        """
        pass

    @abstractmethod
    def get_bucket(self, bucket_name) -> "AbstractBucket":
        """Return a bucket handle for per-object operations.

        Args:
            bucket_name: The name (or ID) of the bucket to look up.

        Returns:
            AbstractBucket: A concrete :class:`AbstractBucket` subclass from the provider.
        """
        pass


class AbstractBucket(ABC):
    """Per-bucket operation contract.

    A bucket handle exposes upload/download/delete/list/exists for a single bucket. Both providers
    ship a :class:`Bucket` class that subclasses this ABC and shares the same method names; provider
    parity is intentional.

    Examples:
        - Type-annotate a helper that works with either provider's bucket:
            ```python
            >>> from unicloud.abstract_class import AbstractBucket
            >>> def push_then_verify(bucket: AbstractBucket, local: str, remote: str) -> bool:
            ...     bucket.upload(local, remote)
            ...     return bucket.file_exists(remote)

            ```
    """

    @abstractmethod
    def __str__(self):
        """Return a short, human-readable representation of the bucket.

        Returns:
            str: Usually ``"Bucket: <name>"``.
        """
        pass

    @abstractmethod
    def __repr__(self):
        """Return a developer-facing representation of the bucket.

        Returns:
            str: Usually the same as :meth:`__str__`.
        """
        pass

    @abstractmethod
    def upload(
        self,
        local_path: Union[str, Path],
        bucket_path: Union[str, Path],
        overwrite: bool = False,
    ):
        """Upload a file or directory into the bucket.

        Implementations must accept both single files and directories; when ``local_path`` is a
        directory, the upload is recursive and preserves the relative tree.

        Args:
            local_path: Local file or directory to upload.
            bucket_path: Destination prefix inside the bucket.
            overwrite: If ``False`` (the default), existing destination objects cause a ``ValueError``.
                If ``True``, existing objects are overwritten silently.
        """
        pass

    @abstractmethod
    def download(
        self, bucket_path: str, local_path: Union[str, Path], overwrite: bool = False
    ):
        """Download a file or directory out of the bucket.

        A trailing ``/`` on ``bucket_path`` signals a directory download; otherwise a single object
        is fetched.

        Args:
            bucket_path: Source path inside the bucket. Trailing ``/`` triggers a recursive download.
            local_path: Local destination path.
            overwrite: If ``False`` (the default), existing local files cause a ``ValueError``.
                If ``True``, existing files are overwritten.
        """
        pass

    @abstractmethod
    def delete(self, bucket_path: str):
        """Delete a file or directory from the bucket.

        A trailing ``/`` on ``bucket_path`` signals a recursive directory delete.

        Args:
            bucket_path: Path inside the bucket to delete.
        """
        pass

    @abstractmethod
    def list_files(self):
        """List the objects in the bucket.

        Implementations may accept provider-specific filtering arguments (prefix, glob pattern,
        max results, ...) as additional parameters.

        Returns:
            list[str]: Object keys, in provider-defined order.
        """
        pass

    @abstractmethod
    def file_exists(self, file_name: str) -> bool:
        """Return whether an object exists in the bucket.

        Args:
            file_name: Object key to check.

        Returns:
            bool: ``True`` if the object exists, ``False`` otherwise.
        """
        pass

    @property
    @abstractmethod
    def name(self):
        """Return the bucket name.

        Returns:
            str: The bucket's name (AWS) or ID (GCS).
        """
        pass
