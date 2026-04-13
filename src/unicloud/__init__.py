"""Unified Python API for AWS S3 and Google Cloud Storage.

`unicloud` exposes a single abstract interface (:class:`unicloud.abstract_class.CloudStorageFactory` and
:class:`unicloud.abstract_class.AbstractBucket`) that both the AWS S3 implementation
(:mod:`unicloud.aws.aws`) and the Google Cloud Storage implementation
(:mod:`unicloud.google_cloud.gcs`) adhere to, so callers can write provider-agnostic code for uploads,
downloads, listings, deletions, existence checks, and renames.

The installed package version is exposed as :data:`__version__` — resolved from the installed distribution
metadata, falling back to ``"unknown"`` when the package is not installed (e.g. when imported from a source
checkout without a build step).

Examples:
    - Read the installed package version at runtime:
        ```python
        >>> import unicloud
        >>> isinstance(unicloud.__version__, str)
        True

        ```
    - Import a provider-specific client (requires the matching optional extra):
        ```python
        >>> from unicloud.aws.aws import S3  # doctest: +SKIP
        >>> from unicloud.google_cloud.gcs import GCS  # doctest: +SKIP

        ```
"""

try:
    from importlib.metadata import PackageNotFoundError, version  # type: ignore
except ImportError:  # pragma: no cover
    from importlib_metadata import PackageNotFoundError, version  # type: ignore


try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
