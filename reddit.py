import os
from webbrowser import get
import praw
from dotenv import load_dotenv
load_dotenv()
from collections import defaultdict


### CONSTANTS ###
search_limit = 20
top_n = 10
USER_AGENT = "ToastyPostyBot/1.0 by u/One-Cap-3906"
SEARCH_LIMIT = 20  # Number of posts to fetch
COMMENT_LIMIT = 5  # Number of top comments to fetch per post
SUMMARY_TOKEN_LIMIT = 200  # Token limit for GPT summarization



def get_relevant_subreddits(keywords, search_limit=100):
    # Initialize Reddit API
    reddit = praw.Reddit(client_id=os.getenv("CLIENT_ID"),
                         client_secret=os.getenv("CLIENT_SECRET"),
                         username=os.getenv("USERNAME"),
                         password=os.getenv("PASSWORD"),
                         user_agent="ToastyPostyBot/1.0 by u/One-Cap-3906")

    subreddit_scores = defaultdict(int)
    subreddit_details = {}

    for keyword in keywords:
        try:
            search_results = reddit.subreddits.search(
                keyword, limit=search_limit)
            for subreddit in search_results:
                try:
                    if subreddit.user_is_banned or len(list(subreddit.rules)) == 0 or subreddit.subscribers < 1000:
                        print("Skipping banned subreddit: " +
                              subreddit.display_name)
                        continue
                    
                    print("Found subreddit: " + subreddit.display_name)

                    content = (
                        f"{subreddit.display_name} {subreddit.public_description}"
                    ).lower()
                    subreddit_details[subreddit.display_name] = {
                        "description": subreddit.public_description
                    }

                    # Count keyword occurrences
                    keyword_matches = sum(
                        1 for k in keywords if k.lower() in content)
                    if keyword_matches > 0:
                        subreddit_scores[subreddit.display_name] += keyword_matches
                except Exception as e:
                    # Skip subreddits where submission check fails
                    print(e)
                    continue

        except Exception as e:  
            print(f"Error searching for '{keyword}': {e}")

    # Sort subreddits by score in descending order
    sorted_subreddits = sorted(
        subreddit_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )


    return sorted_subreddits


def post_to_reddit(subreddit, title, content):
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    username = os.getenv("USERNAME")  
    password = os.getenv("PASSWORD")  
    user_agent = "ToastyPostyBot/1.0 by u/One-Cap-3906"

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        password=password,
        user_agent=user_agent
    )

    subreddit = reddit.subreddit(subreddit)
    title = title
    content = content

    submission = subreddit.submit(title=title, selftext=content)
    print(f"Post submitted! URL: {submission.url}")
    return submission.url


# def search_subreddit(subreddit_name, query, limit=10):
#     client_id = os.getenv("CLIENT_ID")
#     client_secret = os.getenv("CLIENT_SECRET")
#     user_agent = "ToastyPostyBot/1.0 by u/One-Cap-3906"

#     reddit = praw.Reddit(
#         client_id=client_id,
#         client_secret=client_secret,
#         user_agent=user_agent
#     )

#     subreddit = reddit.subreddit(subreddit_name)
#     print(f"Searching for '{query}' in r/{subreddit_name}...")

#     # Perform search
#     for submission in subreddit.search(query, limit=limit):
#         print(f"Title: {submission.title}")
#         print(f"URL: {submission.url}\n")



# def initialize_reddit():
#     """Initialize and return a Reddit API instance."""
#     return praw.Reddit(
#         client_id=os.getenv("CLIENT_ID"),
#         client_secret=os.getenv("CLIENT_SECRET"),
#         username=os.getenv("USERNAME"),
#         password=os.getenv("PASSWORD"),
#         user_agent=USER_AGENT
#     )


# def search_subreddit(reddit, subreddit_name, query, post_limit=10):

#     reddit = praw.Reddit(
#         client_id=os.getenv("CLIENT_ID"),
#         client_secret=os.getenv("CLIENT_SECRET"),
#         username=os.getenv("USERNAME"),
#         password=os.getenv("PASSWORD"),
#         user_agent=USER_AGENT
#     )

#     """Search for posts in a subreddit matching a query."""
#     subreddit = reddit.subreddit(subreddit_name)
#     print(f"Searching for '{query}' in r/{subreddit_name}...")

#     posts = []
#     for submission in subreddit.search(query, limit=post_limit):
#         posts.append({
#             "title": submission.title,
#             "url": submission.url,
#             "id": submission.id
#         })
#         print(f"Title: {submission.title}")
#         print(f"URL: {submission.url}\n")
#     return posts


# def fetch_top_comments(reddit, post_id, comment_limit=5):
#     """Fetch the top comments of a Reddit post."""
#     reddit = praw.Reddit(
#         client_id=os.getenv("CLIENT_ID"),
#         client_secret=os.getenv("CLIENT_SECRET"),
#         username=os.getenv("USERNAME"),
#         password=os.getenv("PASSWORD"),
#         user_agent=USER_AGENT
#     )

#     submission = reddit.submission(id=post_id)
#     submission.comments.replace_more(limit=0)  # Skip "load more" comments

#     comments = []
#     for comment in submission.comments[:comment_limit]:
#         comments.append(comment.body)
#     return comments


# def summarize_comments_with_gpt(comments):
#     """Summarize a list of comments using OpenAI GPT."""


#     prompt = (
#         "Summarize the following Reddit comments into a concise, clear answer:\n\n"
#         + "\n".join(comments)
#     )

#     response = openai.Completion.create(
#         model="gpt-4",  # Replace with "gpt-3.5-turbo" if needed
#         prompt=prompt,
#         max_tokens=SUMMARY_TOKEN_LIMIT,
#         temperature=0.5
#     )
#     return response.choices[0].text.strip()

def fetch_comments_for_query(subreddit_name, query, post_limit=5, comment_limit=5):
    """
    Search for posts matching a query in a subreddit, and fetch top comments.
    
    Args:
        subreddit_name (str): The subreddit to search in.
        query (str): The query to search for.
        post_limit (int): The number of posts to retrieve.
        comment_limit (int): The number of top comments to retrieve per post.

    Returns:
        list: A list of dictionaries, each containing:
              - "title": Post title
              - "url": Post URL
              - "comments": List of top comments
    """
    reddit = praw.Reddit(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        username=os.getenv("USERNAME"),
        password=os.getenv("PASSWORD"),
        user_agent="ToastyPostyBot/1.0 by u/One-Cap-3906"
    )
    subreddit = reddit.subreddit(subreddit_name)
    print(f"Searching '{query}' in r/{subreddit_name}...")

    results = []

    # Search posts matching the query
    for submission in subreddit.search(query, limit=post_limit):
        try:
            submission.comments.replace_more(limit=0)  # Load all top-level comments
            top_comments = [comment.body for comment in submission.comments[:comment_limit]]
            results.append({
                "title": submission.title,
                "url": submission.url,
                "comments": top_comments
            })
        except Exception as e:
            print(f"Error fetching comments for post '{submission.title}': {e}")
            continue

    return results

#print(get_relevant_subreddits(['travel', 'rewards', 'bonuses'], search_limit=20))
#print(post_to_reddit("TravelHacks", "test title", "test content"))
#search_subreddit("TravelHacks", "What are good", limit=5)
#print(fetch_comments_for_query("TravelHacks", "What are good credit cards for travel", post_limit=5, comment_limit=5))
