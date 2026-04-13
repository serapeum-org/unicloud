---
name: Bug report
about: Report a reproducible problem with unicloud (AWS S3, Google Cloud Storage, uploads, downloads, bucket operations)
title: "[Bug]: "
labels: [bug]
assignees: ''
---

## Description
A clear and concise description of the bug. What is wrong and what did you expect instead?

## Cloud provider
- [ ] AWS S3
- [ ] Google Cloud Storage (GCS)
- [ ] Both / not sure

## Minimal Reproducible Example (MRE)
Provide the smallest code snippet that reproduces the issue. Include imports and any necessary setup. **Redact bucket names, object keys, and credentials.**

```python
# Please adjust to the minimal code that triggers the issue
from unicloud.aws.aws import S3
# or
from unicloud.google_cloud.gcs import GCS

# code here
```

### File / object sample (if applicable)
- If the bug depends on a specific object layout, describe it (size, content type, folder depth, number of items). If the issue involves a directory upload/download, describe the local tree.

## Steps to Reproduce
1. ...
2. ...
3. ...

## Expected behavior
Describe what you expected to happen.

## Actual behavior / Error traceback
Paste the full error/traceback if there is one. **Scrub any credentials, bucket names, or object keys you do not want to share.**

```
<full traceback here>
```

## Environment
Please complete the following information:
- OS: [e.g., Windows 11, macOS 14, Ubuntu 24.04]
- Python: [e.g., 3.12.2]
- unicloud version: [e.g., 0.4.0]
- Installation method: [pip, pip extras (`[s3]`, `[gcs]`, `[all]`), from source, editable install]
- Relevant dependencies (if known):
  - boto3 / botocore: [e.g., 1.35.40]
  - google-cloud-storage: [e.g., 2.18.0]

## Authentication setup
How did you authenticate? (check all that apply; do NOT paste secrets)
- [ ] AWS env vars (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_DEFAULT_REGION`)
- [ ] AWS shared credentials file / IAM role / SSO
- [ ] Custom `boto3` config passed via `S3(configs=...)`
- [ ] GCS service-account JSON via `service_key_path`
- [ ] `GOOGLE_APPLICATION_CREDENTIALS` env var
- [ ] `SERVICE_KEY_CONTENT` env var (encoded)

## Additional context
Bucket region, object size, network setup (VPC, proxy), related issues, or anything else that could help diagnose the problem.
