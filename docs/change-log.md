# History

## 0.4.1 (2026-04-13)


- chore: align tooling and docs with serapeum-org template (#52)
- Migrate unicloud to the shared Serapeum Python stack so it can use the                                         
  same CI composite actions, release flow, and doc pipeline as statista
  and friends.                                                                                                   
                           
  - build: move from Poetry + poetry-core to uv + hatchling; rewrite                                             
    pyproject.toml to PEP 621 with [dependency-groups] and pip-installable                                       
    [s3] / [gcs] / [all] optional-dependencies; drop poetry.lock, add
    uv.lock; drop hand-written __author__/__email__ in favor of PEP 621
    metadata.
  - docs: replace the Sphinx + ReadTheDocs site with MkDocs Material and
    mkdocstrings; convert every RST page to Markdown; add reference pages
    for the abstract interface, both providers, and utils; convert every
    module docstring from NumPy to Google style.
  - ci: retire pypi-deployment.yml / conda-deployment.yml / dependabot;
    add tests.yml (uv matrix 3.11/3.12/3.13), rewrite github-release.yml
    as an admin-only commitizen-driven workflow, and rewrite
    pypi-release.yml to trigger off the release workflow with a
    branch-aware checkout; add github-pages-mkdocs.yml for the new site;
    update every issue template and the PR template to ask for
    cloud-storage specifics.
  - feat(aws): let S3.__init__ accept a `configs` dict that forwards to
    boto3.client, enabling a custom botocore.config.Config, non-default
    region overrides, and service-name swapping in tests; covered by
    TestCreateClient in tests/aws/test_aws.py.
-   ref: #211, #212, #213

## 0.4.0 (2024-12-27)

### Dev
- Add logger to both the `S3` and `GCS` classes.

### GCS
- Add `rename` method to the `Bucket` class.

### AWS
- The `S3` class initialization no longer takes AWS credentials as arguments; they are read from environment variables.
- Add `get_bucket` method to the `S3` class to return a more comprehensive `Bucket` object.
- Add `Bucket` class that represents an S3 bucket.
- The `Bucket` class has methods for uploading, downloading, deleting, renaming, and listing files.

## 0.3.0 (2024-12-15)

- Create a `utils` module.
- Move the `aws` and `gcs` modules into submodules `aws` and `google_cloud`.

### GCS
- Create a `Bucket` class that represents a Google Cloud Storage bucket.
- The `Bucket` class has methods for uploading, downloading, and deleting files.
- The `Bucket` class has methods for listing files in the bucket.

## 0.2.0 (2024-10-11)

- Bump up versions of dependencies.

## 0.1.0 (2024-03-01)

- Initial release with Google Cloud Storage and Amazon S3 classes.
