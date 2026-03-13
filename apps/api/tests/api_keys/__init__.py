# Module-level import causes immediate ImportError at collection time
# until apps.api_keys is implemented — this is the intended RED state.
from apps.api_keys.models import APIKey  # noqa: F401
