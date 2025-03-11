import json
from typing import Annotated

from dotenv import load_dotenv
from langchain_community.tools import TavilySearchResults
from langchain_core.messages import ToolMessage
# from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

# 加载.env文件，获取密钥
load_dotenv(verbose=True)
# 定义工具
def get_current_temperature(location: str, unit: str = "celsius"):
    """Get current temperature at a location.

    Args:
        location: The location to get the temperature for, in the format "City, State, Country".
        unit: The unit to return the temperature in. Defaults to "celsius". (choices: ["celsius", "fahrenheit"])

    Returns:
        the temperature, the location, and the unit in a dict
    """
    return {
        "temperature": 26.1,
        "location": location,
        "unit": unit,
    }


def get_temperature_date(location: str, date: str, unit: str = "celsius"):
    """Get temperature at a location and date.

    Args:
        location: The location to get the temperature for, in the format "City, State, Country".
        date: The date to get the temperature for, in the format "Year-Month-Day".
        unit: The unit to return the temperature in. Defaults to "celsius". (choices: ["celsius", "fahrenheit"])

    Returns:
        the temperature, the location, the date and the unit in a dict
    """
    return {
        "temperature": 25.9,
        "location": location,
        "date": date,
        "unit": unit,
    }
tool = TavilySearchResults(max_results=2)
print(f"tools : {tool}")

# tools = [tool, "get_current_temperature", "get_temperature_date"]

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_temperature",
            "description": "Get current temperature at a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": 'The location to get the temperature for, in the format "City, State, Country".',
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": 'The unit to return the temperature in. Defaults to "celsius".',
                    },
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_temperature_date",
            "description": "Get temperature at a location and date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": 'The location to get the temperature for, in the format "City, State, Country".',
                    },
                    "date": {
                        "type": "string",
                        "description": 'The date to get the temperature for, in the format "Year-Month-Day".',
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": 'The unit to return the temperature in. Defaults to "celsius".',
                    },
                },
                "required": ["location", "date"],
            },
        },
    },
]


class BasicToolNode:
    """
    处理输入消息中的每个工具调用请求，通过查找对应的工具对象并执行它们
    然后将结果封装成新的 ToolMessage 对象并返回
    """

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}
        print(f"tools_by_name : {self.tools_by_name }")

    def __call__(self, inputs: dict):
        # 尝试从 inputs 字典中获取 messages 键对应的值
        # 如果存在，它将被赋值给变量 messages
        # 如果不存在，messages 将默认为一个空列表
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        print("Tool Node \n\n")
        print(f"msg tools : {message.tool_calls}\n\n")
        outputs = []
        for tool_call in message.tool_calls:
            # 使用 tool_call 中的 name 作为键，从 tools_by_name 字典中获取对应的工具对象
            # 并调用它的 invoke 方法，传递 tool_call 中的 args 作为参数，执行工具并获取结果
            print(f"Called here 135 \n")
            # tool_result = self.tools_by_name[tool_call["name"]].invoke(
                # tool_call["args"]
            # )
            tool_result = get_current_temperature(tool_call["args"])
            print(f"tool_result : {tool_result}")
            # 将工具调用的结果封装成一个新的 ToolMessage 对象，并添加到 outputs 列表中
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        print(f"Called here\n")
        return {"messages": outputs}


def route_tools(state: State,):
    """
    在图构建器中添加条件边和普通边
    以控制消息处理流程中的路由逻辑
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    print(f"Rout tools info : \nAi msg : {ai_message}")
    # 检查 ai_message 是否包含 tool_calls 属性
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        print(f"return tools \n")
        return "tools"
    print(f"return None tools \n")
    return END


# 初始化 ChatOllama 对象
llm = ChatOpenAI(
    openai_api_key="EMPTY",  # 替换为你的 OpenAI API 密钥
    base_url="http://10.141.5.108:8888/v1",
    model_name="qwen25",  # 默认模型，可改为 "gpt-4"
    temperature=0.2,  # 控制创造性（0-1，越大回答越随机）
)


llm_with_tools = llm.bind_tools(tools)
# llm = ChatOllama(model="gemma2:2b")


class State(TypedDict):
    """
    定义一个字典类型 State（继承自 TypeDict）
    包含一个键 messages
    值是一个 list，并且列表的更新方式由 add_messages 函数定义
    add_message 将新消息追加到列表中，而不是覆盖原有列表
    """
    messages: Annotated[list, add_messages]


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [("user", user_input)]}):
        for value in event.values():
            # 访问最后一个消息的内容，并将其打印出来
            print("Assistant:", value["messages"][-1].content)
            print("Test:", value)


if __name__ == '__main__':
    # 1. 创建一个 StateGraph 对象
    graph_builder = StateGraph(State)

    # 2. 添加 node
    graph_builder.add_node("chatbot", chatbot)
    tool_node = BasicToolNode(tools=[tool])
    graph_builder.add_node("tools", tool_node)
    # 2.1 添加条件边
    graph_builder.add_conditional_edges(
        "chatbot",
        route_tools,
    )
    # 2.2 添加普通边
    # tools 节点调用结束，会又回到 chatbot 节点
    graph_builder.add_edge("tools", "chatbot")

    # 3. 定义 StateGraph 的入口
    # graph_builder.add_edge(START, "chatbot")
    graph_builder.set_entry_point("chatbot")

    # 4. 定义 StateGraph 的出口
    # graph_builder.add_edge("chatbot", END)
    # graph_builder.set_finish_point("chatbot")

    # 5. 创建一个 CompiledGraph，以便后续调用
    graph = graph_builder.compile()

    # 6. 可视化 graph
    try:
        # graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
        graph.get_graph().draw_mermaid_png(output_file_path="graph_with_tools.png")
    except Exception:
        # This requires some extra dependencies and is optional
        pass

    # 7. 运行 graph
    # 通过输入"quit", "exit", "q"结束对话
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            stream_graph_updates(user_input)
        # 如果在 try 块中的代码执行时发生任何异常，将执行 except 块中的代码
        except:
            # 在异常情况下，这行代码将 user_input 变量设置为一个特定的问题
            user_input = "What do you know about LangGraph?"
            print("User: " + user_input)
            stream_graph_updates(user_input)
            break