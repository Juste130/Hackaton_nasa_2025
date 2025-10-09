import dspy
import os

llm = dspy.LM(
    "openai/mistral-small-latest",
    api_key=os.environ.get("MISTRAL_API_KEY"),
    api_base="https://api.mistral.ai/v1",
    max_tokens=20000
)

# Test it
print(llm("Hello, world!"))