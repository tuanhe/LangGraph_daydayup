from typing import Annotated

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


tool = TavilySearchResults(max_results=2)
tools = [tool]

llm = ChatOpenAI(
    openai_api_key="EMPTY",  # 替换为你的 OpenAI API 密钥
    base_url="http://10.141.5.108:8888/v1",
    model_name="qwen25",  # 默认模型，可改为 "gpt-4"
    temperature=0.2,  # 控制创造性（0-1，越大回答越随机）
)

llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

tool_node = ToolNode(tools=[tool])

graph_builder.add_node("chatbot", chatbot)

graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges("chatbot",tools_condition,)
# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")
graph = graph_builder.compile()

try:
    mermaid_png_bytes = graph.get_graph().draw_mermaid_png()  # 👈 获取二进制数据
    # display(Image(graph.get_graph().draw_mermaid_png()))

    with open("state_graph.png", "wb") as f:  # ✅ wb模式写入二进制
        f.write(mermaid_png_bytes) 
    print("图表已保存至: state_graph.png")
except Exception:
    # This requires some extra dependencies and is optional
    print("Something wrong")
    pass

# """
def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


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
# """