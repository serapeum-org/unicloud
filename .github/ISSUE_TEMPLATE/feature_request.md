---
name: Feature request
about: Propose a new capability or enhancement for unicloud (AWS S3, GCS, provider abstraction, bucket operations, auth)
title: "[Feature]: "
labels: [enhancement]
assignees: ''
---

## Problem statement
What problem are you trying to solve? Why is it important in the context of cloud storage (uploads/downloads, bucket management, cross-provider workflows, authentication, etc.)?

## Proposed solution
Describe the feature in detail. If this is an API addition/change, specify the interface:

```python
# Example
from unicloud.abstract_class import CloudStorageFactory, AbstractBucket

class MyProvider(CloudStorageFactory):
    def new_method(self, ...) -> ...:
        ...
```

- Module(s) affected: [e.g., `unicloud.aws.aws`, `unicloud.google_cloud.gcs`, `unicloud.abstract_class`]
- New classes/functions/methods: [list]
- Provider scope: [AWS only | GCS only | both — if one, why?]
- Parameter names/defaults and return types: [describe]

## Example usage
Provide a minimal code snippet demonstrating how the feature would be used.

```python
# sample usage
```

## Alternatives considered
List any alternative approaches or prior art (boto3 / google-cloud-storage native APIs, fsspec, s3fs, gcsfs, cloudpathlib, etc.). Explain trade-offs.

## Backward compatibility
- Does this change break existing APIs (`S3`, `GCS`, `Bucket`, `CloudStorageFactory`, `AbstractBucket`)? If yes, describe migration path.
- Does it affect the `[gcs]` / `[s3]` / `[all]` install extras?

## Provider parity
- If the feature is added to one provider, is it feasible for the other? The abstraction is designed to keep S3 and GCS consistent — flag any intentional divergence.

## Documentation
- What docs/examples would need to be added/updated?

## Additional context
Links to related issues, provider SDK docs, or references.
