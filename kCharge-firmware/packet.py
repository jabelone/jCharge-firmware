import json
from handlers import *
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Packet:
    def __init__(self, version, id, capabilities):
        """Parse and generate kCharge packets.

        Args:
            version (integer): Version of the kCharge protocol
            id (string): Id of the device to use.
            capabilities (dictionary): A kCharge capabilities object.
        """
        self.version = version
        self.id = id
        self.capabilities = capabilities

    def build_hello_server(self):
        """Returns a valid helloServer packet.

        Returns:
            string: A valid helloServer packet
        """
        payload = {
            "id": str(self.id),
            "deviceName": None,
            "deviceManufacturer": "kCharge",
            "deviceModel": "D8",
            "capabilities": self.capabilities,
        }
        return self.build_packet("HelloServer", payload)

    def build_device_status(self, payload):
        """Returns a valid deviceStatus packet.

        Returns:
            string: A valid deviceStatus packet
        """
        return self.build_packet("DeviceStatus", payload)

    def build_ping(self):
        payload = {}
        return self.build_packet("Ping", payload)

    def build_packet(self, command, payload):
        """[summary]

        Args:
            command (string): Name of the kCharge command.
            payload ([type]): A dictionary containing the packet payload.

        Returns:
            string: A JSON encoded string of the entire packet.
        """
        return json.dumps(
            {
                "version": self.version,
                "command": command,
                "deviceId": str(self.id),
                "payload": payload,
            }
        )

    def parse_packet(self, packet):
        """Parses a kCharge packet and checks the version is valid.

        Args:
            packet (string): Raw string received from the websocket.

        Returns:
            dictionary: Returns a dictionary containing the kCharge data
        """
        try:
            packet = json.loads(packet)
        except:
            return None

        if packet["version"] != 1:
            log.error(
                "Unexpected protocol version number: {}".format(
                    packet["version"])
            )
            return None

        else:
            return packet

    def handle_packet(self, packet, channels, ws):
        """Handler that calls the appropriate method for each received kCharge packet.

        Args:
            packet (dictionary): A valid kCharge packet dictionary.
            channels (list): The main channels list.
            ws (uwebsockets client object): The websocket client object.

        Returns:
            [type]: [description]
        """

        if packet["command"] != "pong":
            log.debug("Got a {} packet!".format(packet["command"]))

        if packet["command"] == "startAction":
            start_action(packet.get("payload"), channels, ws)

        return True
