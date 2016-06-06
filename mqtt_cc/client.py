# @see http://stackoverflow.com/questions/31899679/handling-async-in-python
# @see http://hbmqtt.readthedocs.io/en/latest/references/mqttclient.html

import json, decimal, time
import asyncio
from hbmqtt.client import MQTTClient


class MqttClient( MQTTClient ):

    print_method = print
    connected = False

    @asyncio.coroutine
    def run( self ):

        i = 0
        self.print_method('hi')
        while self.is_connected():
            i += 1
            self.print_method(i)
            message = yield from self.deliver_message( )
            packet = message.publish_packet
            self.on_message(packet, i)

    def is_connected(self):
        return self.session.transitions.is_connected()

    def on_message( self, packet, i=None ):

        topic, payload = (packet.variable_header.topic_name, packet.payload.data)
        try:
            parts = topic.split( '/' )
            data = json.loads( str( payload, 'utf-8' ), parse_float=decimal.Decimal )

            if type( data ) is not dict:
                raise ("received a %s when expecting a dictionary" % type( data ))

            # User may have sent an explicit timestamp
            timestamp = data[ "timestamp" ] if "timestamp" in data else time.time()

            mesg = {
                'received_at': int( timestamp ), 'location': parts[ 0 ], 'gateway': parts[ 1 ], 'device': parts[ 2 ],
                'data': data
            }

            self.print_method( mesg )

        except Exception as e:
            self.print_method(e)

    @asyncio.coroutine
    def connect(self, hostname, username=None, password=None, port=1883):

        uri = 'mqtt://{username}:{password}@{hostname}:{port}/'.format(
            username=username,
            port=port,
            hostname=hostname,
            password=password
        )

        yield from super().connect( uri=uri)





