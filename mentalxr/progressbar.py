# -*- coding: utf8 -*-

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://www.wtfpl.net/ for more details.

import sys

import colorama
import blessings


colorama.init()


class ProgressBar(object):
    def __init__(self, parent, position, caption):
        self.parent = parent
        self.terminal = parent.terminal
        self.position = position
        self.caption = caption

        self._state = ""
        self._color = 6
        self._progress = 0

    def y(self):
        return self.parent.y() + self.position

    def redraw(self):
        if not self.parent.enabled:
            return

        self.parent.check_for_size_change()

        caption = self.caption
        state = self._state

        if len(caption) + 4 > self.terminal.width:
            caption = caption[:self.terminal.width - 4]
            state = ""
        elif len(caption) + len(state) + 5 > self.terminal.width:
            state = ""

        line = "[ "
        line += caption
        line += " " * (self.terminal.width - len(caption) - len(state) - 4)
        line += state
        line += " ]"

        if self.color and self._progress > 0:
            end = int(len(line) * self._progress)
            line = "".join((self.terminal.on_color(self._color),
                            line[:end],
                            self.terminal.normal,
                            line[end:]))

        with self.terminal.hidden_cursor():
            with self.terminal.location(0, self.y()):
                sys.stdout.write(line)

    def error(self, message):
        self._state = "Error: %s" % message
        self._progress = 1
        self._color = 1
        self.redraw()

    def no_progress(self, state=None):
        if state:
            self._state = state
        self._color = 7
        self._progress = 1
        self.redraw()

    def done(self, state=None):
        if state:
            self._state = state
        self._color = 2
        self.redraw()

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, progress):
        if self._progress == progress:
            return
        self._progress = max(0, min(1, progress))
        self.redraw()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
        self.redraw()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state
        self.redraw()


class MultiProgressBar(object):
    def __init__(self):
        self.terminal = blessings.Terminal()
        self.enabled = self.terminal.is_a_tty
        self.bars = []
        self._size = (self.terminal.width, self.terminal.height)

    def add_progressbar(self, caption):
        bar = ProgressBar(self, len(self.bars), caption)
        self.bars.append(bar)

        if self.enabled:
            sys.stdout.write("\n")
            bar.redraw()

        return bar

    def check_for_size_change(self):
        if (self.terminal.width, self.terminal.height) != self._size:
            self._size = (self.terminal.width, self.terminal.height)
            sys.stdout.write(self.terminal.clear)
            for bar in self.bars:
                bar.redraw()

    def y(self):
        return self.terminal.height - len(self.bars) - 1
