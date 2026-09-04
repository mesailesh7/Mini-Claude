import json
import os
import subprocess

from openai import OpenAI

client = OpenAI(api_key="")

MODEL = "gpt-5-mini"

SYSTEM_PROMPT = """
You are a coding agent running in the user's terminal.
You can list files, read files, write files, and run shell commands.
Use your tools to complete the user's task, then briefly summarize what you did.
The working directory is the folder the user launched you from.
"""


def list_files(path="."):
    entries = []
    for entry in os.scandir(path):
        entries.append(entry.name + ("/" if entry.is_dir() else ""))
    return "\n".join(sorted(entries)) or "(empty directory)"


def read_files(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path,"w", encoding="utf-8") as f:
        f.write(content)
    return f"Saved {path} ({len(content)} characters)"

def run_command(command):
    answer = input(f"Run '{command}' command? (y/n): ")
    if answer.strip().lower() != "y":
        return "The user declined to run this command"
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
    output = (result.stdout + result.stderr).strip()
    return output or f"(No output, exit code {result.returncode})"

TOOLS={
    "list_files": list_files,
    "read_files": read_files,
    "write_file": write_file,
    "run_command": run_command,
}

TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List the files and directories in a given path. Directory names end with a trailing '/'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to list. Defaults to '.' (current directory).",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_files",
            "description": "Read and return the entire text content of a specified file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file that should be read.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a specified file, overwriting it if it already exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file to write to.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The complete text content to write into the file.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command in the terminal after obtaining user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute.",
                    }
                },
                "required": ["command"],
            },
        },
    },
]

def run_tool(tool_call):
    name = tool_call.funtion.name
    args = json.loads(tool_call.function.arguments)
    print(f" Tool: {name}({args})")

    try:
        return str(TOOLS[name](**args))
    except Exception as error:
        return f"Error: {error}"



def run_agent(messages):
    while True:
        response = client.chat.completions.create(
            model = MODEL,
            messages = messages,
            tools = TOOL_SCHEMA
        )
        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            return message.content

        for tool_call in message.tool_calls:
            result = run_tool(tool_call)
            message.append({
                "role":"tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

def main():
    messages = [{"role":"system", "content":SYSTEM_PROMPT}]
    print("Minni agent ready. Type 'exit' for quit.")

    while True:
        user_input = input("\nYou:")
        if user_input.strip().lower() in ("exit","quit"):
            break
        messages.append({"role":"user", "content":user_input})
        reply = run_agent(messages)
        print(f"\nAgent: {reply}")

if __name__ == "__main__":
    main()