import os
from re import search, sub
import stat
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from reddit import get_relevant_subreddits, post_to_reddit, fetch_comments_for_query

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No OpenAI API key found. Please check your .env file.")

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)


@tool
def grab_subreddits(keywords: list[str]) -> list:
    """finds subreddits based on keywords"""
    print("Grabbing subreddits for keywords: ", keywords)
    subreddits = get_relevant_subreddits(keywords, search_limit=20)
    print("Found subreddits: ", subreddits)
    # next step is to make an LLM call to filter this!
    return subreddits


@tool
def post_to_subreddit(subreddit: str, title: str, content: str) -> str:
    """Posts to a subreddit."""
    result = post_to_reddit(subreddit, title, content)
    if result:
        status = "success"
    else:
        status = "failure"
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


def interactive_chat(initial_instructions: str = ""):
    print("🤖 AI Agent Chat Interface")
    print("Type 'exit' to end the conversation")

    messages = []

    if initial_instructions.strip():
        messages.append(HumanMessage(content=initial_instructions.strip()))
        # print(f"Initial instructions loaded:\n{
        #       initial_instructions.strip()}\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        messages.append(HumanMessage(content=user_input))

        try:
            # Invoke the LLM with the current messages
            ai_response = llm_with_tools.invoke(messages)

            # Add the AI's response to messages
            messages.append(ai_response)

            # Check if there are tool calls
            if ai_response.tool_calls:
                # Process each tool call
                for tool_call in ai_response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_call_id = tool_call["id"]

                    # Dynamically select and invoke the tool
                    if tool_name == "grab_subreddits":
                        tool_result = grab_subreddits.invoke(tool_args)
                    elif tool_name == "post_to_subreddit":
                        tool_result = post_to_subreddit.invoke(tool_args)
                    else:
                        print(f"Unknown tool: {tool_name}")
                        continue

                    # Create a ToolMessage
                    tool_message = ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call_id
                    )

                    # Add the tool message to messages
                    messages.append(tool_message)

                # Re-invoke the LLM with the updated messages
                final_response = llm_with_tools.invoke(messages)

                # Print and add the final response
                print("\nAI:", final_response.content)
                messages.append(final_response)

            else:
                # If no tool calls, just print the AI's response
                print("\nAI:", ai_response.content)

        except Exception as e:
            print(f"\nError: {e}")
            # Print the full traceback for debugging
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    instructions = """

    Prompt for AI Assistant:
You are a helpful AI assistant designed to assist users with their queries and connect them with relevant subreddit communities. Follow these steps:

User Query: Start by understanding the user's initial question or request.
Clarification: Engage in a conversation to clarify the user's intent until you can generate at least 10 distinct keywords related to their topic. These should encompass various facets of their request.
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
Extracted Keywords: ["travel", "credit cards", "rewards"].
MAKE SURE TO PASS THE EXRTRACTED KEYWORDS AS AN ARRAY LIKE ["travel", "credit cards", "rewards", "points"] to the grab_subreddits() function.
Grab Subreddits: Call grab_subreddits(["travel", "credit cards", "rewards", "points", "cashback", "international travel", "foreign transaction fees", "business travel", "personal trips", "frequent flyer"]).
Based on the returned subreddits, choose the top 5 that you think are most relevant to the query based on their descriptions.
Confirmation the subreddit:
"I found these relevant subreddits: r/travel, r/creditcards, r/awardtravel. Would you like to dive deeper into one or more of these subreddits?"
Brainstorm title and content for the post with the user.

Analyze Subreddit Content: Once the user selects a subreddit of interest, analyze the top posts and comments to gather insights relevant to the user’s query:
Call the fetch_comments() tool to: search for the query within the subreddit, retrieve the top N posts (e.g., 5) and the top M comments (e.g., 5) per post, summarize the insights clearly for the user.
Ask if the summary answered the user's question. If the user is happy with the summary, then they have their answer and no further steps are necessary. If not, then continuing to posting steps.

Post to Subreddit: If the user agrees, post the query to the selected subreddit(s). 
If the response from the function says like Post Submitted, then its a success! Let the user know.
"""
    interactive_chat(initial_instructions=instructions)
