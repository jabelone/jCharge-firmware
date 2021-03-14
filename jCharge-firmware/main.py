# This is your main script.
import time
import machine
from temperature import TemperatureSensors
from leds import Leds, BLUE, OFF, YELLOW, GREEN, RED
from channel import Channel
from current import CurrentSensors
from packet import Packet
import network
import ubinascii
from machine import Timer
from ws import WS
from timers import Timers

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

s = None  # our global socket (for auto discovery) object

# define some constants here
CELL_DETECTION_THRESHOLD = 1  # minimum voltage to detect a cell in volts
MAX_CELL_VOLTAGE = 4.25  # maximum voltage to detect a cell in volts

# the channels equal their position in the array + 1
channel_pins = [16, 17, 25, 32, 4, 33, 23, 5]

# current sensor config in the format of channel (ina_address, ina_channel)
current_sensor_configuration = {
    "1": (64, 3),
    "2": (64, 1),
    "3": (64, 2),
    "4": (65, 3),
    "5": (65, 2),
    "6": (65, 1),
    "7": (66, 3),
    "8": (66, 2),
}

# capabilities of the hardware
CAPABILITIES = {
    "channels": 8,
    "charge": False,
    "discharge": True,
    "configurableChargeCurrent": False,
    "configurableDischargeCurrent": False,
    "configurableChargeVoltage": False,
    "configurableDischargeVoltage": True,
}


# try:
status_leds = Leds(number=CAPABILITIES["channels"])
channels = list()

current_sensors = CurrentSensors(current_sensor_configuration)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

if not wlan.isconnected():
    log.info("Connecting to WiFi...")
    wlan.connect("Bill Wi The Science Fi", "225261007622")
    # wlan.connect("HSBNEWiFi", "HSBNEPortHack")
    while not wlan.isconnected():
        time.sleep(0.25)
        status_leds.set_channel(4, OFF)
        status_leds.set_channel(5, BLUE)
        time.sleep(0.25)
        status_leds.set_channel(4, BLUE)
        status_leds.set_channel(5, OFF)

status_leds.set_channel(4, OFF)
status_leds.set_channel(5, OFF)

# get our device ID (the mac address of the WiFi radio) and initialise our jCharge packet class
DEVICE_ID = ubinascii.hexlify(wlan.config("mac")).decode("utf8")
packet = Packet(1, DEVICE_ID, CAPABILITIES)

# initialise our tempreature sensors class
temperature_sensors = TemperatureSensors(status_leds)

# initialise a channel class for each of our configured channels
for x in range(len(channel_pins)):
    channels.append(
        Channel(
            x + 1,
            channel_pins[x],
            status_leds,
            temperature_sensors,
            current_sensors,
        )
    )

log.info("Device IP: " + str(wlan.ifconfig()[0]))
log.info("Device ID: " + DEVICE_ID)
log.info("Searching for jCharge server...")

# setup our websocket class, start searching for jCharge servers and connect if we find one
ws = WS(status_leds, temperature_sensors, channels, packet)
ws.search_and_connect()
ws.send(packet.build_hello_server())  # send the hellow server packet

# request a temperature reading on the 1wire bus and wait for it to complete
channels[0].update_temperatures()
time.sleep(0.75)

# loop through each temperature sensor and retrieve it's reading, then set the channel BLUE
for channel in channels:
    channel.get_temperature()
    channel.set_led(BLUE)

# setup our timers for the io, stats collection and debug output handlers
timers = Timers(status_leds, temperature_sensors, ws, channels, packet)

io_timer = Timer(0)
io_timer.init(period=500, mode=Timer.PERIODIC, callback=timers.io)

stats_collection_timer = Timer(1)
stats_collection_timer.init(
    period=30000, mode=Timer.PERIODIC, callback=timers.stats_collection
)

debug_output_timer = Timer(2)
debug_output_timer.init(period=5000, mode=Timer.PERIODIC, callback=timers.debug_output)

log.info("FINISHED SETUP")

while True:
    for channel in channels:
        # as often as the main loop runs, update the voltage and current, and temperature readings
        voltage_and_current = channel.get_voltage_and_current()
        channel.voltage_and_current = voltage_and_current
        channel.temperature = channel.get_temperature()

        v = voltage_and_current["voltage"]
        c = voltage_and_current["current"]
        t = channel.temperature

        if channel.state == "empty":
            # if the voltage is above the min required to start discharging and below threshold
            if v > channel.start_discharge_voltage_cutoff and v < MAX_CELL_VOLTAGE:
                channel.cell_inserted()

            # if the voltage is outside that range but above the cell detection threshold then set an error state
            elif v > CELL_DETECTION_THRESHOLD:
                channel.set_verror()
                log.info(
                    "Detected cell in channel {} that is out of voltage range ({}).".format(
                        channel.channel, v
                    )
                )

        elif channel.state == "verror":
            # if the cell is removed or the dodgy connection fixes itself (ie cell finished being inserted)
            if (
                v < CELL_DETECTION_THRESHOLD
                or v > channel.start_discharge_voltage_cutoff
            ):
                channel.set_empty()

        elif channel.state == "error" or channel.state == "complete":
            # if the cell is removed
            if v < CELL_DETECTION_THRESHOLD:
                channel.set_empty()

        elif channel.state == "discharging":
            channel.discharge_stats.add_current(
                c,
            )
            # if we're discharging and the voltage gets to the lvc stop the discharge
            if v < channel.low_voltage_cutoff:
                channel.stop_discharge()
                # channel.send_stats() # TODO: implement
                channel.set_complete()

            # if the temp gets too high
            if t and t > channel.temperature_cutoff:
                channel.stop_discharge()
                # channel.send_stats() # TODO: implement
                channel.set_error()
                # TODO: send message indicating over temperature error

# except Exception as e:
#     # if we hit any unhandled exceptions, shut everything down, kill the timers, and set the LEDs red for 1s. Then reset the board.
#     for channel in channels:
#         channel.discharge_pin.off()
#     Timer(0).deinit()
#     Timer(1).deinit()
#     Timer(2).deinit()
#     status_leds.set_all(RED)
#     time.sleep(1)
#     machine.reset()