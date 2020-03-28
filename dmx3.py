# -*- coding: utf-8 -*-

try:
    from pigpio import pi, pulse as pig_pulse, OUTPUT
except ImportError:
    pi = None


PORT = 50007

# pins

PIN_DI = 18  # Driver Input
PIN_DE = 23  # Driver output enable (high to enable)
PIN_RE = 24  # Receive output enable (low to enable)

PIN_NULL = 0

DI = 1 << PIN_DI

# timings in µ seconds

BREAK = 88
MAB = 8
BIT = 4
MTBP = 50  # Time between packets

SLEEP_TIME = 5


class DMX:

    def __init__(self):
        self.init_gpio()
        self.channel_values = []
        # precalculate pulses
        self.create_values()

    def init_gpio(self):
        if pi:
            pig = pi()

            pig.set_mode(PIN_RE, OUTPUT)
            pig.set_mode(PIN_DE, OUTPUT)
            pig.set_mode(PIN_DI, OUTPUT)

            pig.write(PIN_RE, 0)  # disable Receive Enable
            pig.write(PIN_DE, 1)  # enable Driver Enable

            pig.write(PIN_DI, 1)  # high is the rest state
        else:
            pig = None
        self.pig = pig

    def high(self, duration=BIT):
        if self.pig:
            return pig_pulse(0, DI, duration)
        return (1, duration)

    def low(self, duration=BIT):
        if self.pig:
            return pig_pulse(DI, 0, duration)
        return (0, duration)

    def create_values(self):
        values = []

        def create_pulse(value, bits):
            if value:
                return self.high(BIT * bits)
            else:
                return self.low(BIT * bits)

        for value in range(256):
            # start (low for one bit)
            # 8 data bits
            # stop (high for two bits)

            full_value = value << 1 | 1536
            bits = 0
            current = False
            pulses = []
            for bit in range(11):
                bit_value = bool(1 << bit & full_value)
                if bit_value == current:
                    bits += 1
                    continue
                pulses.append(create_pulse(current, bits))
                current = bit_value
                bits = 1
            pulses.append(create_pulse(current, bits))
            values.append(pulses)
        self.pulse_values = values

    def build_waveform(self):
        # clear pulses
        pulses = []
        # Break (low)
        pulses.append(self.low(BREAK))
        # Mark after break (high)
        pulses.append(self.high(MAB))
        # NULL code
        pulses += self.pulse_values[0]
        # Channel data
        for value in self.channel_values:
            pulses += self.pulse_values[value]
        # End of data (leave high)
        pulses.append(self.high(MTBP))
        return pulses

    def send(self):
        waveform = self.build_waveform()
        if self.pig:
            self.pig.wave_clear()  # clear any existing waveforms
            self.pig.wave_add_generic()
            wave = self.pig.wave_create()
            self.pig.wave_send_once(waveform)
        else:
            print(self.channel_values)

    def set(self, channel, value):
        while channel >= len(self.channel_values):
            self.channel_values.append(0)
        self.channel_values[channel] = value

if __name__ == '__main__':
    d = DMX()
    d.set(0,255)
    d.set(1,255)
    d.set(2,255)
    d.set(3,255)
    d.send()

