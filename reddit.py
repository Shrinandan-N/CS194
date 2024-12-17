import praw
import FastAPI


def main():
    client_id = "0MFmtUnQVteI8igkmZIO4A"
    client_secret = "dL5Ud4N_aH2lzTggcGhWDCZVn6_aAg"
    username = "One-Cap-3906"  # Your Reddit username
    password = "toastyposty123"  # Replace with your Reddit password
    user_agent = "ToastyPostyBot/1.0 by u/One-Cap-3906"

    # Initialize Reddit instance
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        password=password,
        user_agent=user_agent
    )

    # Choose subreddit and submit post
    subreddit = reddit.subreddit("test")
    title = "Hello Reddit this is Jatin Devireddy from Goyal Industries"
    content = "Justin Narayanan says hello!"

    submission = subreddit.submit(title=title, selftext=content)
    print(f"Post submitted! URL: {submission.url}")

main()