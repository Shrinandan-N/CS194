from webbrowser import get
import praw

def get_100_subreddits(keywords):
    reddit = praw.Reddit(client_id="0MFmtUnQVteI8igkmZIO4A",
                         client_secret="dL5Ud4N_aH2lzTggcGhWDCZVn6_aAg",
                         user_agent="ToastyPostyBot/1.0 by u/One-Cap-3906")
    subreddits = []
    for keyword in keywords:
        subreddits.extend(reddit.subreddit(keyword).hot(limit=100))

    subreddits = [subreddit.subreddit.display_name for subreddit in subreddits]

    return subreddits

def post_to_reddit(subreddit, title, content):
    client_id = "0MFmtUnQVteI8igkmZIO4A"
    client_secret = "dL5Ud4N_aH2lzTggcGhWDCZVn6_aAg"
    username = "One-Cap-3906"  
    password = "toastyposty123"  
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

print("SUBREDDITS: ", get_100_subreddits(["food"]))