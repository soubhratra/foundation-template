from django.conf import settings
from django.core.checks import Warning, register


@register()
def check_api_key_scopes(app_configs, **kwargs) -> list:
    errors = []
    scopes = getattr(settings, "API_KEY_SCOPES", None)

    if scopes is None:
        errors.append(
            Warning(
                "API_KEY_SCOPES setting is not defined. API key creation will fail at runtime.",
                id="api_keys.W001",
            )
        )
        return errors

    if not isinstance(scopes, dict):
        errors.append(
            Warning(
                "API_KEY_SCOPES must be a dict mapping scope name to config dict.",
                id="api_keys.W002",
            )
        )
        return errors

    for scope_name, config in scopes.items():
        if not isinstance(config, dict) or "description" not in config:
            errors.append(
                Warning(
                    f"API_KEY_SCOPES['{scope_name}'] must be a dict with a 'description' key.",
                    hint=f"Got: {config!r}",
                    id="api_keys.W003",
                )
            )

    return errors
