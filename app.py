import streamlit as st
import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from reddit import get_relevant_subreddits, post_to_reddit

# Load environment variables (contains OPENAI_API_KEY)
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No OpenAI API key found. Please check your .env file.")

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)


@tool
def grab_subreddits(keywords: list[str]) -> list:
    """Finds subreddits based on keywords."""
    return get_relevant_subreddits(keywords, search_limit=10)


@tool
def post_to_subreddit(subreddit: str, title: str, content: str) -> str:
    """Posts to a subreddit."""
    result = post_to_reddit(subreddit, title, content)
    status = "success" if result else "failure"
    return {"status": status, "result": result}


tools = [grab_subreddits, post_to_subreddit]
llm_with_tools = llm.bind_tools(tools)


def init_session_state():
    """Initialize session state variables, if not already present."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "system_prompt" not in st.session_state:
        # Store system instructions hidden from the UI
        st.session_state["system_prompt"] = """
        You are a helpful AI assistant designed to assist users with their queries and connect them with relevant subreddit communities. Follow these steps:

User Query: Start by understanding the user's initial question or request.
Clarification: Engage in a conversation to clarify the user's intent until you can generate at least 2 distinct keywords related to their topic. These should encompass various facets of their request.
Keyword Extraction: Extract the keywords in an array format (e.g., ["travel", "credit cards", "adventure", "points"]).
Grab Relevant Subreddits: Call the grab_subreddits() function with the generated array of keywords to identify all relevant subreddit communities.
Confirmation to Post: Present the user with the list of potential subreddits and ask if they would like to post their query to one or more of them.
Post to Subreddit: If the user consents, proceed with posting the query to their chosen subreddit(s).
Example Conversation Flow:
User Query: "I want to know the best travel credit cards for earning points."
Clarification:
"Are you looking for cards with travel-specific rewards or general cashback?"
"Do you prioritize international travel perks like no foreign transaction fees?"
"Do you want advice for business travel or personal trips?"

Step 2. Once you determine the keywords, send them to the user for approval. If they say yes, move to Step 3.
MAKE SURE TO PASS THE EXRTRACTED KEYWORDS AS AN ARRAY LIKE ["travel", "credit cards", "rewards", "points"] to the grab_subreddits() function.
Step 3. Grab Subreddits: Call grab_subreddits(["travel", "credit cards", "rewards", "points", "cashback", "international travel", "foreign transaction fees", "business travel", "personal trips", "frequent flyer"]).
Based on the returned subreddits, choose the top 5 that you think are most relevant to the query based on their descriptions.
Confirmation to Post:
"I found these relevant subreddits: r/travel, r/creditcards, r/awardtravel. Would you like to post your question to one or more of these subreddits?"
Step 4. Before you post to the subreddit, brainstorm title and content for the post with the user.
Post to Subreddit: If the user agrees, post the query to the selected subreddit(s).
If the response from the function says like Post Submitted, then its a success! Let the user know.
        """


def convert_to_langchain_messages():
    langchain_msgs = [
        AIMessage(role="system", content=st.session_state["system_prompt"])
    ]

    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            langchain_msgs.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_msgs.append(AIMessage(content=msg["content"]))
        elif msg["role"] == "tool":
            langchain_msgs.append(
                HumanMessage(content=f"Output from subreddit tool:{msg['content']}"))

    return langchain_msgs


def add_message(role: str, content: str, tool_call_id: str = None):
    message_data = {"role": role, "content": content}
    if tool_call_id:
        message_data["tool_call_id"] = tool_call_id
    st.session_state["messages"].append(message_data)


def handle_tool_calls(ai_response):
    """Process tool calls, reformat outputs, and display only the final result."""
    final_response = ai_response

    if not ai_response.tool_calls:
        return final_response

    for tool_call in ai_response.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        # 1) Call the tool
        result = None
        if tool_name == "grab_subreddits":
            with st.spinner("Searching for relevant subreddits..."):
                result = grab_subreddits.invoke(tool_args)
        elif tool_name == "post_to_subreddit":
            with st.spinner("Posting to the subreddit..."):
                result = post_to_subreddit.invoke(tool_args)
        else:
            result = f"Unknown tool: {tool_name}"

        # 2) Inject the tool result back into the conversation (hidden from UI)
        reformat_prompt = f"Here is the raw output from the tool: {result}. " \
            f"DO NOT CALL A TOOL CALL AGAIN, IT HAS ALREADY BEEN CALLED.If the output is in the form of [(subreddit name, rank), ...], this is a list of subreddits, please select the top 5 most relevant ones based on their descriptions and return them to the user in a friendly way. Otherwise if the output is a url to a reddit post, say that the post was successfully submitted and hyperlink it. Remember be friendly!"

        print("REFORMAT PROMPT: ", reformat_prompt)
        temp_msgs = convert_to_langchain_messages()
        temp_msgs.append(HumanMessage(content=reformat_prompt))  # Hidden prompt for LLM

        # 3) Invoke the LLM again to reformat the tool output
        with st.spinner("Processing tool results..."):
            final_response = llm_with_tools.invoke(temp_msgs)

        # 4) Add only the reformatted response to the session state for display
        formatted_content = final_response.content
        print("FORMATTED CONTENT: ", final_response)
        add_message("assistant", formatted_content)

    return final_response


def main():
    st.set_page_config(page_title="Subreddit AI Agent",
                       page_icon=None, layout="wide")
    st.title("Welcome to the Subreddit AI Agent")
    init_session_state()

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask me about subreddits or anything else...")

    if user_input:
        # Immediately display user's new message at the bottom
        with st.chat_message("user"):
            st.markdown(user_input)
        add_message("user", user_input)

        # Prepare LLM call
        langchain_msgs = convert_to_langchain_messages()

        # Create a placeholder for the AI response, so the spinner is localized
        ai_message_placeholder = st.chat_message("assistant")
        with ai_message_placeholder:
            with st.spinner("Thinking..."):
                try:
                    ai_response = llm_with_tools.invoke(langchain_msgs)
                except Exception as e:
                    st.error(f"LLM invocation error: {str(e)}")
                    return

                final_content = ai_response.content
                # If tools were called, handle them
                if ai_response.tool_calls:
                    final_response = handle_tool_calls(ai_response)
                    final_content = final_response.content

                # Now replace the spinner with the final AI message
                add_message("assistant", final_content)
                st.markdown(final_content)

    # No final display_messages() call, because we manually printed messages above.
    # The entire conversation plus the new messages is visible now.


if __name__ == "__main__":
    main()
