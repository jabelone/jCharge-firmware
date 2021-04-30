import time
import uwebsockets.client
from usocket import *
from leds import BLUE, OFF

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class WS:
    def __init__(self, status_leds, temperature_sensors, channels, packet):
        self.socket = None
        self.ws = None
        self.connected = False
        self.connecting = False
        self.status_leds = status_leds
        self.temperature_sensors = temperature_sensors
        self.channels = channels
        self.packet = packet
        self.last_pong = None

    def search_and_connect(self):
        # if self.ws:
        #     self.ws.close()

        for i in range(8):
            self.status_leds.set_channel(i, OFF)
        self.connecting = True
        log.debug("Creating socket")
        s = socket(AF_INET, SOCK_DGRAM)
        log.debug("Binding socket")
        s.bind(("0.0.0.0", 54321))
        s.setblocking(False)

        iter = 0
        going_up = True

        log.debug("Starting search")
        while True:
            received_packet = None
            try:
                received_packet = s.recvfrom(4096)[0]
            except OSError as e:
                pass

            # try to parse the received command
            received_packet = self.packet.parse_packet(received_packet)

            # if we got a valid one, then try to connect
            if received_packet and received_packet.get("command") == "hello":
                payload = received_packet.get("payload")
                websocketHost = payload.get("websocketHost")
                serverName = payload.get("serverName")

                # attempt to connect to the discovered server
                log.info("Connecting to {} at {}.".format(websocketHost, serverName))
                self.ws = uwebsockets.client.connect("ws://" + websocketHost)
                self.connected = True
                self.connecting = False

                # log we're connected, update pong time, and send the hello_server packet
                log.info(
                    "Connected to {} at {}. Sending HelloServer packet.".format(
                        serverName, websocketHost
                    )
                )
                self.send(self.packet.build_hello_server())
                self.last_pong = time.time()

                log.debug("Releasing socket")
                s.close()

                return

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
            log.warning("Trying to send MESSAGE while websocket is NOT connected.")

            # if we aren't already tring to connect, then try to
            if not self.connecting:
                log.debug("Starting search")
                self.search_and_connect()

            return False

        try:
            self.ws.send(message)
            return True

        except OSError:
            # this means we probably got disconnected from the websocket so we should try to connect again
            self.connected = False
            self.search_and_connect()

    def send_ping(self):
        if not self.connected:
            log.warning("Trying to send PING while websocket is NOT connected.")

            # if we aren't already trying to connect, then try to
            if not self.connecting:
                # log.debug("Closing connection")
                # self.ws.close()
                log.debug("Starting search")
                self.search_and_connect()

            return False

        try:
            self.ws.send_ping()
        except OSError:
            self.ws.open = False
            self.connected = False
            return None

        self.last_pong = time.time()

    def receive_packet(self):
        try:
            ws_recv = self.ws.recv()
            if ws_recv and ws_recv == "pong":
                self.last_pong = time.time()
                return
            packet = self.packet.parse_packet(ws_recv)
            return packet

        except OSError:
            # this means we probably got disconnected from the websocket so set the state to that
            self.connected = False

class WSDisconnect(Exception):
    """Raised when our websocket disconnects"""

    pass