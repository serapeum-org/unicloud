# Installation

## Required Dependencies

- Python (3.11 or later)
- [numpy](https://www.numpy.org/) (2.1.2 or later)
- [pandas](https://pandas.pydata.org/) (2.2.0 or later)
- [loguru](https://github.com/Delgan/loguru) (0.7.2 or later)

Optional, provider-specific dependencies (installed via extras):

- AWS S3: [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) (1.35.40 or later)
- Google Cloud Storage: [google-cloud-storage](https://cloud.google.com/python/docs/reference/storage/latest) (2.1.0 or later), [google-api-python-client](https://github.com/googleapis/google-api-python-client) (2.119.0 or later)

## Installation Methods

It's recommended to install `unicloud` in a virtual environment to avoid conflicts with your system's Python packages.

### Conda

The easiest way to install `unicloud` is using the `conda` package manager. `unicloud` is available in the [conda-forge](https://conda-forge.org/) channel:

```bash
conda install -c conda-forge unicloud
```

This installs the base package. For provider SDKs, add them explicitly:

```bash
conda install -c conda-forge boto3                 # AWS S3
conda install -c conda-forge google-cloud-storage  # GCS
```

### PyPI

Install the base package:

```bash
pip install unicloud
```

Install with provider extras:

```bash
pip install unicloud[s3]    # pulls in boto3
pip install unicloud[gcs]   # pulls in google-cloud-storage + google-api-python-client
pip install unicloud[all]   # both providers
```

Pin a specific version:

```bash
pip install unicloud==0.4.0
```

### From Sources

The sources for unicloud can be downloaded from the [GitHub repository](https://github.com/serapeum-org/unicloud).

You can clone the public repository:

```bash
git clone https://github.com/serapeum-org/unicloud.git
```

Or download the [tarball](https://github.com/serapeum-org/unicloud/tarball/main):

```bash
curl -OJL https://github.com/serapeum-org/unicloud/tarball/main
```

Once you have a copy of the source, install it with:

```bash
python -m pip install .
```

To install directly from GitHub (HEAD of `main`):

```bash
pip install git+https://github.com/serapeum-org/unicloud.git
```

Or a specific release:

```bash
pip install git+https://github.com/serapeum-org/unicloud.git@0.4.0
```

### Development Installation

If you are planning to contribute, make a git clone and do an editable install so your changes are picked up without reinstalling.

```bash
git clone https://github.com/serapeum-org/unicloud.git
cd unicloud
pip install -e ".[all]"
```

This project uses [uv](https://docs.astral.sh/uv/) for dependency and environment management. To sync the dev environment (runtime deps + `dev` group + all provider extras):

```bash
uv sync --extra all --group dev
```

To include the docs group:

```bash
uv sync --extra all --group dev --group docs
```

## Credentials

### AWS S3

`unicloud`'s `S3` client reads credentials from the standard AWS environment variables:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`

It also honors IAM roles (on EC2 / ECS / Lambda) and the shared credentials file written by `aws configure`, because those are picked up by `boto3` directly. You can pass a custom `botocore.config.Config` via the `configs` argument:

```python
from botocore.config import Config
from unicloud.aws.aws import S3

s3 = S3(configs={
    "config": Config(signature_version="s3v4"),
    "region_name": "us-west-2",
})
```

### Google Cloud Storage

The `GCS` client supports three authentication modes:

1. **Service-account JSON file path** passed directly:
   ```python
   from unicloud.google_cloud.gcs import GCS
   gcs = GCS("my-project", service_key_path="/path/to/service-account.json")
   ```
2. **`GOOGLE_APPLICATION_CREDENTIALS` environment variable** pointing at a service-account JSON file:
   ```python
   gcs = GCS("my-project")
   ```
3. **`SERVICE_KEY_CONTENT` environment variable** containing the encoded contents of a service-account JSON file — useful for CI environments where you cannot ship a file. Encode it ahead of time with `unicloud.utils.encode`.

## Verifying the Installation

To check that the installation is successful, run:

```python
import unicloud
print(unicloud.__version__)
```

And verify the provider you care about imports:

```python
from unicloud.aws.aws import S3            # requires `[s3]` or `[all]`
from unicloud.google_cloud.gcs import GCS   # requires `[gcs]` or `[all]`
```
