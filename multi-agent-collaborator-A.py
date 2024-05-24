import getpass
import json
import os
from dotenv import load_dotenv
from langchain_core.messages import (
    BaseMessage,
    ToolMessage,
    HumanMessage,
    AIMessage
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, StateGraph

from langchain_core.tools import tool
from typing import Annotated
from langchain_experimental.utilities import PythonREPL
from langchain_community.tools.tavily_search import TavilySearchResults

import operator
from typing import Annotated, Sequence, TypedDict

from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict

import functools
from langgraph.prebuilt import ToolNode

# Either agent can decide to end
from typing import Literal
import matplotlib.pyplot as plt
from pandas import DataFrame

load_dotenv()
def router(state) -> Literal["call_tool", "__end__", "continue"]:
    # This is the router
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        # The previous agent is invoking a tool
        return "call_tool"
    if "FINAL ANSWER" in last_message.content:
        # Any agent decided the work is done
        return "__end__"
    return "continue"


# Helper function to create a node for a given agent
def agent_node(state, agent, name):
    result = agent.invoke(state)
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        pass
    else:
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }


# This defines the object that is passed between each node
# in the graph. We will create different nodes for each agent and tool
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str


tavily_tool = TavilySearchResults(max_results=5)

# Warning: This executes code locally, which can be unsafe when not sandboxed

python_repl = PythonREPL()


@tool
def python_repl(
    code: Annotated[str, "The python code to execute to generate your chart."]
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user.
    If you have to install using pip any dependency like pandas, do it before executing the code"""
    try:
        result = python_repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"
    return (result_str
        #result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."
    )


def create_agent(llm, tools, system_message: str):
    """Create an agent."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " If you or any of the other assistants have the final answer or deliverable,"
                " prefix your response with FINAL ANSWER so the team knows to stop."
                " You have access to the following tools: {tool_names}.\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    return prompt | llm.bind_tools(tools)


def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")


def main():
    print("main...")
    _set_if_undefined("OPENAI_API_KEY")
    _set_if_undefined("LANGCHAIN_API_KEY")
    _set_if_undefined("TAVILY_API_KEY")

    # Optional, add tracing in LangSmith
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "Multi-agent Collaboration"

    llm = ChatOpenAI(model="gpt-4-1106-preview")

    # Research agent and node
    research_agent = create_agent(
        llm,
        [tavily_tool],
        system_message="You should provide accurate data for the chart_generator to use.",
    )
    research_node = functools.partial(
        agent_node, agent=research_agent, name="Researcher"
    )

    # chart_generator
    chart_agent = create_agent(
        llm,
        [python_repl],
        system_message="Any charts you display will be visible by the user.",
    )
    chart_node = functools.partial(
        agent_node, agent=chart_agent, name="chart_generator"
    )
    tools = [tavily_tool, python_repl]
    tool_node = ToolNode(tools)

    workflow = StateGraph(AgentState)

    workflow.add_node("Researcher", research_node)
    workflow.add_node("chart_generator", chart_node)
    workflow.add_node("call_tool", tool_node)

    workflow.add_conditional_edges(
        "Researcher",
        router,
        {"continue": "chart_generator", "call_tool": "call_tool", "__end__": END},
    )
    workflow.add_conditional_edges(
        "chart_generator",
        router,
        {"continue": "Researcher", "call_tool": "call_tool", "__end__": END},
    )

    workflow.add_conditional_edges(
        "call_tool",
        # Each agent node updates the 'sender' field
        # the tool calling node does not, meaning
        # this edge will route back to the original agent
        # who invoked the tool
        lambda x: x["sender"],
        {
            "Researcher": "Researcher",
            "chart_generator": "chart_generator",
        },
    )
    workflow.set_entry_point("Researcher")
    graph = workflow.compile()
    content_human_message = "Obtenga el PIB de España de los últimos 5 años y luego muestre los datos utilizando un dataframe. Una vez lo codifiques, termina."
    print(f"content_human_message is {content_human_message}")
    events = graph.stream(
        {
            "messages": [
                HumanMessage(
                    content=content_human_message
                )
            ],
        },
        # Maximum number of steps to take in the graph
        {"recursion_limit": 150},
    )
    print(f"these are the events: ")
    for s in events:
        print(f"type(s): {type(s)}")
        s = {key: convert_messages(value) for key, value in s.items()}
        s = {key: json.loads(json.dumps(value, default=message_to_dict)) for key, value in s.items()}  # Usar json.dumps para serializar
        print(json.dumps(s, indent=4, ensure_ascii=False))  # Usar json.dumps para serializar
        print("----")
        print("\n")

def message_to_dict(message):
    print(f"Message type: {type(message)}")
    if isinstance(message, (BaseMessage, AIMessage, HumanMessage, ToolMessage)):
        return message.dict()
    return message

def convert_messages(messages):
    print(f"Messages type: {type(messages)}")
    if isinstance(messages, list):
        return [message_to_dict(msg) for msg in messages]
    return messages

if __name__ == "__main__":
    main()
    print("Sample complete.")
