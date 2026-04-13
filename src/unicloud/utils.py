"""Small helpers for moving credential payloads through environment variables.

Google Cloud service-account JSON files do not round-trip cleanly through most shells or CI secret
stores, so unicloud ships :func:`encode` and :func:`decode` — a complementary base64 pair that lets
you stash the full JSON inside a single environment variable (commonly ``SERVICE_KEY_CONTENT``, which
:class:`unicloud.google_cloud.gcs.GCS` reads out of ``os.environ``) and decode it back into a dict
at runtime.
"""

import base64
import json
import os.path
from typing import Any, Dict, Union


def encode(secret_file: Union[str, Any]) -> bytes:
    """Encode a service-account payload to a base64 bytestring.

    Accepts three equivalent inputs so you can produce the encoded value from whatever form of the
    service-account JSON you have handy: a file path on disk, an in-memory ``dict``, or a JSON string.

    Args:
        secret_file: One of:

            - a string path to a service-account JSON file on disk,
            - a ``dict`` that already contains the parsed service-account content, or
            - a JSON string containing the same content.

    Returns:
        bytes: The base64-encoded JSON, suitable for storing in an environment variable.

    Examples:
        - Encode an in-memory dict directly:
            ```python
            >>> secret_file_content = {"type": "service_account", "project_id": "your_project_id"}
            >>> encode(secret_file_content)
            b'eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogInlvdXJfcHJvamVjdF9pZCJ9'

            ```
        - Encode from a JSON string with the same content:
            ```python
            >>> secret_file_json = '{"type": "service_account", "project_id": "your_project_id"}'
            >>> encode(secret_file_json)  # doctest: +SKIP
            b'eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogImV4YW1wbGUtcHJvamVjdF9pZCJ9'

            ```
        - Encode from a file path on disk:
            ```python
            >>> encode("examples/data/secret-file.json")  # doctest: +SKIP
            b'eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogImV4YW1wbGUtcHJvamVjdC1pZCIs******'

            ```

    See Also:
        decode: Inverse operation that turns the base64 payload back into a ``dict``.
    """
    if isinstance(secret_file, str) and os.path.exists(secret_file):
        content: dict = json.load(open(secret_file))
    elif isinstance(secret_file, dict):
        # Direct dictionary input
        content: dict = secret_file
    else:
        # a JSON string representing the content
        content: dict = json.loads(secret_file)

    # serialize first
    dumped_service_account = json.dumps(content)
    encoded_service_account = base64.b64encode(dumped_service_account.encode())
    return encoded_service_account


def decode(string: bytes) -> Dict[str, str]:
    """Decode a base64 bytestring back into a service-account ``dict``.

    This is the inverse of :func:`encode` — given the bytes that :func:`encode` produced (or the
    same bytes pulled out of ``os.environ["SERVICE_KEY_CONTENT"]``), return the parsed JSON as a
    plain dictionary.

    Args:
        string: The base64-encoded JSON payload, typically read from an environment variable.

    Returns:
        Dict[str, str]: The decoded service-account content.

    Examples:
        - Round-trip a base64 payload back into a dict:
            ```python
            >>> encoded_content = b'eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogImV4YW1wbGUtcHJvamVjdF9pZCJ9'
            >>> decode(encoded_content)
            {'type': 'service_account', 'project_id': 'example-project_id'}

            ```

    See Also:
        encode: Produces the base64 bytestring that this function decodes.
    """
    service_key = json.loads(base64.b64decode(string).decode())
    return service_key
