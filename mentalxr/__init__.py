# -*- coding: utf8 -*-

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://www.wtfpl.net/ for more details.

import gevent.monkey
gevent.monkey.patch_all()

import re
import os
import sys
import time
import locale
import urllib
import os.path

import unidecode
import requests
import humanize
import gevent
import bs4

import mentalxr.progressbar


locale.setlocale(locale.LC_ALL, "de_DE")


class Playlist(object):
    def __init__(self, url):
        r = requests.get(url)
        if not r.ok:
            r.raise_for_status()

        dom = bs4.BeautifulSoup(r.content)
        self.tracks = list(self.extract_tracks(dom))
        self.date = self.extract_date(dom)

    def extract_tracks(self, dom):
        for tag in dom.select("div.article_body p"):
            if tag.string is None:
                continue
            data = unidecode.unidecode(tag.string.strip()).split(" / ")
            if len(data) < 3:
                continue
            yield Track(*data[:3])

    def extract_date(self, dom):
        match = re.search('\d+\. \w+ \d+', dom.title.string)
        try:
            return time.strptime(match.group(0).encode("utf-8"), "%d. %B %Y")
        except:
            return time.localtime()

    def download(self, destination):
        destination = os.path.join(destination, str(self))
        if not os.path.exists(destination):
            os.makedirs(destination)

        progressbar = mentalxr.progressbar.MultiProgressBar()

        jobs = [gevent.spawn(track.download, destination, progressbar)
                for track in self.tracks]
        gevent.joinall(jobs)

        print
        print "Files have been downloaded and moved to", destination

    def __str__(self):
        return time.strftime("Mental X - %d.%m.%Y", self.date)

    def __repr__(self):
        return time.strftime("Playlist(%d.%m.%Y)", self.date)


class Track(object):
    VMUSICE_URL = "http://vmusice.net/mp3/%s"
    DURATION_PATTERN = re.compile("((\d+):)?(\d+):(\d+)")

    def __init__(self, artist, title, mix):
        self.artist = artist
        self.title = title
        self.mix = mix

    def __str__(self):
        return "%s - %s (%s)" % (self.artist, self.title, self.mix)

    def __repr__(self):
        return "Track(artist:%s, title:%s, mix:%s)" % (self.artist, self.title,
                                                       self.mix)

    def searchterm(self):
        return "%s %s %s" % (self.artist, self.title, self.mix)

    def fetch_downloads(self):
        r = requests.get(self.VMUSICE_URL % urllib.quote(self.searchterm()))
        if r.status_code == requests.codes.not_found:
            return
        elif not r.ok:
            r.raise_for_status()

        dom = bs4.BeautifulSoup(r.content)
        for tag in dom.select("li.x-track"):
            artist = tag.span.strong.string
            if artist:
                artist = artist.strip()

            title = tag.span.strong.next_sibling.string.strip()
            if title.startswith(u"–"):
                title = title[1:].strip()

            url = tag.find("a", class_="download").get("href")
            duration = self.parse_duration(tag.em.string)
            yield Download(self, artist, title, duration, url, r.url)

    def download(self, destination, progressbar):
        progressbar = progressbar.add_progressbar(str(self))

        downloads = list(self.fetch_downloads())
        best = Download.pick_best(downloads)
        if best:
            best.download(destination, progressbar)
        else:
            progressbar.error("No suitable download available")

    @classmethod
    def parse_duration(cls, string):
        match = cls.DURATION_PATTERN.search(string)
        return (int(match.group(2)) * 3600 if match.group(1) else 0 +
                int(match.group(3)) * 60 +
                int(match.group(4)))


class Download(object):
    CHUNK_SIZE = 1024

    def __init__(self, track, artist, title, duration, url, referer):
        self.track = track
        self.artist = artist
        self.title = title
        self.duration = duration
        self.url = url
        self.referer = referer

    def score(self):
        return abs(8 * 60 - self.duration)

    def download(self, destination, progressbar):
        r = requests.get(self.url, headers={'referer': self.referer},
                         stream=True)
        if not r.ok:
            progressbar.error("Download failed with code %d" % r.status_code)
            return

        size = int(r.headers.get("content-length", 0))

        if not size:
            progressbar.no_progress("Downloading (Unknown Size)")
        else:
            progressbar.state = ("Starting downloading (%s)" %
                                  humanize.naturalsize(size))

        progress = 0

        with open(os.path.join(destination, "%s.mp3" % self.track), "w") as f:
            for chunk in r.iter_content(self.CHUNK_SIZE):
                f.write(chunk)
                progress += self.CHUNK_SIZE
                if size:
                    progressbar.progress = progress / float(size)
                    progressbar.state = (
                        "Downloading (%s / %s)" %
                        (humanize.naturalsize(progress),
                         humanize.naturalsize(size))
                    )

        progressbar.done("Download complete (%s)" %
                          humanize.naturalsize(size))

    def __repr__(self):
        return ("%s - %s (%d:%d)" % (
            self.artist, self.title, self.duration // 60, self.duration % 60)
        ).encode("utf-8")

    @classmethod
    def pick_best(cls, downloads):
        if not downloads:
            return None
        best = sorted(downloads, key=lambda t: t.score(), reverse=True)[0]
        return best if best.duration >= 4 * 60 else None

    @staticmethod
    def download_progress(progress, total):
        return "%s/%s" % (humanize.naturalsize(progress),
                          humanize.naturalsize(total))


def main():
    if len(sys.argv) >= 2:
        playlist = Playlist(sys.argv[1])
        playlist.download(os.path.join(os.getenv("HOME"), "Downloads"))
    else:
        print "Usage: mentalxr playlist-url"
        sys.exit(1)


if __name__ == "__main__":
    main()
