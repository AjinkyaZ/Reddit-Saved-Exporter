import codecs
import json
import praw
import re
from time import time
from datetime import datetime
import sys
import argparse


def parse_args(main_args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="", type=str, default="")
    parser.add_argument("-p", "--password", help="", type=str, default="")
    parser.add_argument("-i", "--client-id", help="", type=str, default="")
    parser.add_argument("-s", "--client-secret", help="", type=str, default="")
    parser.add_argument("-v", "--verbose", help="", type=bool, default=False)
    args = parser.parse_args(main_args)

    return args


def main():
    args = parse_args(sys.argv[1:])

    reddit = praw.Reddit(client_id=args.client_id,
                         client_secret=args.client_secret,
                         username=args.username,
                         password=args.password,
                         user_agent=f"savedexporter:v0.1.0")

    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    me = reddit.user.me()
    print(f"Fetching saved links for u/{me}")

    verbose = args.verbose

    saved = []
    start = time()
    for item_ix, item in enumerate(me.saved(limit=None)):
        item_name = item.name
        item_created = datetime.utcfromtimestamp(
            item.created_utc).strftime(TIME_FORMAT)

        item_title = "N/A"
        if item_name[:2] == "t1":
            type_saved = "comment"
            content = item.body.strip()
            # https://reddit.com/r/<SUBREDDIT>/comments/<POST_ID>/<POST_TITLE>/<COMMENT_ID>/"
            post_id = item.permalink.split("/")[4]
            post_item = list(reddit.info(fullnames=[f"t3_{post_id}"]))[0]
            item_title = post_item.title.strip()
            link = "https://reddit.com" + item.permalink
        elif item.name[:2] == "t3":
            type_saved = "post"
            item_title = item.title.strip()
            content = item.selftext.strip()
            link = item.url
        else:
            continue

        sub = re.findall(r"/r/([^\s/]+)", link)
        try:
            subreddit = sub[0]
        except IndexError as e:
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
        }
        # pprint(item_dict)
        saved.append(item_dict)

    print("SAVED:", len(saved), "links")
    print("TOOK :", time() - start, "seconds")
    print("AVG  :", (time() - start) / float(len(saved)))

    with open("./saved_links.json", "w") as f:
        json.dump(saved, f)

    with codecs.open("./saved_links.md", "w", encoding="utf-8") as f:
        for item_ix, item in enumerate(saved):
            subreddit = item["subreddit"]

            if subreddit == "Image/External Link":
                f.write(f"{item_ix+1}  :\n")
            else:
                f.write(
                    f"{item_ix+1} : [r/{subreddit}](https://reddit.com/{subreddit})\n"
                )

            f.write(f"  -- [{item['title']}]({item['url']})\n")
            if item["type"] == "comment":
                f.write("\n")
                f.write(item["content"])
            f.write(f"\n{'*'*40}\n")


if __name__ == "__main__":
    main()