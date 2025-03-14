from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.tools import tool, Tool, BaseTool
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END
from typing import Type
from pydantic import BaseModel, Field
# from langchain.tools import BaseTool
import yfinance as yf


llm = ChatOpenAI(
    openai_api_key="EMPTY",  # 替换为你的 OpenAI API 密钥
    base_url="http://10.141.5.108:8888/v1",
    model_name="qwen25",  # 默认模型，可改为 "gpt-4"
    temperature=0.2,  # 控制创造性（0-1，越大回答越随机）
)

def get_current_stock_price(ticker):
    """Method to get current stock price"""
 
    ticker_data = yf.Ticker(ticker)
    recent = ticker_data.history(period="1d")
    return {"price": recent.iloc[0]["Close"], "currency": ticker_data.info["currency"]}

class CurrentStockPriceInput(BaseModel):
    """Inputs for get_current_stock_price"""

    ticker: str = Field(description="Ticker symbol of the stock")

class CurrentStockPriceTool(BaseTool):
    name : str = "get_current_stock_price"
    description : str = """Useful when you want to get current stock price.You should enter the stock ticker symbol recognized by the yahoo finance"""
    args_schema: Type[BaseModel] = CurrentStockPriceInput
 
    def _run(self, ticker: str):
        price_response = get_current_stock_price(ticker)
        return price_response
 
    def _arun(self, ticker: str):
        raise NotImplementedError("get_current_stock_price does not support async")

tools = [CurrentStockPriceTool()]

llm_with_tools = llm.bind_tools(tools)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


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
    # graph_builder.set_finish_point("chatbot")
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_conditional_edges(
        "chatbot", route_tools
        #tools_condition
    )

    graph = graph_builder.compile()

    try:
        graph.get_graph().draw_mermaid_png(output_file_path="graph_with_tools.png")
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

"""
 "What is the current price of Microsoft stock?"
"""