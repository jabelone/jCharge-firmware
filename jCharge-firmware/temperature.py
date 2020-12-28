import time
import os
import json
import machine
import onewire, ds18x20
import ubinascii
from leds import YELLOW, OFF, RED, GREEN


def convert_sensor_str(sensor):
    return ubinascii.hexlify(sensor).decode("utf8")


def convert_sensor_byte(sensor):
    return ubinascii.unhexlify(sensor)


class TemperatureSensors:
    _CALIBRATION_FILE_NAME = "temperature_calibration.json"
    TEMP_RESOLUTION = 9
    sensor_calibration = {}
    temperature_data = {}

    def __init__(self, status_leds, force_calibrate=False):
        self.status_leds = status_leds

        # the data bus is on GPIO 27
        bus_pin = machine.Pin(27)

        # create the onewire object
        self.data_bus = onewire.OneWire(bus_pin)
        self.temp_bus = ds18x20.DS18X20(self.data_bus)

        # scan for devices on the bus
        self.sensors = self.data_bus.scan()
        print("Found {} sensors on the data bus.".format(len(self.sensors)))

        for sensor in self.sensors:
            # set each sensor to 9 bit resolution for fast reading
            self.temp_bus.write_scratch(sensor, b"\x00\x00\x1f")

        # check if the calibration exists and load it if it does
        if self._CALIBRATION_FILE_NAME in os.listdir() and force_calibrate == False:
            with open(self._CALIBRATION_FILE_NAME) as json_file:
                self.sensor_calibration = json.load(json_file)
                print(
                    "Found {} sensors in the calibration file.".format(
                        len(self.sensor_calibration)
                    )
                )

                if len(self.sensor_calibration) != len(self.sensors):
                    raise RuntimeError(
                        "Sensor calibration data does not match the amount found on the bus!"
                    )

        else:
            print(
                "No temperature sensor calibration data. Calculating temperature baseline."
            )

            baseline = {}
            baseline_loops = 3  # loops to perform baseline temperature calculation

            for sensor in self.sensors:
                baseline[convert_sensor_str(sensor)] = 0

            for loop in range(baseline_loops):
                self.temp_bus.convert_temp()
                time.sleep(1)
                for sensor in self.sensors:
                    baseline[convert_sensor_str(sensor)] += self.temp_bus.read_temp(
                        sensor
                    )

            for sensor in self.sensors:
                baseline[convert_sensor_str(sensor)] /= baseline_loops

            print("Temperature baseline calculated, starting calibration.")

            for channel in range(len(self.sensors)):
                channel += 1
                ignore = []

                for sensor in self.sensor_calibration.values():
                    ignore.append(sensor)

                calibrated = self.calibrate_channel(channel, baseline, ignore)

                if calibrated:
                    self.sensor_calibration[channel] = calibrated

            with open(self._CALIBRATION_FILE_NAME, "w") as outfile:
                json.dump(self.sensor_calibration, outfile)

            print("Temperature sensors calibrated!")

    def calibrate_channel(self, channel, baseline, ignore=None):
        """[Calibrates a specific channel's temperature sensor.]

        Args:
            channel ([number]): [The channel to calibrate.]
            baseline ([number]): [The baseline temperature.]

        Returns:
            [type]: [A string of the sensor ID.]
        """
        baseline_rise = 1  # rise above baseline in degrees C required to calibrate
        max_calibration_loops = (
            20  # max times to look for the temp rise specified above per channel
        )

        if ignore:
            print("Ignoring:")
            print(ignore)
        print("Please press finger to channel {} sensor.".format(channel))
        for x in range(max_calibration_loops):
            self.temp_bus.convert_temp()
            self.status_leds.set_channel(channel, YELLOW)
            time.sleep(0.5)
            self.status_leds.set_channel(channel, OFF)
            time.sleep(0.5)

            for sensor in self.sensors:
                # if we should ignore the sensor then continue the loop
                if convert_sensor_str(sensor) in ignore:
                    continue

                temperature = self.temp_bus.read_temp(sensor)
                if temperature > baseline[convert_sensor_str(sensor)] + baseline_rise:
                    print(
                        "Channel {} complete! Mapped to {}.".format(
                            channel, convert_sensor_str(sensor)
                        )
                    )
                    self.status_leds.set_channel(channel, GREEN)
                    return convert_sensor_str(sensor)

        print("FAILED to calibrated sensor for channel {}.".format(channel))
        self.status_leds.set_channel(channel, RED)
        return None

    def get_temperature(self, channel):
        """[Returns the latest temperature read for the channel.]

        Args:
            channel ([number]): [Channel to get.]

        Returns:
            [number]: [Temperature in degrees celcius.]
        """
        try:
            sensor_id = convert_sensor_byte(self.sensor_calibration[channel])
            return self.temp_bus.read_temp(sensor_id)

        except Exception as e:
            return None

    def update_temperatures(self, blocking=False):
        """[Requests a new temperature converion/update from the sensors.]"""
        self.temp_bus.convert_temp()
        if blocking:
            time.sleep(0.75)
