# History

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
