import machine, neopixel, time

GREEN = (255, 0, 0)
RED = (0, 255, 0)
DIM_BLUE = (0, 0, 50)
BLUE = (0, 0, 255)

class Leds:
    pin = 18
    number = 8
    neopixel = None

    def __init__(self, pin=18, number=8):
        """[Initialise the LED driver]

        Args:
            pin ([type]): [The pin to drive the addressable LEDs from.]
            number ([type]): [The number of LEDs connected.]
        """
        self.pin = pin
        self.number = number

        self.neopixel = neopixel.NeoPixel(machine.Pin(self.pin), self.number)
        self.clear()

        for i in reversed(range(self.number)):
            self.neopixel[i] = (0, 0, 255)
            time.sleep(0.1)
            self.neopixel.write()

        for i in range(self.number):
            self.neopixel[i] = (0, 0, 0)
            time.sleep(0.1)
            self.neopixel.write()
        
        for i in reversed(range(self.number)):
            self.neopixel[i] = (0, 0, 50)
            time.sleep(0.1)
            self.neopixel.write()
    
    def clear(self):
        """[Set every LED to off.]
        """
        for i in range(self.number):
            self.neopixel[i] = (0, 0, 0)
        self.neopixel.write()

    def set_all(self, colour):
        """[Set every LED to the specified RGB colour.]

        Args:
            r ([integer]): [Red value 0-255]
            g ([integer]): [Green value 0-255]
            b ([integer]): [Blue value 0-255]
        """
        r, g, b = colour[0], colour[1], colour[2]

        for i in range(self.number):
            self.neopixel[i] = (r, g, b)
        self.neopixel.write()   

    def set_channel(self, channel, colour):
        """[Set the channel's LED to the specified RGB colour.]

        Args:
            channel ([integer]): [The channel to set 1-8]
            r ([tuple]): [Red, green and blue values 0-255 (r, g, b)]
        """
        r, g, b = colour[0], colour[1], colour[2]

        self.neopixel[channel-1] = (r, g, b)
        self.neopixel.write()       
