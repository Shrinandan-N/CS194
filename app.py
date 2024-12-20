import streamlit as st
import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from reddit import get_relevant_subreddits, post_to_reddit, fetch_comments_for_query

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

@tool
def fetch_comments(subreddit: str, query: str, post_limit: int = 5, comment_limit: int = 5) -> list:
    """
    Fetch top posts and comments for a given query in a subreddit.
    
    Args:
        subreddit (str): The subreddit to search.
        query (str): The search query.
        post_limit (int): Number of top posts to retrieve.
        comment_limit (int): Number of comments per post.

    Returns:
        list: A list of dictionaries containing post titles, URLs, and comments.
    """
    print(f"Fetching comments for query '{query}' in r/{subreddit}...")
    results = fetch_comments_for_query(subreddit, query, post_limit, comment_limit)
    return results

tools = [grab_subreddits, post_to_subreddit, fetch_comments]
llm_with_tools = llm.bind_tools(tools)

def init_session_state():
    """Initialize session state variables, if not already present."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "system_prompt" not in st.session_state:
        # Store system instructions hidden from the UI
        st.session_state["system_prompt"] = """
        You are a helpful AI assistant designed to assist users with their queries and connect them to relevant subreddit communities. Follow these steps:

Step 1: **Understand the User Query**
- Start by understanding the user's question or request.
- Ask clarifying questions to refine the user's intent and gather relevant details.

Step 2: **Keyword Extraction**
- Generate at least 5 distinct, meaningful keywords that represent the core aspects of the user's query.
- Keywords should cover various dimensions of the query (e.g., topics, preferences, constraints).
- Present the keywords to the user for approval in array format, such as: ["travel", "credit cards", "rewards", "points", "international travel"].

Step 3: **Find Relevant Subreddits**
- Call the `grab_subreddits()` function with the approved keyword list.
- Review the returned subreddits and select the top 5 most relevant ones based on their descriptions.
- Present the selected subreddits to the user in a friendly manner:
    "I found these subreddits that might help: r/travel, r/creditcards, r/awardtravel. Would you like to explore one of these further?"

Step 4: **Analyze Subreddit Content**
- Once the user chooses a subreddit, formulate a relevant query based on their original question and preferences.
- Call the `fetch_comments()` function with the chosen subreddit and query to retrieve:
    - The top N posts (e.g., 5) and the top M comments per post (e.g., 5).
    - Each posts's answers will be in a list and in the following format: {
                "title": submission.title,
                "url": submission.url,
                "comments": top_comments (list)
            }
- Summarize the most relevant insights from the comments to address the user's question. Present the summary clearly:
    "Here’s what I found based on community insights: ..."
- Ask the user if the summary answers their question:
    - If yes: End the conversation politely.
    - If no: Proceed to the next step.

Step 5: **Prepare to Post to Subreddit**
- If the user is unsatisfied with the summary and agrees to post a question, collaborate with them to brainstorm:
    - A clear and engaging post title.
    - A well-structured and concise post body.
- Confirm the final content with the user before proceeding.

Step 6: **Post to Subreddit**
- Call the `post_to_subreddit()` function with the chosen subreddit, title, and content.
- If the post is successful, confirm with the user and provide a direct link:
    "Your question has been successfully posted! Here's the link: [POST_URL]"

Example Flow:
User Query: "I want to know the best travel credit cards for earning points."

1. **Clarification**:
   - "Are you looking for travel-specific rewards or general cashback?"
   - "Do you need perks like no foreign transaction fees?"
   - "Is this for business travel, personal trips, or international travel?"

2. **Extracted Keywords**:
   ["travel", "credit cards", "rewards", "points", "international travel"]

3. **Subreddit Suggestions**:
   "I found these subreddits: r/travel, r/creditcards, r/awardtravel. Would you like me to look deeper into one of these?"

4. **Content Analysis**:
   Summarize top posts and comments to provide insights, such as:
   - "The Chase Sapphire Preferred is highly recommended for its rewards flexibility."
   - "Amex Platinum is great for lounge access but has a high annual fee."

5. **Posting**:
   If the user requests, prepare and post their question to the chosen subreddit.

Ensure all responses are concise, clear, and user-friendly. Keep the user informed at every step.
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
        elif tool_name == "fetch_comments":
            with st.spinner("Fetching top posts and comments..."):
                print(f"Reached: {tool_args}")
                result = fetch_comments.invoke(tool_args)
        else:
            result = f"Unknown tool: {tool_name}"

        # 2) Inject the tool result back into the conversation (hidden from UI)
        reformat_prompt = f"""Here is the raw output from the tool: {result}. DO NOT CALL A TOOL CALL AGAIN, IT HAS ALREADY BEEN CALLED.
            If the output is in the form of [(subreddit name, rank), ...], this is a list of subreddits, please select the top 5 most relevant ones based on their descriptions and return them to the user in a friendly way. 
            Otherwise if the output is in the form of [(title, url, comments)], this is a list of posts and comments, and please summarize the most relevant insights from the comments to address the user's question. Present the summary clearly:
            Otherwise if the output is a url to a reddit post, say that the post was successfully submitted and hyperlink it. Remember be friendly!"""

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
