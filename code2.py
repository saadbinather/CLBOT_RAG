import requests
import pandas as pd
import time
from datetime import datetime

SUBREDDIT = "championsleague"
POSTS_PER_REQUEST = 100
TOTAL_POSTS = 1000   # change this to 2000, 3000 etc


def fetch_posts(subreddit, total_posts):
    headers = {
        "User-Agent": "Mozilla/5.0 reddit-data-collector"
    }

    all_posts = []
    after = None

    while len(all_posts) < total_posts:
        url = f"https://www.reddit.com/r/{subreddit}/.json?limit={POSTS_PER_REQUEST}"
        
        if after:
            url += f"&after={after}"

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("Error:", response.status_code)
            break

        data = response.json()
        posts = data["data"]["children"]

        if not posts:
            break

        for post in posts:
            p = post["data"]

            all_posts.append({
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

        after = data["data"]["after"]

        print(f"Collected: {len(all_posts)} posts")

        time.sleep(1)  # avoid rate limiting

        if not after:
            break

    return all_posts[:total_posts]


def main():
    print("Fetching posts...")

    posts = fetch_posts(SUBREDDIT, TOTAL_POSTS)

    df = pd.DataFrame(posts)

    filename = f"{SUBREDDIT}_posts_extended.csv"
    df.to_csv(filename, index=False)

    print(f"\nSaved {len(df)} posts to {filename}")


if __name__ == "__main__":
    main()