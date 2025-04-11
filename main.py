from fastapi import FastAPI, Request
from pydantic import BaseModel
from agents import run_autogen_agents
from fastapi.responses import JSONResponse

app = FastAPI()

class DialogflowRequest(BaseModel):
    intent: str
    user_text: str
    parameters: dict
    sentiment: str = ""
    chat_history: list = []

# In-memory session store (use Redis or DB in production)
session_memory = {}

# 🔁 Map webhook tag to intent
TAG_TO_INTENT = {
    "WaveAPITag": "balance_enquiry"
}

@app.post("/dialogflow-hook")
async def dialogflow_webhook(request: Request):
    body = await request.json()

    print("📩 Full request body:")
    import json
    print(json.dumps(body, indent=2))

    # Extract session ID, user input, and parameters
    session_id = body.get("sessionInfo", {}).get("session", "default")
    user_text = body.get("text", "")
    parameters = body.get("sessionInfo", {}).get("parameters", {})
    tag = body.get("fulfillmentInfo", {}).get("tag", "")
    chat_history = session_memory.get(session_id, [])

    # Map tag to intent (fallback to default)
    tag = body.get("fulfillmentInfo", {}).get("tag", "").strip()

    intent = TAG_TO_INTENT.get(tag, "fallback")
    #intent = tag or "loan_balance"

    print("intent***", intent)
    if intent == "fallback":
        print(f"⚠️ Unknown webhook tag received: '{tag}'")

    # Call the agent logic
    result = run_autogen_agents(
        intent=intent,
        user_text=user_text,
        parameters=parameters,
        sentiment="neutral",
        chat_history=chat_history
    )

    # Save updated chat history
    chat_history.append({"role": "user", "content": user_text})
    chat_history.append({"role": "assistant", "content": result})
    session_memory[session_id] = chat_history

    print("✅ Returning to Dialogflow:", result)

    # Send response to Dialogflow CX
    return {
        "fulfillment_response": {
            "messages": [
                {
                    "text": {
                        "text": [result]
                    }
                }
            ]
        }
    }


@app.post("/dialogflow-hookold")
def handle_dialogflow(request: DialogflowRequest):
    response = run_autogen_agents(
        intent=request.intent,
        user_text=request.user_text,
        parameters=request.parameters,
        sentiment=request.sentiment,
        chat_history=request.chat_history
    )
    return {"fulfillmentText": response}


@app.post("/webhook")  # working endpoint
async def webhook(request: Request):
    req = await request.json()
    print(f"Request is {req}")



    # Extract relevant info
    session_id = req.get('session', 'default')
    user_text = req.get('queryResult', {}).get('queryText', '')
    intent = req.get('queryResult', {}).get('intent', {}).get('displayName', 'unknown')
    parameters = req.get('queryResult', {}).get('parameters', {})
    chat_history = session_memory.get(session_id, [])
    # parameters = {}

    # 👇 Normalize Dialogflow follow-up intent names
    base_intent = intent.split(" - ")[0] if " - " in intent else intent

    print(f"user_text is: {user_text}")
    print(f"Intent is: {intent}")
    print(f"BaseIntent is: {base_intent}")
    print(f"🧾 Dialogflow Parameters: {parameters}")
    # print(f"🧾 Required: {required}, Missing: {missing}")

    # Run agent logic
    result = run_autogen_agents(
        intent=base_intent,
        user_text=user_text,
        parameters=parameters,
        sentiment="neutral",
        chat_history=chat_history
    )

    # Update chat memory
    chat_history.append({"role": "user", "content": user_text})
    chat_history.append({"role": "assistant", "content": result})
    session_memory[session_id] = chat_history

    print(f'Result in main.py before sending to DF is {result}')
    # Respond to Dialogflow
    # response = {
    #     "fulfillmentText": result,
    #     "fulfillmentMessages": [
    #         {
    #             "text": {
    #                 "text": [result]
    #             }
    #         },
    #         {
    #             "platform": "AUDIO",
    #             "ssml": f"<speak>{result}</speak>"
    #         }
    #     ]
    # }

    response = {
        "fulfillmentText": result,
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [result]
                }
            },
            {
                "platform": "TELEPHONY",
                "telephonySynthesizeSpeech": {
                    "ssml": f"<speak>{result}</speak>"
                }
            }
        ]
    }

    print(f"Response is {response}")
    print(f"✅ Returning final webhook response to Dialogflow {JSONResponse(content=response)}")
    return JSONResponse(content=response)