import socket
import curses
import asyncio
import pyperclip
import configparser
import pprint
import datetime

from os.path import expanduser
from mqtt_cc.client import MqttClient

class BasePanel(object):
    """ Synchronous panel code """
    testing = False

    debug = True

    config  = None
    message = None
    client  = None
    topic   = None

    def __init__(self, loop, stdscr, messages, feedback, console, popup):
        self.loop = loop
        self.stdscr = stdscr
        self.messages = messages
        self.feedback = feedback
        self.console = console
        self.popup = popup

        # Recursive attributes
        messages.panel = feedback.panel = console.panel = popup.panel = self

        # Should be in window.ListWindow.__init__
        feedback.win.scrollok(True)
        feedback.reset()


        self.config = configparser.ConfigParser()

    def reset(self):
        for win in [ self.messages, self.feedback, self.console ]:
            win.display( )

    def redraw( self ):
        for win in [self.messages, self.feedback, self.console]:
            win.display()

    def display(self):
        # self.messages.display()
        self.messages.freshen()
        self.feedback.freshen()
        self.console.freshen()
        self.update()

    def update(self):
        if not self.testing:
            curses.doupdate()

    def wait_for_input(self):
        # self.cache.win.nodelay(False)
        return self.console.win.getstr()

    def view(self, key):
        # Load cache from disk
        if key == ord('L'):
            pass

    def m(self, *args, **kwargs):
        return self.feedback.printstr(*args, **kwargs)

class Panel(BasePanel):
    """ Asynchronous panel code """

    @asyncio.coroutine
    def clipboard(self):
        cprint = self.feedback.printstr
        try:
            contents = pyperclip.paste()
        except:
            contents = None
            cprint('Cannot seem to read the clipboard')
        if contents:
            contents = str(contents).strip()
            cprint('Checking clipboard: {}'.format(contents))
            yield from self.connect(contents)
        else:
            cprint('Found nothing in clipboard')

        self.message = contents

    @asyncio.coroutine
    def connect(self, url):
        self.m(url)

        pass

    @asyncio.coroutine
    def ping(self):

        if self.client and self.client.is_connected():
            r = self.client.ping()
        else:
            self.m("Not connected", warn=True)

    @asyncio.coroutine
    def send( self, message=None ):

        if message is None:
            message = self.message

        self.feedback.printstr( "Sending message")

    @asyncio.coroutine
    def connect(self, profile="default"):

        if profile is None:
            profile = "default"

        c = self.config
        home = expanduser( "~" )

        config_file = home + '/.mqtt_cc'
        c = configparser.ConfigParser( )
        c.read( config_file )

        clid = c.get(profile, 'clid', fallback=None)
        host = c.get(profile, 'host', fallback="localhost")
        port = c.getint(profile, 'port', fallback=1883)
        user = c.get(profile, 'user', fallback="guest")
        pswd = c.get(profile, 'pass', fallback="guest")

        if self.client:
            self.client.disconnect()

        if clid is None:
            clid = socket.gethostname()

        client = MqttClient(clid)

        self.m("Connecting to {host} as client {client}, user {user}".format(
            host=host,
            client=clid,
            user=user
        ))

        yield from client.connect( username=user, password=pswd, hostname=host, port=port )

        # Assign a callback
        def callback_function(data):
            pp = pprint.PrettyPrinter( indent=4 )
            mesg = pp.pformat(data)
            self.messages.printstr(mesg)

            if "timestamp" in data:
                timestamp = int(data['timestamp'])
                datetime.datetime.fromtimestamp( timestamp).strftime( '%Y-%m-%d %H:%M:%S' )

        client.print_method = callback_function

        if client.is_connected():
            self.m('Connected', success=True)
            self.client = client
        else:
            self.m('Problem connecting', warn=True)

    @asyncio.coroutine
    def subscribe(self, r):

        d = r.split(' ')
        topic = d[0]
        qos = hex(d[1]) if 1 in d else 0x01

        if not self.client or not self.client.is_connected():
            self.m("Client is not connected", error=True)
        else:
            c = self.client

            # Only one subscription at a time
            if self.topic:
                self.client.unsubscribe(self.topic)

            self.m("Subscribe to topic '{}' using {}...".format(topic, qos))
            try:
                yield from c.subscribe([
                    (topic, qos )
                ])
                self.m('Subscribed', success=True)

                #c.run()
                i = 0
                while c.is_connected( ):
                    i += 1
                    message = yield from c.deliver_message( )
                    packet = message.publish_packet
                    c.on_message( packet, i )
            except Exception as e:
                self.m(str(type(e)) + str(e), error=True)

    @asyncio.coroutine
    def unsubscribe(self, r):

        if not self.topic:
            self.m("No subscriptions", warn=True)
            return

        if self.client and self.client.is_connected():
            self.m("Unsubscribing topic {}".format(self.topic))
            self.client.unsubscribe(self.topic)
            self.m("Unsubscribed", success=True)
        else:
            self.m("No connected", warn=True)

    @asyncio.coroutine
    def disconnect(self):

        if self.client and self.client.is_connected():
            self.m( "Disconnect...")
            yield from self.client.disconnect()
            self.m("Disconnected", success=True)
        else:
            self.m("Not connected", warn=True)

    def test(self, r=None):

        if r == 'mesg':

            msg = {"memory_total": 25769803776, "cpu_system": 88586.54, "memory_available": 9971847168, "cpu_user": 242895.93, "cpu_load": 16.1, "cpu_idle": 2613568.58, "memory_free": 35233792, "memory_used": 23304474624}

            self.m('Printing a test message')
            pp = pprint.PrettyPrinter( indent=4 )
            self.messages.printstr(pp.pformat(msg))


    def terminate(self):

        if self.topic:
            yield from self.client.unsubscribe(self.topic)

        if self.client and self.client.is_connected():
            yield from self.client.disconnect()

        yield from asyncio.sleep(4)



