# unicloud - Unified Cloud Storage API

[![Python Versions](https://img.shields.io/pypi/pyversions/unicloud.svg)](https://pypi.org/project/unicloud/)
[![PyPI version](https://badge.fury.io/py/unicloud.svg)](https://badge.fury.io/py/unicloud)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/unicloud.svg)](https://anaconda.org/conda-forge/unicloud)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Documentation Status](https://readthedocs.org/projects/unicloud/badge/?version=latest)](https://unicloud.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/Serapieum-of-alex/unicloud/branch/main/graph/badge.svg?token=g0DV4dCa8N)](https://codecov.io/gh/Serapieum-of-alex/unicloud)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![GitHub last commit](https://img.shields.io/github/last-commit/Serapieum-of-alex/unicloud)](https://github.com/Serapieum-of-alex/unicloud/commits/main)
[![GitHub issues](https://img.shields.io/github/issues/Serapieum-of-alex/unicloud)](https://github.com/Serapieum-of-alex/unicloud/issues)
[![GitHub stars](https://img.shields.io/github/stars/Serapieum-of-alex/unicloud)](https://github.com/Serapieum-of-alex/unicloud/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Serapieum-of-alex/unicloud)](https://github.com/Serapieum-of-alex/unicloud/network/members)

## Overview

**unicloud** provides a unified, provider-agnostic API for interacting with **AWS S3** and **Google Cloud Storage (GCS)**. It is built around a shared abstract interface so application code can be written once and run against either provider, while still exposing provider-specific functionality when needed.

Typical use cases:

- uploading data backups and build artifacts,
- downloading objects for batch analysis or ETL pipelines,
- managing buckets (listing, deleting, renaming, existence checks) from Python,
- writing tooling that targets either AWS or GCS without rewriting storage code.

Current release info
====================

| Name | Downloads | Version | Platforms |
| --- | --- | --- | --- |
| [![Conda Recipe](https://img.shields.io/badge/recipe-unicloud-green.svg)](https://anaconda.org/conda-forge/unicloud) | [![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/unicloud.svg)](https://anaconda.org/conda-forge/unicloud) [![Downloads](https://pepy.tech/badge/unicloud)](https://pepy.tech/project/unicloud) [![Downloads](https://pepy.tech/badge/unicloud/month)](https://pepy.tech/project/unicloud) [![Downloads](https://pepy.tech/badge/unicloud/week)](https://pepy.tech/project/unicloud) ![PyPI - Downloads](https://img.shields.io/pypi/dd/unicloud?color=blue&style=flat-square) | [![Conda Version](https://img.shields.io/conda/vn/conda-forge/unicloud.svg)](https://anaconda.org/conda-forge/unicloud) [![PyPI version](https://badge.fury.io/py/unicloud.svg)](https://badge.fury.io/py/unicloud) | [![Conda Platforms](https://img.shields.io/conda/pn/conda-forge/unicloud.svg)](https://anaconda.org/conda-forge/unicloud) |

## Installation

### Conda (recommended)

```bash
conda install -c conda-forge unicloud
```

### PyPI

```bash
pip install unicloud
```

Install provider-specific extras:

```bash
pip install unicloud[s3]   # AWS S3 only
pip install unicloud[gcs]  # Google Cloud Storage only
pip install unicloud[all]  # both providers
```

### Development version

```bash
pip install git+https://github.com/Serapieum-of-alex/unicloud
```

## Main Features

### Provider abstraction
- `CloudStorageFactory` — common client interface for AWS S3 and GCS.
- `AbstractBucket` — common bucket interface (`upload`, `download`, `delete`, `list_files`, `file_exists`, `rename`).

### AWS S3
- `S3` client built on top of `boto3`, reading credentials from standard AWS environment variables or accepting a custom `botocore.config.Config`.
- `Bucket` class for per-bucket operations including recursive directory upload/download.

### Google Cloud Storage
- `GCS` client built on top of `google-cloud-storage`, with three auth modes: service-account file path, `GOOGLE_APPLICATION_CREDENTIALS`, or encoded `SERVICE_KEY_CONTENT`.
- `Bucket` class mirroring the S3 API surface for parity across providers.

### Utilities
- `unicloud.utils.encode` / `decode` for ferrying service-account JSON through environment variables safely.

## Quick Start

### AWS S3

```python
from unicloud.aws.aws import S3

# Credentials read from AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_DEFAULT_REGION
s3 = S3()

bucket = s3.get_bucket("my-bucket")
bucket.upload("local/file.txt", "remote/path/file.txt")
bucket.download("remote/path/file.txt", "downloads/file.txt")

assert bucket.file_exists("remote/path/file.txt")
print(bucket.list_files())
```

### Google Cloud Storage

```python
from unicloud.google_cloud.gcs import GCS

# Option A: service-account JSON file
gcs = GCS("my-project-id", service_key_path="/path/to/service-account.json")

# Option B: GOOGLE_APPLICATION_CREDENTIALS env var
# gcs = GCS("my-project-id")

bucket = gcs.get_bucket("my-bucket")
bucket.upload("local/dir", "remote/dir")          # recursive directory upload
bucket.download("remote/dir", "downloads/")       # recursive download
bucket.delete("remote/dir/obsolete.txt")
```

### Writing provider-agnostic code

Because both `S3` and `GCS` implement `CloudStorageFactory`, and both `Bucket` classes implement `AbstractBucket`, you can write functions that accept either one:

```python
from unicloud.abstract_class import CloudStorageFactory


def sync(client: CloudStorageFactory, bucket_name: str, local: str, remote: str) -> None:
    bucket = client.get_bucket(bucket_name)
    bucket.upload(local, remote)
```

For more examples, see the [Reference](reference/abstract-class.md) pages.

## Contributing

Contributions are welcome — see the [Contributing guide](contributing.md).

## License

This project is licensed under the GPLv3 License — see [LICENSE](LICENSE.md) for details.

## Citation

If you use unicloud in your work, please cite it as:

```
Farrag, M. (2024). unicloud: A unified Python API for AWS S3 and Google Cloud Storage.
https://github.com/Serapieum-of-alex/unicloud
```

BibTeX:

```bibtex
@software{unicloud2024,
  author = {Farrag, Mostafa},
  title  = {unicloud: A unified Python API for AWS S3 and Google Cloud Storage},
  url    = {https://github.com/Serapieum-of-alex/unicloud},
  year   = {2024}
}
```
