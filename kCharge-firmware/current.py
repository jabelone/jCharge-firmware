from machine import I2C, Pin


class CurrentSensors:
    def __init__(self, channels, shunt_value=0.01):
        """[Initialise a current sensor object.]

        Args:
            channels ([type]): [Main channels object.]
            shunt_value (float, optional): [Value in ohms of shunt resistor.]. Defaults to 0.01.
        """
        self.channels = channels
        self._shunt_value = shunt_value

        self.bus = I2C(1, scl=Pin(22), sda=Pin(21))
        self.devices = self.bus.scan()
        print("Found {} sensors at {}.".format(
            len(self.devices), self.devices))

    def _get_channel_bus_voltage(self, channel):
        ina_address = self.channels[channel][0]
        ina_channel = self.channels[channel][1]

        raw_bus_voltage = self.bus.readfrom_mem(
            ina_address, ina_channel * 2, 2)
        bus_voltage = int.from_bytes(raw_bus_voltage, "big")

        return bus_voltage * 0.001

    def _get_channel_shunt_voltage(self, channel):
        ina_address = self.channels[channel][0]
        ina_channel = self.channels[channel][1]

        raw_shunt_voltage = self.bus.readfrom_mem(
            ina_address, (ina_channel * 2) - 1, 2)
        shunt_voltage = int.from_bytes(raw_shunt_voltage, "big")

        return shunt_voltage * 0.005  # scaling factor of ina3221

    def get_channel_current(self, channel):
        """[Gets the current measured on the specified channel.]

        Args:
            channel ([number]): [Channel to measure.]

        Returns:
            [number]: [Current measured in mA of the channel.]
        """
        shunt_voltage = self._get_channel_shunt_voltage(channel)

        return round(shunt_voltage / self._shunt_value)  # ohms law V = IR

    def get_channel_voltage_and_current(self, channel):
        """[Returns the voltage and current of a channel.]

        Args:
            channel ([string]): [the channel number to get]

        Returns:
            [object]: [{"current": current, "voltage": voltage}]
        """
        shunt_voltage = self._get_channel_shunt_voltage(channel)
        current = round(shunt_voltage / self._shunt_value)  # ohms law V = IR
        voltage = self._get_channel_bus_voltage(
            channel) + (shunt_voltage / 1000)  # we add the shunt voltage to make up for the small voltage loss it exhibits

        return {"current": current, "voltage": voltage}
