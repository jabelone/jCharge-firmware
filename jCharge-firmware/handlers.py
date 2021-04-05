
def start_action(packet, channels, ws):
    channel = packet.get("channel")
    action = packet.get("action")
    rate = packet.get("rate")
    cutoff_voltage = packet.get("cutoffVoltage")

    if action == "charge":
        pass
    elif action == "discharge":
        pass
    elif action == "dcResistance":
        pass