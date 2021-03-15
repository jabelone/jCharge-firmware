import json
from leds import BLUE, OFF, YELLOW, GREEN, RED
import gc
import time

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Timers:
    def __init__(self, status_leds, temperature_sensors, ws, channels, packet):
        self.status_leds = status_leds
        self.temperature_sensors = temperature_sensors
        self.ws = ws
        self.channels = channels
        self.packet = packet
        self.leds_on = False

    def io(self, timer):
        self.leds_on = not self.leds_on
        stats = []

        if time.ticks_ms() - self.ws.last_pong > 5000:
            log.warning(
                "WSDiscconect: the last ping response was more than 5 seconds ago..."
            )
            self.ws.connected = False

        for channel in self.channels:
            channel.get_temperature()
            # add each channel's stats to the stats list
            stats.append(channel.get_stats())

            if channel.state == "empty":
                channel.set_led(BLUE, write=False)

            elif channel.state == "idle":
                channel.set_led(YELLOW, write=False)

            elif channel.state == "discharging":
                if self.leds_on:
                    channel.set_led(YELLOW, write=False)
                else:
                    channel.set_led(OFF, write=False)

            elif channel.state == "complete":
                channel.set_led(GREEN, write=False)

            elif channel.state == "error" or channel.state == "verror":
                if self.leds_on:
                    channel.set_led(RED, write=False)

                else:
                    channel.set_led(OFF, write=False)

        # update all the LEDs at once, so don't write them all after each iteration - just once at the end
        self.status_leds.write()

        # request new temperature readings for next time
        self.temperature_sensors.update_temperatures()

        stats = json.dumps({"channels": stats})

        self.ws.send(self.packet.build_device_status(stats))
        self.ws.send(self.packet.build_ping())

    def stats_collection(self, timer):
        for channel in self.channels:
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

    def debug_output(self, timer):
        debug_string = "\n"
        for channel in self.channels:
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
        log.debug(debug_string)
        log.debug("FREE RAM: " + str(gc.mem_free()))
        log.debug("Up Time: " + str(time.time()))