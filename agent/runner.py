import json
import os
import requests

from dotenv import load_dotenv
from pathlib import Path

from agent.prompts import load_agent_instructions
from agent.tools import get_city_conditions


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openrouter/free"

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# --------------------------------------------------
# Tool definitions
# --------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_city_conditions",
            "description": (
                "Fetch current air quality and weather conditions "
                "for any city. Use this whenever reliable city-specific "
                "environmental data is needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city_name": {
                        "type": "string",
                        "description": "Name of the city to look up."
                    }
                },
                "required": ["city_name"],
                "additionalProperties": False
            }
        }
    }
]


# --------------------------------------------------
# Tool execution
# --------------------------------------------------

def execute_tool(tool_name, arguments):

    if tool_name == "get_city_conditions":
        return get_city_conditions(**arguments)

    return {"error": f"Unknown tool: {tool_name}"}


# --------------------------------------------------
# AI Agent
# --------------------------------------------------

def run_agent(user_message, chat_history=None, dashboard_context=None):

    if not API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY is missing from your .env file."
        )

    if chat_history is None:
        chat_history = []

    # Load BreatheWise personality and instructions
    instructions = load_agent_instructions()

    system_prompt = instructions

    # Give the AI awareness of the currently selected dashboard city
    if dashboard_context:
        system_prompt += (
            "\n\nCURRENT DASHBOARD CONTEXT:\n"
            + json.dumps(dashboard_context, ensure_ascii=False)
            + "\nUse this information when relevant. "
            "Fetch additional city data when needed."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        *chat_history,
        {"role": "user", "content": user_message}
    ]

    # Allow the AI to reason and call tools in multiple steps
    max_iterations = 5

    for _ in range(max_iterations):

        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": messages,
                "tools": TOOLS,
                "tool_choice": "auto"
            },
            timeout=60
        )

        response.raise_for_status()

        result = response.json()
        assistant_message = result["choices"][0]["message"]

        tool_calls = assistant_message.get("tool_calls")

        # No more tools needed: AI has its final answer
        if not tool_calls:

            answer = assistant_message.get("content") or ""

            updated_history = chat_history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": answer}
            ]

            return answer, updated_history

        # Preserve the assistant's tool-call message
        messages.append(assistant_message)

        # Execute every tool requested by the AI
        for tool_call in tool_calls:

            tool_name = tool_call["function"]["name"]
            tool_call_id = tool_call["id"]

            try:
                arguments = json.loads(
                    tool_call["function"]["arguments"]
                )

                tool_result = execute_tool(tool_name, arguments)

            except Exception as error:
                tool_result = {"error": str(error)}

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps(
                    tool_result,
                    ensure_ascii=False,
                    default=str
                )
            })

    raise RuntimeError(
        "The AI reached its maximum tool-call iterations."
    )