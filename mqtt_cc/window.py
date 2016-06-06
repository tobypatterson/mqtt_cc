
import os
import re
import curses
import curses.textpad
import collections
import threading
import asyncio

import mqtt_cc.panel
from curses.textpad import Textbox

class Window(object):
    """
    Window absraction with border
    """
    win = box = None
    panel = None
    title = None

    def __init__(self, lines, cols, y, x, title="None"):

        self.title = title

        # Border
        self.box = curses.newwin(lines, cols, y, x)
        Y, X = self.box.getmaxyx()
        self.box.box()

        # Inner window
        Y, X = self.box.getmaxyx()
        self.win = self.box.subwin(Y-2, X-3, y+1, x+2)
        self.win.scrollok(True)
        self.win.keypad(True)

        if self.title:
            self.box.addstr( 0, 3, self.title )


    def _coord(self, y, x):
        self.win.addstr(y, x, '+ {} {}'.format(y, x))

    def display(self):
        self.win.erase()
        self.box.erase()
        self.box.box()
        # TODO: the title doesn't show up the first time
        if self.title:
            self.box.addstr(0, 3, self.title)

    def freshen(self):
        self.box.noutrefresh()
        self.win.noutrefresh()

    def printstr(self, text='', success=False, wow=False, warn=False, error=False):
        string = '{}\n'.format(text)
        if error:
            self.win.addstr(string, curses.A_BOLD | curses.color_pair(1))
        elif success:
            self.win.addstr(string, curses.color_pair(2))
        elif warn:
            self.win.addstr(string, curses.color_pair(3))
        elif wow:
            self.win.addstr(string, curses.A_STANDOUT)
        else:
            self.win.addstr(string)
        # Display immediately
        self.freshen()
        self.panel.update()


class PopupWindow(Window):
    """
    Window overlay for data input
    """
    title = ' Enter a topic, then press Enter or Ctrl-G '

    # def __init__(self, *a, **kw):
    #     super(PopupWindow, self).__init__(*a, **kw)
    #     self.box.addstr(0, 1, ' Input your search string, then press Enter ')

    def get_input(self):
        self.freshen()
        self.display()

        curses.curs_set(True)

        self.panel.feedback.printstr( "inside get_input" )
        textbox = curses.textpad.Textbox(self.win)
        textbox.stripspaces = True
        textbox.edit()  # Let the user edit (until Ctrl-G is struck?)
        # textbox.do_command(chr(7))  # Control-G
        self.panel.feedback.printstr( "outside get_input" )

        curses.curs_set(False)

        return textbox.gather()  # Get resulting contents of textbox


class DetailWindow(Window):
    """
    Window with video info
    """
    topic = None

    def reset(self):
        self.topic = None

    def displayx(self):
        super(DetailWindow, self).display()

        if self.topic:
            pass
            self.printstr("display")

        self.freshen()


class ComposeWindow(DetailWindow):

    pass
