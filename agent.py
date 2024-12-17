import os
from langchain_core.tools import tool  # for convenience
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No OpenAI API key found. Please check your .env file.")

llm = ChatOpenAI(model="gpt-4o-mini",api_key=OPENAI_API_KEY)

@tool
def add(a: int, b: int) -> int:
    """Adds a and b."""
    print("reached add: ", a + b)
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b."""
    print("reached multiply")
    return a * b


tools = [add, multiply]

llm_with_tools = llm.bind_tools(tools)


def interactive_chat():
    print("🤖 AI Agent Chat Interface")
    print("Type 'exit' to end the conversation")

    messages = []

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        messages.append(HumanMessage(user_input))

        try:
            ai_msg = llm_with_tools.invoke(messages)

            for tool_call in ai_msg.tool_calls:
                selected_tool = {"add": add, "multiply": multiply}[
                    tool_call["name"].lower()]
                tool_msg = selected_tool.invoke(tool_call)
                messages.append(tool_msg)

            messages.append(ai_msg)

            print("\nAI:", ai_msg.content)

        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    interactive_chat()
