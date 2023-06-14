from __future__ import annotations

import argparse
import codecs
import json
import re
import sys
from datetime import datetime
from pathlib import Path, WindowsPath
from time import time

import praw
from tqdm import tqdm

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def fetch_item_comments(item: praw.models.Submission) -> list:
    item.comment_sort = "top"
    item_comments = []
    for comment in item.comments:
        # top level comment
        if isinstance(comment, praw.models.MoreComments):
            continue
        comment_created = datetime.utcfromtimestamp(
            comment.created_utc).strftime(TIME_FORMAT)
        comment_author_name = "N/A"
        if comment.author is not None:
            comment_author_name = comment.author.name
        comment_body = {
            "id": comment.id,
            "author": comment_author_name,
            "content": comment.body,
            "created": comment_created,
            "score": comment.score,
            "url": comment.permalink
        }
        item_comments.append(comment_body)
        if len(item_comments) == 10:
            break
    return item_comments


def build_saved_item_dict(reddit: praw.Reddit,
                          item: praw.models.Submission | praw.models.Comment,
                          item_ix: int, fetch_comments: bool) -> dict:
    item_created = datetime.utcfromtimestamp(
        item.created_utc).strftime(TIME_FORMAT)

    item_title = "N/A"
    item_comments = []
    if isinstance(item, praw.models.Comment):
        type_saved = "comment"
        content = item.body.strip()
        # https://reddit.com/r/<SUBREDDIT>/comments/<POST_ID>/<POST_TITLE>/<COMMENT_ID>/"
        post_id = item.permalink.split("/")[4]
        post_item = list(reddit.info(fullnames=[f"t3_{post_id}"]))[0]
        item_title = post_item.title.strip()
        link = "https://reddit.com" + item.permalink
    elif isinstance(item, praw.models.Submission):
        type_saved = "post"
        item_title = item.title.strip()
        content = item.selftext.strip()

        if fetch_comments:
            item_comments = fetch_item_comments(item)
        link = item.url
    else:
        return None

    sub = re.findall(r"/r/([^\s/]+)", link)
    if len(sub):
        subreddit = sub[0]
    else:
        subreddit = "Image/External Link"

    author_name = "N/A"
    if item.author is not None:
        author_name = item.author.name
    item_dict = {
        "id": item.id,
        "type": type_saved,
        "title": item_title,
        "content": content,
        "url": link,
        "subreddit": subreddit,
        "created": item_created,
        "author": author_name,
        "score": item.score,
        "awards": item.total_awards_received,
        "ix": item_ix,
        "comments": item_comments,
    }
    # pprint(item_dict)
    return item_dict


def fetch_saved_items(client_id: str,
                      client_secret: str,
                      reddit_username: str,
                      reddit_password: str,
                      fetch_comments: bool = True,
                      verbose: bool = False) -> list:
    reddit = praw.Reddit(client_id=client_id,
                         client_secret=client_secret,
                         username=reddit_username,
                         password=reddit_password,
                         user_agent=f"savedexporter:v0.1.0")

    me = reddit.user.me()
    print(f"Fetching saved links for u/{me}")

    saved_items = []
    start = time()
    for item_ix, item in tqdm(enumerate(me.saved(limit=None))):
        item_dict = build_saved_item_dict(reddit, item, item_ix,
                                          fetch_comments)
        if item_dict is None:
            continue
        saved_items.append(item_dict)

    print("FETCHED:", len(saved_items))
    print("TOOK :", time() - start, "seconds")
    print("AVG  :", (time() - start) / float(len(saved_items)))

    return saved_items


def read_from_json(reddit_username: str, json_filepath: str) -> list:
    print(f"Fetching saved links for u/{reddit_username}")
    with open(json_filepath, "r") as f:
        saved_items = json.load(f)
    print("FOUND:", len(saved_items))
    return saved_items


def write_to_json(reddit_username: str, saved_items: list):
    cwd = Path.cwd()
    saved_path = Path(f"{cwd}/{reddit_username}/saved/")
    print(saved_path)
    if not saved_path.exists():
        saved_path.mkdir(parents=True, exist_ok=False)

    with open(str(saved_path) + "/saved_links.json", "w") as f:
        json.dump(saved_items, f)


def write_to_md(reddit_username: str, saved_items: list):
    cwd = Path.cwd()
    saved_path = Path(f"{cwd}/{reddit_username}/saved/")
    print(saved_path)
    with open(str(saved_path) + "/saved_links.md", "w", encoding="utf-8") as f:
        for item_ix, item in enumerate(saved_items):
            subreddit = item["subreddit"]

            if subreddit == "Image/External Link":
                f.write(f"{item_ix+1}  :\n")
            else:
                f.write(
                    f"{item_ix+1} : [r/{subreddit}](https://reddit.com/r/{subreddit})\n"
                )

            f.write(f"  -- [{item['title']}]({item['url']})\n")
            f.write("\n")
            f.write(item["content"])
            f.write(f"\n{'*'*40}\n")


def parse_args(main_args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="", type=str, default="")
    parser.add_argument("-p", "--password", help="", type=str, default="")
    parser.add_argument("-i", "--client-id", help="", type=str, default="")
    parser.add_argument("-s", "--client-secret", help="", type=str, default="")
    parser.add_argument("-f", "--json-file", help="", type=str, default="")
    parser.add_argument("-c",
                        "--fetch-comments",
                        help="",
                        type=bool,
                        default=False)
    parser.add_argument("-v", "--verbose", help="", type=bool, default=False)
    args = parser.parse_args(main_args)

    return args


def main():
    args = parse_args(sys.argv[1:])

    if args.json_file and args.username:
        saved_items = read_from_json(args.username, args.json_file)
        write_to_md(args.username, saved_items)
    else:
        saved_items = fetch_saved_items(args.client_id, args.client_secret,
                                        args.username, args.password,
                                        args.fetch_comments, args.verbose)
        write_to_json(args.username, saved_items)
        write_to_md(args.username, saved_items)


if __name__ == "__main__":
    main()