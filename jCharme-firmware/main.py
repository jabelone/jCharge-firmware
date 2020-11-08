# This is your main script.
import time
from leds import Leds
from channel import Channel
from machine import I2C, Pin

num_channels = 8
channel_pins = [23, 33, 33, 33, 17, 16, 27, 25]

status_leds = Leds()
channels = list()

for x in range(num_channels):
    channels.append(Channel(x+1, channel_pins[x], status_leds))

bus = I2C(1, scl=Pin(22), sda=Pin(21))
print(bus.scan())

while True:
    print("Hello, world!")
    print(bus.scan())
    time.sleep(1)

