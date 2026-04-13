# Utils

Small helpers used across unicloud. The `encode` / `decode` pair is the recommended way to pass a GCS service-account JSON through an environment variable (for example `SERVICE_KEY_CONTENT` in CI), since the raw JSON contains characters that do not round-trip through most shells safely.

::: unicloud.utils
    options:
        show_root_heading: true
        show_source: true
        heading_level: 3
        members_order: source
