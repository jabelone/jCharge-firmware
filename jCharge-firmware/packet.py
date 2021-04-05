import json
from handlers import *
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Packet:
    def __init__(self, version, id, capabilities):
        """[Parse and generate jCharge packets.]

        Args:
            version ([integer]): [Version of the jCharge protocol]
        """
        self.version = version
        self.id = id
        self.capabilities = capabilities

    def build_hello_server(self):
        payload = {
            "id": str(self.id),
            "deviceName": None,
            "deviceManufacturer": "jCharge",
            "deviceModel": "D8",
            "capabilities": self.capabilities,
        }
        return self.build_packet("HelloServer", payload)

    def build_device_status(self, payload):
        return self.build_packet("DeviceStatus", payload)

    def build_ping(self):
        payload = {}
        return self.build_packet("Ping", payload)

    def build_packet(self, command, payload):
        """Returns a string of a jCharge packet"""
        return json.dumps(
            {
                "version": self.version,
                "command": command,
                "deviceId": str(self.id),
                "payload": payload,
            }
        )

    def parse_packet(self, packet):
        """Attempts to parse a jCharge packet"""
        try:
            packet = json.loads(packet)
        except:
            return None

        if packet["version"] != 1:
            log.error(
                "Unexpected protocol version number: {}".format(packet["version"])
            )
            return None

        else:
            return packet

    def handle_packet(self, packet, channels, ws):
        """Handle a parsed packet"""

        if packet["command"] != "pong":
            log.debug("Got a {} packet!".format(packet["command"]))

        if packet["command"] == "startAction":
            start_action(packet, channels, ws)

        return True
