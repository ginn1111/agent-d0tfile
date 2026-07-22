from providers import register_provider
from providers.base import ProviderProfile

gin = ProviderProfile(
    name="gin-interface",
    aliases=("gin",),
    display_name="Gin Interface",
    description="Gin Interface — OpenAI-compatible direct API",
    signup_url="https://agents.gin1111.dev",
    env_vars=("GIN_API_KEY", "GIN_BASE_URL"),
    base_url="https://agents.gin1111.dev/v1",
    auth_type="api_key",
    default_aux_model="aux",
)

register_provider(gin)
