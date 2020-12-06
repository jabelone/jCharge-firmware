import time
from machine import Pin
from leds import BLUE, RED

class Channel:
    def __init__(self, channel, discharge_pin, leds_object=None, temperature_sensors=None):
        """[Control an individual discharge channel.]

        Args:
            channel ([integer]): [Physical/logical channel number 1-8]
            discharge_pin ([integer]): [Pin number that corresponds to the MOSFET that controls discharge]
            leds_object ([Leds]): [Leds object for showing output status]
        """
        self.channel = channel
        self.discharge_pin = Pin(discharge_pin, Pin.OUT)
        self.leds = leds_object
        self.temperature_sensors = temperature_sensors
        self.state = None

        self.stop_discharge()
    

    def __str__(self):
        return str(self.channel)


    def stop_discharge(self):
        """[Stops the current discharge if underway, otherwise turns off the discharge MOSFET]
        """
        self.leds.set_channel(self.channel, BLUE)
        if self.state == "discharging":
            # TODO - implement logic to stop a discharge
            pass
        else:
            self.discharge_pin.off()
    

    def start_discharge(self):
        """[Starts the current discharge if underway, otherwise turns on the discharge MOSFET]
        """
        self.leds.set_channel(self.channel, RED)
        if self.state == "charging":
            # TODO - implement logic to start a discharge
            pass
        else:
            self.discharge_pin.on()
    

    def get_temperature(self):
        """[Returns the latest temperature read for the channel.]

        Returns:
            [number]: [Temperature in degrees celcius.]
        """
        return self.temperature_sensors.get_temperature(str(self.channel))

