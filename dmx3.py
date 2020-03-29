# -*- coding: utf-8 -*-
from time import sleep
import colorsys

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
            self.pig.wave_add_generic(waveform)
            wave = self.pig.wave_create()
            self.pig.wave_send_once(wave)
            print(self.channel_values)
        else:
            print(self.channel_values)

    def set(self, channel, value):
        while channel >= len(self.channel_values):
            self.channel_values.append(0)
        self.channel_values[channel] = value


class PAR:

    def __init__(self, dmx, channel):
        self.dmx = dmx
        self.channel = channel
        self.brightness = 255
        self.red = 0
        self.green = 0
        self.blue = 0
        self.hex = '#000'

    def color(self, value):
        red, green, blue = color_to_rgb(value)
        self.red = red
        self.green = green
        self.blue = blue
        self.hex = '#%02X%02X%02X' % (red, green, blue)
        self.output()

    def output(self):
        self.dmx.set(self.channel, self.brightness)
        self.dmx.set(self.channel + 1, self.red)
        self.dmx.set(self.channel + 2, self.green)
        self.dmx.set(self.channel + 3, self.blue)
        self.dmx.send()


def color_to_rgb(value):
    if value[0] == '#':
        if len(value) == 4:
            red = int(value[1], 16) * 17
            green = int(value[2], 16) * 17
            blue = int(value[3], 16) * 17
        if len(value) == 7:
            red = int(value[1: 3], 16)
            green = int(value[3: 5], 16)
            blue = int(value[5: 7], 16)
    if isinstance(value, tuple):
        red = int(value[0])
        green = int(value[1])
        blue = int(value[2])
    return red, green, blue


def sequence(p):

    values = ['#F00', '#00F']
    index = 0
    while True:
        p.color(values[index])
        print p.hex
        index += 1
        if index >= len(values):
            index = 0
        sleep(1)

def fade(p):

    def fade_value(v0, v1, steps, step, wrap=False):
        d = (v0 - v1)
        if wrap:
            if d > 0.5:
                d = 1 - d
            if d < -0.5:
                d = -(1 + d)
            value = v0 + (d / (steps - 1)) * step
            if value < 0:
                value += 1
            elif value > 1:
                value -= 1
        else:
            value = v0 + (d / (steps - 1)) * step
        #print step, d, '@@', v0, v1, value
        return value

    values = ['#00F', '#F00', '#00F']
    v0 = colorsys.rgb_to_hls(*color_to_rgb(values[0]))
    v1 = colorsys.rgb_to_hls(*color_to_rgb(values[1]))
    step = 0
    direction = 1
    bounce = True
    steps = 10
    while True:
        h = fade_value(v0[0], v1[0], steps, step, True)
        l = fade_value(v0[1], v1[1], steps, step)
        s = fade_value(v0[2], v1[2], steps, step)
        rgb = colorsys.hls_to_rgb(h, l, s)
        p.color(rgb)
        print p.hex
        step += direction
        if bounce:
            if step <=0 or step >= steps -1:
                direction = - direction
        else:
            if step < 0:
                step = steps
            if step >= steps:
                step = 0
        sleep(1)



if __name__ == '__main__':
    d = DMX()
    d.send()
    p = PAR(d, 0)
    fade(p)

#    while True:
#        data = raw_input('> ')
#        if data:
#            if data[0].lower() == 'q':
#                break
#            c, v = data.split()
#            d.set(int(c), int(v))
#        d.send()

