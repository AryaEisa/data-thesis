import praw
import pandas as pd
import time
import os
import re
import concurrent.futures
import logging
from prawcore.exceptions import TooManyRequests, NotFound, Forbidden, Redirect
from praw.exceptions import RedditAPIException


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

reddit = praw.Reddit(
    client_id="",
    client_secret="",
    user_agent=""
)
CSV_FILE = ""
MAX_RETRIES = 5
REQUEST_DELAY = 3  
def ensure_csv():
  
    columns = ["No.", "id", "created_utc", "title", "text", "subreddit", "type", "author", "score"]
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
def get_last_number():

    try:
        df = pd.read_csv(CSV_FILE, dtype={"No.": "Int64"})
        return df["No."].max() if not df.empty else 0
    except Exception as e:
        logger.warning(f"Kunde inte läsa CSV: {e}")
        return 0
def get_existing_ids():
    """Hämtar sparade ID:n"""
    try:
        df = pd.read_csv(CSV_FILE)
        return set(df["id"].astype(str)) if "id" in df.columns else set()
    except Exception as e:
        logger.warning(f"Kunde inte läsa existerande ID:n: {e}")
        return set()

me_too_patterns = [
    
]

exclusion_patterns = [
   
]

subreddits = [
  
]
def contains_relevant_keywords(text: str) -> bool:
    text = re.sub(r"[^a-zA-ZåäöÅÄÖéÉ\s]", "", text.lower())
    return any(pattern.search(text) for pattern in me_too_patterns)
def fetch_subreddit_posts(subreddit, existing_ids, current_number):
    posts = []
    local_number = current_number
    retries = 0
    while retries < MAX_RETRIES:
        try:
            subreddit_instance = reddit.subreddit(subreddit)
            logger.info(f" r/{subreddit}...")

            for submission in subreddit_instance.top(time_filter="all", limit=500):
                try:
                    if submission.id in existing_ids or len(submission.selftext.split()) < 150:
                        continue
                    if not contains_relevant_keywords(submission.selftext):
                        continue
                    local_number += 1
                    posts.append({
                        "No.": local_number,
                        "id": submission.id,
                        "created_utc": submission.created_utc,
                        "title": submission.title.strip(),
                        "text": submission.selftext.strip(),
                        "subreddit": subreddit,
                        "type": "post",
                        "author": submission.author.name if submission.author else "Deleted",
                        "score": submission.score
                    })
                    time.sleep(REQUEST_DELAY)

                except Exception as e:
                    logger.error(f"Fel vid bearbetning av post: {e}")
            break
        except Forbidden:
            logger.warning(f"❌ Åtkomst nekad: r/{subreddit} (403 Forbidden) - Hoppar över...")
            return pd.DataFrame(), current_number 
        except (TooManyRequests, RedditAPIException) as e:
            retries += 1
            wait_time = min(300, (2 ** retries) * 30)
            logger.warning(f"Rate limit nådd på r/{subreddit}, väntar {wait_time}s...")
            time.sleep(wait_time)
    return pd.DataFrame(posts), local_number


