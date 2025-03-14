from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.tools import tool
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition

llm = ChatOpenAI(
    openai_api_key="EMPTY",  # 替换为你的 OpenAI API 密钥
    base_url="http://10.141.5.108:8888/v1",
    model_name="qwen25",  # 默认模型，可改为 "gpt-4"
    temperature=0.2,  # 控制创造性（0-1，越大回答越随机）
)

@tool
def divide(a: float, b: float) -> int:
    """Return a / b."""
    return a / b

tools = [divide]

llm_with_tools = llm.bind_tools(tools)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

if __name__ == '__main__':
    # 1. 创建一个 StateGraph 对象
    graph_builder = StateGraph(State)
    graph_builder.add_node("tools", ToolNode(tools))
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.set_entry_point("chatbot")
    graph_builder.set_finish_point("chatbot")
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_conditional_edges(
        "chatbot", tools_condition
    )

    graph = graph_builder.compile()

    try:
        graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
    except Exception:
        # This requires some extra dependencies and is optional
        pass

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            stream_graph_updates(user_input)
        except:
            # fallback if input() is not available
            user_input = "What do you know about LangGraph?"
            print("User: " + user_input)
            stream_graph_updates(user_input)
            break