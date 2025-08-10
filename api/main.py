from fastapi import FastAPI, Request
from agent.agent_runner import agent

app = FastAPI()

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_input = body["message"]
    response = agent.run(user_input)
    return {"reply": response}
