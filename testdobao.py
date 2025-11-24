import os
from openai import OpenAI
api_key=os.environ.get("ARK_API_KEY"),
print(api_key)
client = OpenAI(
    # Make sure the environment variable "ARK_API_KEY" has been set.
    api_key=os.environ.get("ARK_API_KEY"), 
    # The base URL for model invocation .
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    )
completion = client.chat.completions.create(
    # Replace with Model ID .
    model="doubao-seed-1-6-251015",
    messages=[
        {"role": "user", "content": "hello"}
    ]
)
print(completion.choices[0].message)