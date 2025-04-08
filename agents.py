# agents.py
import os
from dotenv import load_dotenv
from openai import OpenAI
import autogen
from autogen import AssistantAgent, UserProxyAgent

load_dotenv()

# Get API key and do a simple test first to verify it works
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(f"API Key (first 5 chars): {OPENAI_API_KEY[:5]}...")


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
def run_autogen_agents(intent, user_text, parameters, sentiment):
    # First test direct connection
    if not test_openai_connection():
        return "Failed to connect to OpenAI API. Please check your API key and network connection."

    # Configure AutoGen
    llm_config = configure_autogen()

    # Create a simple user proxy agent (no code execution)
    user_proxy = UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        code_execution_config=False,
        max_consecutive_auto_reply=0,
    )

    # Create specialized assistant agents
    loan_status_agent = AssistantAgent(
        name="LoanStatusAgent",
        llm_config=llm_config,
        system_message="""You are a virtual loan officer. You check loan status and provide information 
        about loan approvals. For the demo, the user has a pending home loan application submitted 3 days ago
        which is still under review. Respond naturally as if you are speaking to the customer."""
    )

    balance_enquiry_agent = AssistantAgent(
        name="BalanceEnquiryAgent",
        llm_config=llm_config,
        system_message="""You are a helpful bank assistant for balance inquiries.
        For this demo, the user has a checking account with $2,543.78 and a savings account with $15,689.22.
        Respond naturally as if you are speaking to the customer."""
    )

    loan_balance_agent = AssistantAgent(
        name="LoanBalanceAgent",
        llm_config=llm_config,
        system_message="""You help customers check their loan balances.
        For this demo, the user has a car loan with a remaining balance of $12,450.67 with 36 payments left.
        Respond naturally as if you are speaking to the customer."""
    )

    # Map intents to agents
    agent_map = {
        "loan_status": loan_status_agent,
        "balance_enquiry": balance_enquiry_agent,
        "loan_balance": loan_balance_agent
    }

    # Select agent based on intent
    selected_agent = agent_map.get(intent)
    if not selected_agent:
        return "Sorry, I couldn't route your request to a suitable agent."

    try:
        # Initiate chat with selected agent
        print(f"Initiating chat with {selected_agent.name}")
        user_proxy.initiate_chat(
            selected_agent,
            message=user_text.strip()
        )
        response = selected_agent.last_message()["content"]
        print(f"Got response: {response[:30]}...")
        return response
    except Exception as e:
        print(f"Error during chat: {str(e)}")
        return f"There was an error processing your request: {str(e)}"