from __future__ import annotations
from typing import Any, Callable
from botocore.exceptions import ClientError, EndpointConnectionError

def mk_id(*parts: str) -> str:
    """Create a unique ID from a list of parts."""
    return ":".join([p for p in parts if p])

def safe_call(fn: Callable, *args: Any, **kwargs: Any) -> tuple[Any | None, str | None]:
    """
    Safely call a function, returning the result and any error message.
    """
    try:
        return fn(*args, **kwargs), None
    except (ClientError, EndpointConnectionError) as e:
        code = getattr(e, 'response', {}).get('Error', {}).get('Code', str(e))
        return None, code
    except Exception as e:
        return None, str(e)
