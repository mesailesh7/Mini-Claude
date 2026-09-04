from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
        {"role": "user", "content": "Explain what an AI agent is in one sentence."},
        {
            "role": "assistant",
            "content": "An AI agent is simply an llm connected to tools in a loop",
        },
        # {"role": "system", "content": "Explain what an AI agent is in one sentence"},
    ],
)

print(response.choices[0].message.content)
