import codecs
import json
import praw
from pprint import pprint
import re
from time import time

REDDIT_USERNAME = ''
REDDIT_PASSWORD = ''
CLIENT_ID = ''
CLIENT_SECRET = ''

reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     password=REDDIT_PASSWORD,
                     user_agent='reddit saves exporter /u/' + REDDIT_USERNAME,
                     username=REDDIT_USERNAME)

me = reddit.redditor(REDDIT_USERNAME)

saved = {}
start = time()
for ix, item in enumerate(me.saved(limit=None)):
    item_name = item.name
    item_id = item.id
    if item_name[:2] == 't1':
        type_saved = 'comment'
        content = item.body.strip()
        link = 'https://reddit.com' + item.permalink
        print(f"ID: {item_name} TYPE: COMMENT")
    elif item.name[:2] == 't3':
        type_saved = 'post'
        content = item.title.strip()
        print(f"ID: {item_name} TYPE: POST TITLE: {item.title.strip()}")
        link = item.url
    else:
        continue
    sub = re.findall(r"/r/([^\s/]+)", link)
    try:
        sub = sub[0]
    except IndexError as e:
        sub = u'Image/External Link'
    saved[ix] = {
        'Name': item_name,
        'Type': type_saved,
        'Content': content,
        'Url': link,
        'Subreddit': sub
    }

print("SAVED:", len(saved), "links")
print("TOOK :", time() - start, "seconds")
print("AVG  :", (time() - start) / float(len(saved)))

with open('./saved_links.json', 'w') as f:
    json.dump(saved, f)

with codecs.open('./saved_links.md', 'w', encoding='utf-8') as f:
    for item in saved:
        subr = saved[item]['Subreddit']
        new_content = re.sub(r'_{3,}', '', saved[item]['Content'])
        if subr == u'Image/External Link':
            f.write(str(item + 1) + "  :\n")
        else:
            f.write(
                str(item + 1) + "  :  [r/" + subr + '](' +
                'https://reddit.com/' + subr + ')\n')
        if saved[item]['Type'] == 'post':
            f.write("[" + new_content + "](" + saved[item]['Url'] + ")")
        else:
            f.write("\n")
            f.write("[Permalink](" + saved[item]['Url'] + ")\n")
            f.write(new_content)
        f.write("\n********************************************\n")
