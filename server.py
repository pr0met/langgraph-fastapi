import asyncio
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from graph import graph


app = FastAPI(
    title="LangGraph Streaming Server",
    description="An example of how to stream LangGraph responses with FastAPI.",
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_index():
    return FileResponse('static/index.html')


class UserRequest(BaseModel):
    """Request model for user input."""
    content: str
    thread_id: str | None = None  # used to resume a conversation


AGENT_PRE_PROMPT = """
    You are an agent specializing in content creation. A content belongs to a content type and is created using a specific template, which also belongs to the content type.
    Your goal is to create and save a content in the system given the user request.
    You need to identify which content type is most appropriate given the user request, and in this content type, which template is most appropriate. 
    You must list the content types and the templates and try to identify the most appropriate one given the user request. 
    If it's fairly obvious, don't ask for validation, however if there is some ambiguity, ask the user for confirmation.

    When a piece of text is needed as an input property:
    - if the user input contains sufficient information, generate it
    - otherwise, ask a question to the user so they can give more info about it
"""


@app.post("/stream")
async def stream_graph(request: UserRequest) -> StreamingResponse:
    """
    Streams the complete LangGraph output for a given user request.
    Each part of the output is sent as a Server-Sent Event (SSE).
    """
    # Each conversation needs a unique ID.
    # If the client doesn't provide one, we generate a new one.
    thread_id = request.thread_id or str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    async def event_stream():
        """The async generator that yields SSE events."""
        try:
            messages = [
                SystemMessage(content=AGENT_PRE_PROMPT),
                HumanMessage(content=request.content),
            ]
            async for event in graph.astream_events(
                {"messages": messages},
                config,
                version="v1",
            ):
                # We're looking for events that have new data from the chatbot
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if isinstance(chunk, BaseMessage):
                        # Stream the content of the message chunk
                        yield chunk.content

                await asyncio.sleep(0.01)
        except Exception as e:
            # Handle potential errors during the stream
            error_message = f"[ERROR] An error occurred: {str(e)}\n\n"
            yield error_message

    response = StreamingResponse(event_stream(), media_type="text/event-stream")
    response.headers["x-thread-id"] = thread_id
    return response

