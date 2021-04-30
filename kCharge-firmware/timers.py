import json
from leds import BLUE, OFF, YELLOW, GREEN, RED
import gc
import time
import micropython

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
        self.control_loop_last_run = time.ticks_ms()
        self.control_loop_ticks = 0

    def stats_collection(self, timer):
        def do_stats(arg):
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

        micropython.schedule(do_stats, None)

    def debug_output(self, timer):
        def do_debug(arg):
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

        micropython.schedule(do_debug, None)

    def control_loop(self, timer):
        # def do_control_loop(arg):
        # dif = time.ticks_diff(time.ticks_ms(), self.control_loop_last_run)
        self.control_loop_ticks = 0

        self.control_loop_ticks += 1
        self.control_loop_last_run = time.ticks_ms()

        # micropython.schedule(do_control_loop, None)
