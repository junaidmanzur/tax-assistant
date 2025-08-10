from fastapi import FastAPI, Request
from agent.agent_runner import agent
from api.models import ChatRequest

app = FastAPI(title="Tax Agent API", description="A FastAPI application for a tax agent")

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_input = body["message"]
    response = agent.run(user_input)
    return {"reply": response}


# --- Streaming (SSE) optional ---
# pip install sse-starlette
from sse_starlette.sse import EventSourceResponse

@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """
    Streams tokens / steps as Server-Sent Events (EventSource).
    Frontends can consume with EventSource in the browser.
    """
    config = req.config or {}
    config.setdefault("configurable", {})["thread_id"] = req.thread_id

    def event_gen():
        try:
            for step in agent.stream(
                {"messages": [m.model_dump() for m in req.messages]},
                config=config,
                stream_mode="values",
            ):
                # You can shape the payload as you like
                yield {"event": "step", "data": step}
            yield {"event": "done", "data": "true"}
        except Exception as e:
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_gen())