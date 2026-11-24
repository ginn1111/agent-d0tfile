"""gin1111 OpenAI-compatible model provider."""

from providers import register_provider
from providers.base import ProviderProfile

register_provider(
    ProviderProfile(
        name="gin1111",
        display_name="gin1111",
        description="Local OpenAI-compatible endpoint",
        api_mode="chat_completions",
        auth_type="api_key",
        env_vars=("GIN1111_API_KEY", "GIN1111_BASE_URL"),
        base_url="http://localhost:20128/v1",
        fallback_models=("builder",),
    )
)
