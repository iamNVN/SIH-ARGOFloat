import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    try:
        client = Anthropic()
        # Try a minimal call: list models (or a simple message if list is not available)
        # Here, we use the messages.create endpoint with a dummy message
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=5,
            temperature=0,
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print("Anthropic API key is valid. Response:")
        print(response)
    except Exception as e:
        print("Anthropic API key test failed:")
        print(e)
