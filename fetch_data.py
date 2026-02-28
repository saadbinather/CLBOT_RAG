import praw
import json

reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="ucl-bot"
)

subreddit = reddit.subreddit("soccer")

posts_data = []

for post in subreddit.search("Champions League", limit=100):
    post.comments.replace_more(limit=0)
    
    comments = []
    for comment in post.comments.list():
        comments.append(comment.body)

    posts_data.append({
        "title": post.title,
        "selftext": post.selftext,
        "comments": comments
    })

with open("ucl_reddit_raw.json", "w", encoding="utf-8") as f:
    json.dump(posts_data, f, indent=4)

print("Saved Reddit data")