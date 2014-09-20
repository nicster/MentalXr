# -*- coding: utf8 -*-

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://www.wtfpl.net/ for more details.

import re
import os
import sys
import urllib
import shutil
import os.path
import threading

import bs4
import requests


def download_playlist(url):
    r = requests.get(url)
    b = bs4.BeautifulSoup(r.content)

    title = 'Mental X ' + re.search('\d{1,2}\. \w+ \d{4}', b.title.string).group(0)

    if not os.path.exists(title):
        os.mkdir(title)

    specialchar = {
        u'ö': 'oe',
        u'ä': 'ae',
        u'ü': 'ue',
        u'ù': 'u',
        u'ï': 'i',
        u'ì': 'i'
    }

    def replace_special_chars(string):
        for old, new in specialchar.iteritems():
            string = string.replace(old, new)
        return string

    tracks = [
        ('%s - %s (%s)' % tuple(replace_special_chars(tag.string.strip())
                                .split(' / '))) for tag in 
        b.select("div.article_body p") if tag.string is not None
    ]

    threads = []
    home = os.getenv("HOME")

    for track in tracks:
        threads.append(threading.Thread(target=download, args=(track, title)))

    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    print
    print 'Files have been downloaded and moved to ' + home + '/Downloads'

    shutil.move(title, os.getenv("HOME") + '/Downloads/' + title)


def download(track, folder, counter=0):
    if counter >= 3:
        print track + ' is not available'
        return
    try:
        r = requests.get('http://vmusice.net/mp3/' + 
                         urllib.quote(re.sub('[-()]', '', track)))
    except:
        print track
        return

    cookies = r.cookies
    b = bs4.BeautifulSoup(r.content)

    ptracks = []

    for ptrack in b.select("li.x-track"):
        try:
            d = re.search('(\d{1,2}):(\d{2})', 
                      ptrack.select("em").pop().string)
            ptracks.append({
                "title": ' '.join(
                    t.string for t in 
                    ptrack.select("span.title").pop().contents
                ),
                "duration": int(d.group(1)) * 60 + 
                            int(d.group(2)),
                "link": ptrack.select("a.download").pop()['href']
            })
        except Exception as e:
            print e

    ptracks.sort(key=lambda e: trackscore(e, track))

    if not ptracks:
        print "Couldn't find " + track 
        return
    elif ptracks[0]['duration'] < 4 * 60:
        print "Couldn't find a proper version of " + track
        return
    try:
        r = requests.get(ptracks[0]['link'], cookies=cookies, 
                         headers={'referer': r.url})
    except:
        download(track, folder, counter + 1)
        return

    with open(os.path.join(folder, track + '.mp3'), 'w') as f:
        f.write(r.content)


def trackscore(track, searchterm):
    return abs(track['duration'] - 8 * 60)


def main():
    if len(sys.argv) >= 2:
        download_playlist(sys.argv[1])
    else:
        print "Usage: mentalxr playlist-url"
        sys.exit(1)


if __name__ == "__main__":
    main()