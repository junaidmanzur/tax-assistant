from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from agent.agent_runner import agent
from api.models import ChatRequest

app = FastAPI(title="Tax Agent API", description="A FastAPI application for a tax agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_input = body["message"]
    response = agent.run(user_input)
    return {"reply": response}


import json
from fastapi.responses import StreamingResponse

@app.post("/api/chat/stream")
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
                # Extract the last AI message content from the step
                ai_content = ""
                if "messages" in step and step["messages"]:
                    last_message = step["messages"][-1]
                    if hasattr(last_message, 'type') and last_message.type == 'ai':
                        ai_content = getattr(last_message, 'content', '')
                    elif hasattr(last_message, 'content'):
                        ai_content = last_message.content
                
                # Send properly formatted SSE with valid JSON
                data = json.dumps({"ai_content": ai_content})
                yield f"event: step\ndata: {data}\n\n"
                
            # Send done event with valid JSON
            done_data = json.dumps({"status": "completed"})
            yield f"event: done\ndata: {done_data}\n\n"
            
        except Exception as e:
            # Send error event with valid JSON
            error_data = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )