from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from services.agent.agent_runner import agent
from services.api_gateway.models import ChatRequest
from services.deductions.deductions_service import deductions_service
from pydantic import BaseModel

app = FastAPI(title="Tax Assistant API", description="A FastAPI application for a tax assistant")

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
    thread_id = body.get("thread_id", "default")
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Build messages list
    messages = [{"role": "user", "content": user_input}]
    
    # Use the streaming agent and collect the final response
    final_response = ""
    for step in agent.stream(
        {"messages": messages}, 
        config=config, 
        stream_mode="values"
    ):
        if "messages" in step and step["messages"]:
            last_message = step["messages"][-1]
            if hasattr(last_message, 'type') and last_message.type == 'ai':
                final_response = getattr(last_message, 'content', '')
            elif hasattr(last_message, 'content'):
                final_response = last_message.content
    
    return {"reply": final_response}


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


# Feature flag management endpoints

class FeatureFlagRequest(BaseModel):
    enabled: bool

@app.get("/api/features/deductions")
def get_deductions_feature_status():
    """Get the current status of the deductions feature."""
    return deductions_service.get_feature_status()

@app.post("/api/features/deductions")
def set_deductions_feature_status(request: FeatureFlagRequest):
    """Enable or disable the deductions feature at runtime."""
    new_status = deductions_service.set_feature_enabled(request.enabled)
    return {
        "enabled": new_status,
        "message": f"Deductions feature {'enabled' if new_status else 'disabled'}"
    }