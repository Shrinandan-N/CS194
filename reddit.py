import os
from webbrowser import get
import praw
from dotenv import load_dotenv
load_dotenv()
from collections import defaultdict



def get_relevant_subreddits(keywords, search_limit=100):
    # Initialize Reddit API
    reddit = praw.Reddit(client_id=os.getenv("CLIENT_ID"),
                         client_secret=os.getenv("CLIENT_SECRET"),
                         username=os.getenv("USERNAME"),
                         password=os.getenv("PASSWORD"),
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
                try:
                    if subreddit.user_is_banned or len(list(subreddit.rules)) == 0 or subreddit.subscribers < 1000:
                        print("Skipping banned subreddit: " +
                              subreddit.display_name)
                        continue
                    
                    print("Found subreddit: " + subreddit.display_name)

                    content = f"{subreddit.display_name} {
                        subreddit.public_description}".lower()
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


# print(get_relevant_subreddits(['travel', 'rewards', 'bonuses'], search_limit=20, top_n=10))
# print(post_to_reddit("TravelHacks", "test title", "test content"))
