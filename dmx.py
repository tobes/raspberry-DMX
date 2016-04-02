# -*- coding: utf-8 -*-
# http://www.jonshouse.co.uk/rpidmx512.cgi

from threading import Thread
from time import sleep

from pigpio import pi, pulse as pig_pulse, OUTPUT

# pins

PIN_DI = 18  # Driver Input
PIN_DE = 23  # Driver output enable (high to enable)
PIN_RE = 24  # Receive output enable (low to enable)

PIN_NULL = 0

DI = 1 << PIN_DI

# timings in µ seconds

BREAK = 90
MAB = 8
BIT = 4
MTBP = 500000  # Time between packets

SLEEP_TIME = 5


class Channel(Thread):

    def __init__(self, name, value=0):
        Thread.__init__(self)
        self.name = name
        self.value = None
        self.set(value)
        self.mode = None
        self.daemon = True
        self.offset = 1
        self.cycle = False

    def set(self, value=0):
        if self.value == value:
            return

        self.value = value

        wave = []
        # start (low for one bit)
        wave.append(pig_pulse(0, DI, BIT))

        for bit in range(8, 0, -1):
            if 1 << bit & value:
                # high
                wave.append(pig_pulse(DI, 0, BIT))
            else:
                # low
                wave.append(pig_pulse(0, DI, BIT))

        # stop (high for two bits)
        wave.append(pig_pulse(DI, 0, BIT * 2))

        # save wave
        self.wave = wave

    def run(self):
        while True:
            if self.cycle:
                value = self.value
                value += self.offset
                if value > 255:
                    value = 255
                    self.offset = -1
                elif value < 0:
                    value = 0
                    self.offset = 1

                self.set(value)
            sleep(0.1)


class Effect:

    def __init__(self, channel):
        self.channel = channel


class Dmx:

    def __init__(self):

        self.channels = []
        self.pulses = []
        self.null_channel = Channel('null', 0)
        self.null_channel.start()

    def build_wave(self):
        pulses = []
        channels = self.channels
        # start

        # Break (low)
        pulses.append(pig_pulse(0, DI, BREAK))
        # Mark after break (high)
        pulses.append(pig_pulse(DI, 0, MAB))
        # Channel data
        for index in range(len(channels)):
            channel = channels[index]
            if channel:
                pulses += channel.wave
            else:
                pulses += self.null_channel.wave
        # End of data (leave high)
        pulses.append(pig_pulse(DI, 0, MTBP))
        self.pulses = pulses
        return pulses

    def add_channel(self, channel, index):
        no_channels = len(self.channels)
        if index >= no_channels - 1:
            for i in range(index + 1 - no_channels):
                self.channels.append(None)
        self.channels[index] = channel
        # start the channels thread
        channel.start()


def raspberryGPIO(dmx):
    pig = pi()
    # enable pins FIXME move out of Dmx
    pig.set_mode(PIN_RE, OUTPUT)
    pig.set_mode(PIN_DE, OUTPUT)
    pig.set_mode(PIN_DI, OUTPUT)

    pig.write(PIN_RE, 1)  # disable Receive Enable
    pig.write(PIN_DE, 0)  # enable Driver Enable

    pig.write(PIN_DI, 1)  # high is the rest state

    while True:
        pig.wave_clear()  # clear any existing waveforms
        pig.wave_add_generic(dmx.build_wave())
        wave = pig.wave_create()
        pig.write(PIN_DE, 0)  # enable Driver Enable
        pig.wave_send_once(wave)
        pig.write(PIN_DE, 1)  # disable Driver Enable
        sleep(0.1)


if __name__ == '__main__':
    dmx = Dmx()

    channel = Channel('1', 0)
    channel.cycle = True
    dmx.add_channel(channel, 1)

    channel = Channel('2', 0)
    channel.cycle = True
    dmx.add_channel(channel, 2)

    channel = Channel('3', 0)
    channel.cycle = True
    dmx.add_channel(channel, 3)

    channel = Channel('4', 0)
    channel.cycle = True
    dmx.add_channel(channel, 4)

    channel = Channel('5', 0)
    channel.cycle = True
    dmx.add_channel(channel, 5)

    channel = Channel('6', 0)
    channel.cycle = True
    dmx.add_channel(channel, 6)

    raspberryGPIO(dmx)
