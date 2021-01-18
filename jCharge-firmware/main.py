# This is your main script.
import time
from temperature import TemperatureSensors
from leds import Leds, BLUE, OFF, YELLOW, GREEN, RED
from channel import Channel
from current import CurrentSensors
from packet import Packet
import network
import ubinascii
from machine import Timer, reset
import gc
import json
from usocket import *
import uwebsockets.client

# define some constants here
CELL_DETECTION_THRESHOLD = 1  # in volts
MAX_CELL_VOLTAGE = 4.25  # in volts

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

status_leds = Leds()
channels = list()

current_sensors = CurrentSensors(current_sensor_configuration)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

if not wlan.isconnected():
    print("connecting to WiFi...")
    wlan.connect("Bill Wi The Science Fi", "225261007622")
    while not wlan.isconnected():
        time.sleep(0.25)
        status_leds.set_channel(4, OFF)
        status_leds.set_channel(5, BLUE)
        time.sleep(0.25)
        status_leds.set_channel(4, BLUE)
        status_leds.set_channel(5, OFF)

status_leds.set_channel(4, OFF)
status_leds.set_channel(5, OFF)

DEVICE_ID = str(ubinascii.hexlify(wlan.config("mac")))
CAPABILITIES = {
    "channels": 8,
    "charge": False,
    "discharge": True,
    "configurableChargeCurrent": False,
    "configurableDischargeCurrent": False,
    "configurableChargeVoltage": False,
    "configurableDischargeVoltage": True,
}

print("Device IP:", wlan.ifconfig()[0])
print("Device ID: " + DEVICE_ID)
print("Searching for jCharge server...")

packet = Packet(1, DEVICE_ID, CAPABILITIES)

s = socket(AF_INET, SOCK_DGRAM)
s.bind(("0.0.0.0", 54321))
payload = None

while True:
    payload = s.recvfrom(4096)[0]

    try:
        payload = json.loads(payload)

    except:
        pass

    if payload.get("command") == "hello":
        break


print(
    "Connecting to {} at {}.".format(
        payload["payload"]["serverName"], payload["payload"]["serverHost"]
    )
)
websocket = uwebsockets.client.connect("ws://" + payload["payload"]["serverHost"])
websocket.send(packet.build_hello_server())
# resp = websocket.recv()
# print(resp)

temperature_sensors = TemperatureSensors(status_leds)

for x in range(len(channel_pins)):
    channels.append(
        Channel(
            x + 1, channel_pins[x], status_leds, temperature_sensors, current_sensors
        )
    )

leds_on = True

channels[0].update_temperatures()
time.sleep(0.75)

for channel in channels:
    channel.get_temperature()


def io_timer_handler(timer):
    global leds_on
    leds_on = not leds_on
    for channel in channels:
        channel.get_temperature()
        if channel.state == "empty":
            channel.set_led(BLUE, write=False)

        elif channel.state == "idle":
            channel.set_led(YELLOW, write=False)

        elif channel.state == "discharging":
            if leds_on:
                channel.set_led(YELLOW, write=False)
            else:
                channel.set_led(OFF, write=False)

        elif channel.state == "complete":
            channel.set_led(GREEN, write=False)

        elif channel.state == "error" or channel.state == "verror":
            if leds_on:
                channel.set_led(RED, write=False)

            else:
                channel.set_led(OFF, write=False)

    # we're updating all the LEDs at once, so don't write them all at the same time - just once at the end
    status_leds.write()

    # get new temp readings too
    temperature_sensors.update_temperatures()


def stats_collection_handler(timer):
    for channel in channels:
        if channel.state == "discharging":
            c = (
                channel.voltage_and_current["current"]
                if channel.voltage_and_current
                else 0
            )
            v = (
                round(channel.voltage_and_current["voltage"], 2)
                if channel.voltage_and_current
                else 0
            )
            t = channel.temperature if channel.temperature else 0

            channel.discharge_stats.add_stat(
                v,
                c,
                t,
            )


def debug_output_handler(timer):
    debug_string = ""
    for channel in channels:
        voltage_and_current = channel.voltage_and_current
        v = voltage_and_current["voltage"]
        c = voltage_and_current["current"]
        t = channel.temperature

        debug_string += "{} | Capacity: {}mAh | Current: {}mA | Voltage: {}v | Temp: {}C | State: {} \n".format(
            channel.channel,
            round(channel.discharge_stats.get_milliamp_hours(), 1)
            if channel.discharge_stats
            else 0,
            c,
            v,
            t,
            channel.state,
        )
    gc.collect()
    # print(chr(27) + "[2J")
    print(debug_string)
    print("FREE RAM: " + str(gc.mem_free()))
    print("Up Time: " + str(time.time()))


io_timer = Timer(0)
io_timer.init(period=500, mode=Timer.PERIODIC, callback=io_timer_handler)

stats_collection_timer = Timer(1)
stats_collection_timer.init(
    period=30000, mode=Timer.PERIODIC, callback=stats_collection_handler
)

debug_output_timer = Timer(2)
debug_output_timer.init(period=5000, mode=Timer.PERIODIC, callback=debug_output_handler)

print("FINISHED SETUP")

try:
    while True:
        for channel in channels:
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
                    print(
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
                    channel.send_stats()
                    channel.set_complete()

                # if the temp gets too high
                if t and t > channel.temperature_cutoff:
                    channel.stop_discharge()
                    channel.send_stats()
                    channel.set_error()
                    # TODO: send message indicating over temperature error

except Exception as e:
    for channel in channels:
        channel.discharge_pin.off()
    io_timer.deinit()
    debug_output_timer.deinit()
    stats_collection_timer.deinit()
    status_leds.set_all(RED)
    time.sleep(0.1)
    raise (e)
