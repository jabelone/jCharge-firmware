import machine, neopixel, time

GREEN = (0, 10, 0)
RED = (10, 0, 0)
BLUE = (0, 0, 10)
YELLOW = (24, 16, 0)
OFF = (0, 0, 0)

class Leds:
    neopixel = None

    def __init__(self, pin=26, number=8):
        """[Initialise the LED driver]

        Args:
            pin ([type]): [The pin to drive the addressable LEDs from.]
            number ([type]): [The number of LEDs connected.]
        """
        self.pin = pin
        self.number = number

        self.leds = neopixel.NeoPixel(machine.Pin(self.pin), self.number)
        self.clear()

        for i in range(self.number):
            self.leds[i] = BLUE
            time.sleep(0.1)
            self.leds.write()

        for i in reversed(range(self.number)):
            self.leds[i] = OFF
            time.sleep(0.1)
            self.leds.write()
        
        for i in range(self.number):
            self.leds[i] = BLUE
            time.sleep(0.1)
            self.leds.write()
    
    def clear(self):
        """[Set every LED to off.]
        """
        for i in range(self.number):
            self.leds[i] = OFF
        self.leds.write()

    def set_all(self, colour):
        """[Set every LED to the specified RGB colour.]

        Args:
            r ([integer]): [Red value 0-255]
            g ([integer]): [Green value 0-255]
            b ([integer]): [Blue value 0-255]
        """
        r, g, b = colour[0], colour[1], colour[2]

        for i in range(self.number):
            self.leds[i] = (r, g, b)
        self.leds.write()   

    def set_channel(self, channel, colour):
        """[Set the channel's LED to the specified RGB colour.]

        Args:
            channel ([integer]): [The channel to set 1-8]
            r ([tuple]): [Red, green and blue values 0-255 (r, g, b)]
        """
        self.leds[channel-1] = colour
        self.leds.write()       
