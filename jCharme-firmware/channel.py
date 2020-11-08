import time
from machine import Pin
from leds import DIM_BLUE, RED

class Channel:
    def __init__(self, channel, discharge_pin, leds_object=None):
        """[Control an individual discharge channel.]

        Args:
            channel ([integer]): [Physical/logical channel number 1-8]
            discharge_pin ([integer]): [Pin number that corresponds to the MOSFET that controls discharge]
            leds_object ([Leds]): [Leds object for showing output status]
        """
        self.channel = channel
        self.discharge_pin = Pin(discharge_pin, Pin.OUT)
        self.leds = leds_object
        self.state = None

        self.stop_discharge()

    def stop_discharge(self):
        """[Stops the current discharge if underway, otherwise turns off the discharge MOSFET]
        """
        self.leds.set_channel(self.channel, DIM_BLUE)
        if self.state == "discharging":
            # TODO - implement logic to stop a discharge
            pass
        else:
            self.discharge_pin.off()

