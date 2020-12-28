import time
from machine import Pin
from discharge_stats import DischargeStats


class Channel:
    def __init__(
        self,
        channel,
        discharge_pin,
        leds_object=None,
        temperature_sensors=None,
        current_sensors=None,
        low_voltage_cutoff=3.15,
        start_discharge_voltage_cutoff=3.3,
        temperature_cutoff=50,
    ):
        """[Control an individual discharge channel.]

        Args:
            channel ([integer]): [Physical/logical channel number 1-8]
            discharge_pin ([integer]): [Pin number that corresponds to the MOSFET that controls discharge]
            leds_object ([Leds]): [Leds object for showing output status]
        """
        self.channel = str(channel)
        self.low_voltage_cutoff = low_voltage_cutoff
        self.start_discharge_voltage_cutoff = start_discharge_voltage_cutoff
        self.temperature_cutoff = temperature_cutoff
        self.discharge_pin = Pin(discharge_pin, Pin.OUT)
        self.leds = leds_object
        self.temperature_sensors = temperature_sensors
        self.current_sensors = current_sensors
        self.state = "empty"
        self.led_state = 0
        self.discharge_stats = None

        voltage_and_current = self.get_voltage_and_current()
        self.voltage_and_current = voltage_and_current

        self.discharge_pin.off()

    def __str__(self):
        return self.channel

    def update_temperatures(self):
        self.temperature_sensors.temp_bus.convert_temp()

    def cell_removed(self):
        """[A cell was removed from the channel]"""
        self.stop_discharge()
        self.set_empty()

    def cell_inserted(self):
        """[A cell was inserted into the channel]"""
        self.start_discharge()
        self.set_discharging()

    def stop_discharge(self):
        """[Stops the current discharge]"""
        self.discharge_pin.off()
        self.send_stats()
        print(
            "Discharged finished at {}mAh on channel {}.".format(
                str(self.discharge_stats), self.channel
            )
        )
        self.discharge_stats = None

    def start_discharge(self):
        """[Starts the current discharge]"""
        self.discharge_stats = DischargeStats(
            self.temperature, self.voltage_and_current["voltage"]
        )
        self.discharge_pin.on()

    def send_stats(self):
        # TODO implement send stats
        pass

    def get_temperature(self):
        """[Returns the latest temperature read for the channel.]

        Returns:
            [number]: [Temperature in degrees celcius.]
        """
        self.temperature = self.temperature_sensors.get_temperature(self.channel)
        return self.temperature

    def get_current(self):
        """[Returns the current for the channel.]

        Returns:
            [number]: [Current in milliamps.]
        """
        return self.current_sensors.get_channel_current(self.channel)

    def get_voltage_and_current(self):
        """[Returns the voltage and current for the channel.]

        Returns:
            [number]: [Voltage in volts and current in milliamps.]
        """
        return self.current_sensors.get_channel_voltage_and_current(self.channel)

    def set_led(self, colour, write=True):
        self.leds.set_channel(self.channel, colour, write)

    def set_error(self):
        self.state = "error"

    def set_verror(self):
        self.state = "verror"

    def set_idle(self):
        self.state = "idle"

    def set_empty(self):
        self.state = "empty"

    def set_discharging(self):
        self.state = "discharging"

    def set_complete(self):
        self.state = "complete"
