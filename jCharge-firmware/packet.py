import json


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
            "id": self.id,
            "deviceName": None,
            "deviceManufacturer": "jCharge",
            "deviceModel": "D8",
            "capabilities": self.capabilities,
        }
        return self.build_packet("HelloServer", payload)

    def build_packet(self, command, payload):
        return json.dumps(
            {"version": self.version, "command": command, "payload": payload}
        )
