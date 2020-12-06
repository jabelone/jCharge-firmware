# This is your main script.
import time
from temperature import TemperatureSensors
from leds import Leds
from channel import Channel
import network
from machine import I2C, Pin

num_channels = 8
channel_pins = [16, 17, 25, 32, 4, 33, 23, 5]

status_leds = Leds()
channels = list()

# wlan = network.WLAN(network.STA_IF)
# wlan.active(True)
# if not wlan.isconnected():
#     print('connecting to WiFi...')
#     wlan.connect('Bill Wi The Science Fi', '225261007622')
#     while not wlan.isconnected():
#         pass
# print('Device IP:', wlan.ifconfig()[0])
# print("Device ID: " + str(ubinascii.hexlify(wlan.config('mac') )))

temperature_sensors = TemperatureSensors(status_leds)

for x in range(num_channels):
    channels.append(Channel(x+1, channel_pins[x], status_leds, temperature_sensors))

while True:
    for channel in channels:
        channel.start_discharge()
        print("Channel {} is {} C.".format(channel, channel.get_temperature()))

    time.sleep(20)

    for channel in channels:
        channel.stop_discharge()

    time.sleep(20)

# bus = I2C(1, scl=Pin(22), sda=Pin(21))
# print(bus.scan())

# while True:
#     print("Hello, world!")
#     print(bus.scan())
#     time.sleep(1)

