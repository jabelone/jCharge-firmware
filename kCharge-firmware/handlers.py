import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def start_action(payload, channels, ws):
    # extract all of the data that we need
    channel = payload.get("channel")
    action = payload.get("action")
    rate = payload.get("rate")
    cutoff_voltage = payload.get("cutoffVoltage")

    # start the relevant action
    if action == "charge":
        log.info("Starting CHARGE from startAction command.")

    elif action == "discharge":
        channels[channel-1].start_discharge()

    elif action == "dcResistance":
        log.info("Starting DC RESISTANCE from startAction command.")
