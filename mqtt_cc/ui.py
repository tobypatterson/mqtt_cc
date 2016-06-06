
import os
import curses
import asyncio

import mqtt_cc.panel
import mqtt_cc.window

TITLE = 'MQTT Command and Control'
VERSION = '0.1'


def async(task):
    loop.call_soon_threadsafe(asyncio.async, task)


def key_loop(stdscr, panel):

    #panel.console.printstr("Enter your commands below")
    run = True
    while run:

        # Refresh screen with each keystroke for snappy display
        stdscr.noutrefresh()
        panel.display()

        # Accept keyboard input
        b = panel.wait_for_input()
        s = b.decode()
        c, r = s.split(' ', 1) if ' ' in s else (s, None)

        if c == 'sekret':       async(panel.connect(panel.popup.get_input()))
        elif c == 'subscribe':  async(panel.subscribe(r))
        elif c == 'copy':       async(panel.clipboard())
        elif c == 'send':       async(panel.send())
        elif c == 'ping':       async(panel.ping())
        elif c == 'reset':      panel.reset()
        elif c == 'redraw':     panel.redraw()
        elif c == 'connect':    async(panel.connect(r))
        elif c == 'disconnect': async(panel.disconnect())
        elif c == 'test':       panel.test(r)
        elif c == 'help':
            panel.feedback.printstr('First connect to a topic, then load a message.  Finally, send it.', wow=True)
        elif c == '':
            # Should do something funny
            pass
        elif c == 'quit':
            panel.terminate()
            loop.stop( )
            run = False
        else:
            panel.feedback.printstr('Unknown command: {}'.format(c))
        # Show last key pressed
        # stdscr.addstr(curses.LINES-1, curses.COLS-40, 'c={}'.format(c))

def init(stdscr, hostname):

    # Setup curses
    curses.init_pair( 1, curses.COLOR_WHITE, curses.COLOR_RED )
    curses.init_pair( 2, curses.COLOR_BLACK, curses.COLOR_GREEN )
    curses.init_pair( 3, curses.COLOR_BLACK, curses.COLOR_YELLOW )
    if curses.has_colors( ):
        curses.start_color( )

    curses.echo()

    # Title bar at top
    stdscr.addstr( TITLE, curses.A_REVERSE )
    stdscr.chgat( -1, curses.A_REVERSE )
    version = 'UIv {} '.format( VERSION )
    stdscr.addstr( 0, curses.COLS - len( version ), version, curses.A_REVERSE )

    # Menu options at bottom
    menu_options = (
        ('topic', 'Change Topic'),
        ('copy', 'Copy Clipboard'),
        ('connect', 'Edit Message'),
        ('subscribe', 'Subscribe to a topic'),
        ('send', 'Send Message'),
        ('reset', 'help'),
        ('quit', 'quit'),
    )

    menu_string = 'Commands: ' + ', '.join( [ '{}'.format( k ) for k, v in menu_options ] )
    stdscr.addstr( curses.LINES - 1, 0, menu_string )

    # Create the middle three windows and the popoup
    L = curses.LINES
    C = curses.COLS
    messages = mqtt_cc.window.DetailWindow( L - 9, C // 2, 1, 0, title="Messages")
    console = mqtt_cc.window.Window( 7, C, L - 8, 0, title="Console" ) # The bottom one
    feedback = mqtt_cc.window.ComposeWindow( L - 9, C // 2, 1, C - C // 2, title="Log" )
    popup = mqtt_cc.window.PopupWindow( 3, C // 2, L // 4, C // 4 )

    # Create control panel
    control_panel = mqtt_cc.panel.Panel( loop, stdscr, messages, feedback, console, popup )

    # Enter curses keyboard event loop
    key_loop( stdscr, control_panel )

    # After the curses loop has finished we then stop the Python loop
    loop.call_soon_threadsafe( loop.stop )


def main(hostname):
    """
    Single entry point to run two event loops:

    1. Python `asyncio` event loop
    2. Curses wrapper runs init in another thread which in-turn runs `key_loop`
    """
    global loop

    # Python event loop
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_in_executor(None, curses.wrapper, *(init, hostname))
    loop.run_forever()
    loop.close()