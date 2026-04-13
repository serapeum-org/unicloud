# Abstract interface

The abstract base classes that define the unified storage contract. Both the AWS S3 and GCS implementations derive from these, so you can write code against the abstract types to stay provider-agnostic.

::: unicloud.abstract_class.CloudStorageFactory
    options:
        show_root_heading: true
        show_source: true
        heading_level: 3
        members_order: source


::: unicloud.abstract_class.AbstractBucket
    options:
        show_root_heading: true
        show_source: true
        heading_level: 3
        members_order: source
