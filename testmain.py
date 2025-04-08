
# testmain.py
from agents import run_autogen_agents

test_cases = [
    {"intent": "loan_balance", "user_text": "How much do I still owe on my car loan?", "parameters": {}, "sentiment": "neutral"},
    {"intent": "balance_enquiry", "user_text": "What's in my checking account right now?", "parameters": {}, "sentiment": "neutral"},
    {"intent": "loan_status", "user_text": "Is my home loan approved yet?", "parameters": {}, "sentiment": "neutral"},
    {"intent": "unsupported_intent", "user_text": "Tell me a joke.", "parameters": {}, "sentiment": "neutral"}
]

for i, test in enumerate(test_cases, start=1):
    print(f"\n🔍 Test {i}: {test['intent'].replace('_', ' ').title()}")
    print("📤 Message:", test["user_text"])
    response = run_autogen_agents(
        test["intent"], test["user_text"], test["parameters"], test["sentiment"]
    )
    print("📣 Response:", response)