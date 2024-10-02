import instructor
from openai import OpenAI
from anthropic import Anthropic

def create_openai_client(api_key: str):
    return instructor.from_openai(OpenAI(api_key=api_key))

def create_anthropic_client(api_key: str):
    return instructor.from_anthropic(Anthropic(api_key=api_key))

INSTRUCTOR_CLIENT_MAP = {
    "gpt-4o-mini": create_openai_client,
    "gpt-4o": create_openai_client,
    "claude-3-haiku-20240307": create_anthropic_client,
}
