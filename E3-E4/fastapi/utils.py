import os

MISSING_OPENAI_KEY_MSG = "OPENAI_API_KEY environment variable is missing"

def get_openai_api_key() -> str:
    """Return the OpenAI API key from the environment.

    Raises:
        EnvironmentError: if the OPENAI_API_KEY variable is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(MISSING_OPENAI_KEY_MSG)
    return api_key
