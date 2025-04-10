# agents.py
import os
from dotenv import load_dotenv
from openai import OpenAI
import autogen
from autogen import AssistantAgent, UserProxyAgent
import requests

load_dotenv()

# Get API key and do a simple test first to verify it works
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(f"API Key (first 5 chars): {OPENAI_API_KEY[:5]}...")

# API Base URL (change if backend API runs elsewhere)
API_ROOT = "http://localhost:8085"

# Intent-to-config mapping
INTENT_CONFIG = {
    "loan_balance": {
        "api": f"{API_ROOT}/loan_balance",
        "prompt": """
        You are a helpful banking assistant. The user said: '{user_text}'.
        Based on the following account info: '{api_data}',
        respond conversationally and clearly, as if you're speaking to a customer.
        """,
        "required_params": ["account_number"]
    },
    "balance_enquiry": {
        "api": f"{API_ROOT}/balance_enquiry",
        "prompt": """
        You are a helpful banking assistant. The user asked: '{user_text}'.
        Here is what the system returned: '{api_data}'.
        Respond naturally and clearly.
        """,
        "required_params": ["account_number"]
    },
    "loan_status": {
        "api": f"{API_ROOT}/loan_status",
        "prompt": """
        You are a virtual loan officer. The user said: '{user_text}'.
        Here is the current loan status: '{api_data}'.
        Craft a natural and informative response.
        """,
        "required_params": ["loan_id"]
    },
    # Add more intents here
}


# Test direct OpenAI API connection first
def test_openai_connection():
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        print(f"OpenAI API Test: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"Error testing OpenAI API: {str(e)}")
        return False


# Configure AutoGen
def configure_autogen():
    config_list = [
        {
            "model": "gpt-3.5-turbo",  # Use 3.5 to start as it's more reliable for testing
            "api_key": OPENAI_API_KEY,
        }
    ]

    return {
        "config_list": config_list,
        "temperature": 0.5,
        "timeout": 120,
    }


# Main function to run agents
def run_autogen_agents(intent, user_text, parameters, sentiment, chat_history=None):
    # First test direct connection
    if not test_openai_connection():
        return "Failed to connect to OpenAI API. Please check your API key and network connection."

    config = INTENT_CONFIG.get(intent)
    if not config:
        return f"Unknown intent: '{intent}'. No agent configuration available."

    chat_history = chat_history or []

    # Check for required parameters
    required = config.get("required_params", [])
    missing = [param for param in required if not parameters.get(param)]

    if missing:
        # Ask user for missing parameters
        missing_str = ", ".join(missing)
        prompt = (
            f"The user said: '{user_text}'. "
            f"Please ask them to provide the following missing detail(s): {missing_str}."
        )

        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": prompt})

        context_prompt = "\n".join(
            [f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history]
        )

        llm_config = configure_autogen()
        user_proxy = UserProxyAgent(
            name="user",
            human_input_mode="NEVER",
            code_execution_config=False,
            max_consecutive_auto_reply=0,
        )
        assistant = AssistantAgent(
            name="VoiceAgent",
            llm_config=llm_config,
            system_message="You are a smart, friendly voice assistant for a bank."
        )

        try:
            print("🔎 Asking for missing parameters...")
            user_proxy.initiate_chat(assistant, message=context_prompt.strip())
            return assistant.last_message()["content"]
        except Exception as e:
            return f"Error prompting for missing parameters: {str(e)}"

    # Call external API (if configured)
    api_data = "No data found"
    api_url = config.get("api")

    if api_url:
        try:
            payload = {
                "user_text": user_text,
                "parameters": parameters or {},
                "sentiment": sentiment or ""
            }
            response = requests.post(api_url, json=payload, timeout=10)
            response.raise_for_status()
            api_data = response.json().get("response", "No 'response' key in API reply")
        except Exception as e:
            return f"API call failed for '{intent}': {str(e)}"

    # Prepare final prompt with user input + API output
    final_prompt = config["prompt"].format(user_text=user_text, api_data=api_data)

    # Configure AutoGen
    llm_config = configure_autogen()

    # Create a simple user proxy agent (no code execution)
    user_proxy = UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        code_execution_config=False,
        max_consecutive_auto_reply=0,
    )

    assistant = AssistantAgent(
        name="VoiceAgent",
        llm_config=llm_config,
        system_message="You are a smart, friendly voice assistant for a bank."
    )

    try:

        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": final_prompt})
        full_prompt = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history])

        # Initiate chat with selected agent
        print(f"Initiating chat with {assistant.name}")
        user_proxy.initiate_chat(
            assistant,
            message=full_prompt.strip()
        )
        response = assistant.last_message()["content"]
        print(f"Got response: {response[:30]}...")
        return response
    except Exception as e:
        print(f"Error during chat: {str(e)}")
        return f"There was an error processing your request: {str(e)}"