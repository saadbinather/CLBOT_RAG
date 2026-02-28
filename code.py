import requests
import pandas as pd
import time
from datetime import datetime


SUBREDDIT = "championsleague"
POST_LIMIT = 100  # Max ~100 per request


def fetch_posts(subreddit, limit=100):
    url = f"https://www.reddit.com/r/{subreddit}/.json?limit={limit}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) reddit-scraper"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Error:", response.status_code)
        return []

    data = response.json()
    posts = data["data"]["children"]

    results = []

    for post in posts:
        p = post["data"]

        results.append({
            "id": p["id"],
            "title": p["title"],
            "author": p["author"],
            "score": p["score"],
            "num_comments": p["num_comments"],
            "created_utc": datetime.fromtimestamp(p["created_utc"]),
            "upvote_ratio": p.get("upvote_ratio"),
            "url": p["url"],
            "selftext": p["selftext"]
        })

    return results


def main():
    print(f"Fetching posts from r/{SUBREDDIT}...")

    posts = fetch_posts(SUBREDDIT, POST_LIMIT)

    df = pd.DataFrame(posts)

    print(df.head())

    filename = f"{SUBREDDIT}_posts.csv"
    df.to_csv(filename, index=False)

    print(f"\nSaved {len(df)} posts to {filename}")


if __name__ == "__main__":
    main()