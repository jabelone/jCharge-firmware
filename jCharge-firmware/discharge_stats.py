import time
import gc


class DischargeStats:
    def __init__(self, start_temperature, start_voltage):
        self.milliamp_seconds = 0
        self.start_time = time.ticks_ms()
        self.last_stats_update = self.start_time  # last time we updated the stats

        self.start_temperature = start_temperature
        self.end_temperature = None

        self.start_voltage = start_voltage
        self.end_voltage = None

        self.data_points = []

    def __str__(self):
        return str(self.get_milliamp_hours())

    def get_milliamp_hours(self):
        return self.milliamp_seconds / 3600

    def add_stat(self, voltage, current, temperature):
        data = (
            int((time.ticks_ms() - self.start_time) / 1000),
            int(voltage * 1000),
            int(current),
            int(self.get_milliamp_hours()),
            int(temperature * 100) if temperature else None,
        )

        print("Added stats!")

        self.data_points.append(data)

    def add_current(self, current):
        t = time.ticks_ms()
        milliseconds_elapsed = t - self.last_stats_update
        self.last_stats_update = t
        self.milliamp_seconds += current * milliseconds_elapsed / 1000
