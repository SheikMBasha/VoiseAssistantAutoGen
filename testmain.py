from agents import run_autogen_agents

def extract_account_number(text):
    # Very simple mock extractor - replace with NLP or Dialogflow later
    for token in text.split():
        if token.isdigit() and len(token) >= 6:
            return token
    return None

if __name__ == "__main__":
    test_intent = "loan_balance"
    parameters = {}
    sentiment = "neutral"
    chat_history = []

    print("💬 You: How much do I still owe on my car loan?")
    user_text = "How much do I still owe on my car loan?"
    chat_history.append({"role": "user", "content": user_text})

    while True:
        response = run_autogen_agents(
            intent=test_intent,
            user_text=user_text,
            parameters=parameters,
            sentiment=sentiment,
            chat_history=chat_history
        )

        print("\n🤖 Assistant:", response)
        chat_history.append({"role": "assistant", "content": response})

        print("\n🤖 Assistant:", response)

        # Check if response was final (contains actual answer, not a request)
        if "please provide" not in response.lower():
            break

        # Simulate user providing requested info
        user_reply = input("\n💬 You: ")
        chat_history.append({"role": "user", "content": user_reply})

        extracted_account = extract_account_number(user_reply)
        if extracted_account:
            parameters["account_number"] = extracted_account
            user_text = chat_history[0]["content"]  # replay original question
        else:
            user_text = user_reply
