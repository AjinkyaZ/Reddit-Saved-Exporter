import codecs
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
                     user_agent='reddit saves exporter /u/'+REDDIT_USERNAME,
                     username=REDDIT_USERNAME)

me = reddit.redditor(REDDIT_USERNAME)

saved = {}
start = time()
for index, i in enumerate(me.saved()):
    name = i.name
    if i.name[:2]=='t1':
        type_saved = 'comment'
        content = i.body.strip()
        link = 'https://reddit.com'+i.permalink()
    elif i.name[:2]=='t3':
        type_saved = 'post'
        content = i.title.strip()
        link = i.url
    else:
        continue 
    sub = re.findall(r"/r/([^\s/]+)", link)
    try:
        sub = sub[0]
    except IndexError, e:
        sub = u'Image/External Link'
    saved[index] = {'Name': name, 
                    'Type':type_saved,
                    'Content': content,
                    'Url': link,
                    'Subreddit': sub
                   }

print "SAVED:", len(saved), "links"
print "TOOK :", time()-start, "seconds"
print "AVG  :", (time()-start)/float(len(saved))

with open('./saved_links.json', 'w') as f:
    json.dump(saved, f)

with codecs.open('./saved_links.md', 'w', encoding='utf-8') as f:
    for i in saved:
        subr = saved[i]['Subreddit']
        new_content = re.sub(r'_{3,}', '', saved[i]['Content'])
        if subr == u'Image/External Link':
            f.write(str(i+1)+"  :\n")
        else:
            f.write(str(i+1)+"  :  [r/"+subr+']('+'https://reddit.com/'+subr+')\n')
        if saved[i]['Type'] == 'post':
            f.write("["+new_content+"]("+saved[i]['Url']+")")
        else:
            f.write("\n")
            f.write("[Permalink]("+saved[i]['Url']+")\n")
            f.write(new_content)
        f.write("\n********************************************\n")
