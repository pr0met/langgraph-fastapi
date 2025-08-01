import os
from typing import TypedDict, Annotated

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver

from tools import get_content_types, get_content_type_templates, get_template_details, create_content

# --- LangGraph Setup ---

# 1. Define the state for the graph
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 2. Define the tools
tools = [get_content_types, get_content_type_templates, get_template_details, create_content]

# 3. Define the model and bind tools
llm = init_chat_model("google_genai:gemini-2.5-flash")
llm_with_tools = llm.bind_tools(tools)


# 4. Define the functions used in the graph nodes
async def chatbot(state: State) -> dict:
    """
    A node that streams the response from the LLM.
    """
    # Use astream to get a stream of chunks
    stream = llm_with_tools.astream(state["messages"])
    # Yield each chunk as it comes in
    async for chunk in stream:
        yield {"messages": [chunk]}


# 5. Define the conditional edge to decide if we need to call tools
def should_call_tools(state: State) -> str:
    """Return the next node to call."""
    last_message = state["messages"][-1]
    # The LLM decides to make a tool call: route to the tools node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, we're done
    return END


# 6. Build the graph
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=tools))

graph_builder.set_entry_point("chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    should_call_tools,
)
graph_builder.add_edge("tools", "chatbot")

# The checkpointer is important for persisting conversation state across requests
memory = InMemorySaver()
# The `compile()` method creates the runnable graph
graph = graph_builder.compile(checkpointer=memory)
