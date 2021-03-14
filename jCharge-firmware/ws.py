import time
import json
import uwebsockets.client
from usocket import *
from machine import Timer
from leds import BLUE, OFF

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class WS:
    _ping_timeout = 2  # number of seconds to wait for a pong response before considering the websocket as disconnected

    def __init__(self, status_leds, temperature_sensors, channels, packet):
        self.socket = None
        self.ws = None
        self.connected = False
        self.status_leds = status_leds
        self.temperature_sensors = temperature_sensors
        self.channels = channels
        self.packet = packet
        self.last_pong = None
        self._ping_timer = Timer(3)

    def search_and_connect(self):
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(("0.0.0.0", 54321))
        s.setblocking(False)

        iter = 0
        going_up = True

        while True:
            try:
                packet = json.loads(s.recvfrom(4096)[0])
                if packet and packet.get("command") == "hello":
                    self.last_pong = time.time()

                    payload = packet.get("payload")
                    websocketHost = payload.get("websocketHost")
                    serverName = payload.get("serverName")

                    log.info(
                        "Connecting to {} at {}.".format(websocketHost, serverName)
                    )
                    self.ws = uwebsockets.client.connect("ws://" + websocketHost)
                    self.connected = True
                    log.info("Connected to {} at {}.".format(serverName, websocketHost))
                    return

            except:
                pass

            time.sleep(0.15)  # every 150ms we update the searching animation
            if going_up:
                self.status_leds.set_channel(4 - iter, BLUE)
                self.status_leds.set_channel(5 + iter, BLUE)
                iter += 1

                if iter > 3:  # once we get to the "top" start going back down
                    going_up = False

            else:
                iter -= 1  # this needs to be first so we decrement before writing to the LEDs
                self.status_leds.set_channel(4 - iter, OFF)
                self.status_leds.set_channel(5 + iter, OFF)

                if iter < 1:  # once we get to the "bottom" start going back up
                    going_up = True

    def send(self, message):
        if not self.connected:
            log.warn("Trying to send message while websocket is NOT connected.")
            return False

        try:
            self.ws.send(message)
            return True

        except OSError:
            # this means we probably got disconnected from the websocket so we should try to connect again
            self.connected = False
            self.search_and_connect()

    def send_ping(self):
        self.ws.send_ping()
        return True

    def recv(self):
        return self.ws.recv()


class WSDisconnect(Exception):
    """Raised when our websocket disconnects"""

    pass