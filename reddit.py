from webbrowser import get
import praw
from dotenv import load_dotenv
load_dotenv()
import os
from collections import defaultdict

### CONSTANTS ###
search_limit = 20
top_n = 10

def get_relevant_subreddits(keywords, search_limit=20, top_n=50):
    """
    Fetch the top 'top_n' relevant subreddits based on keyword matches in their name and description.

    Args:
        keywords (list): A list of keywords to search for.
        search_limit (int): Number of subreddit results to evaluate for each keyword search.
        top_n (int): Number of top relevant subreddits to return.

    Returns:
        list: A list of tuples containing subreddit names and descriptions.
    """
    # Initialize Reddit API
    reddit = praw.Reddit(client_id=os.getenv("CLIENT_ID"),
                         client_secret=os.getenv("CLIENT_SECRET"),
                         user_agent="ToastyPostyBot/1.0 by u/One-Cap-3906")

    # Dictionary to store subreddit scores
    subreddit_scores = defaultdict(int)
    subreddit_details = {}

    # Search subreddits for each keyword
    for keyword in keywords:
        try:
            search_results = reddit.subreddits.search(
                keyword, limit=search_limit)
            for subreddit in search_results:
                # Combine name and description for keyword matching
                content = f"{subreddit.display_name} {subreddit.public_description}".lower()
                subreddit_details[subreddit.display_name] = {
                    "description": subreddit.public_description
                }

                # Count keyword occurrences
                keyword_matches = sum(
                    1 for k in keywords if k.lower() in content)
                if keyword_matches > 0:
                    subreddit_scores[subreddit.display_name] += keyword_matches
        except Exception as e:
            print(f"Error searching for '{keyword}': {e}")

    # Sort subreddits by score in descending order
    sorted_subreddits = sorted(
        subreddit_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Get top 'top_n' subreddits with details
    top_subreddits = [
        (name, subreddit_details[name]["description"])
        for name, _ in sorted_subreddits[:top_n]
    ]

    return top_subreddits


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


# Example Usage
keywords = [
    "credit cards",
    "rewards",
    "cashback",
    "travel cards",
    "balance transfer",
    "credit score",
    "low interest",
    "annual fee",
    "secured cards",
    "debt management"
]
print("SUBREDDITS: ", get_relevant_subreddits(keywords, search_limit, top_n))