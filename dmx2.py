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
MAB = 122
BIT = 4
MTBP = 50  # Time between packets

SLEEP_TIME = 5

pulses = []

def high(duration=BIT):
    pulses.append(pig_pulse(0, DI, duration))


def low(duration=BIT):
    pulses.append(pig_pulse(DI, 0, duration))


def channel(value)
    # start (low for one bit)
    low()
    for bit in range(8):
        if 1 << bit & value:
            high()
        else:
            low()
    # stop (high for two bits)
    high(BIT * 2)


def build(values):
    # clear pulses
    del pulses[:]
    # Break (low)
    low(BREAK)
    # Mark after break (high)
    high(MAB)
    # Channel data
    for value in values:
        channel(value)
    # End of data (leave high)
    high(MTBP)


def send(values):
    pig = pi()
    # enable pins FIXME move out of Dmx
    pig.set_mode(PIN_RE, OUTPUT)
    pig.set_mode(PIN_DE, OUTPUT)
    pig.set_mode(PIN_DI, OUTPUT)

    pig.write(PIN_RE, 0)  # disable Receive Enable
    pig.write(PIN_DE, 1)  # enable Driver Enable

    pig.write(PIN_DI, 1)  # high is the rest state

    pig.wave_clear()  # clear any existing waveforms
    pig.wave_add_generic(build(values))
    wave = pig.wave_create()
 #   pig.write(PIN_DE, 0)  # enable Driver Enable
    pig.wave_send_once(wave)
  #  pig.write(PIN_DE, 1)  # disable Driver Enable


if __name__ == '__main__':
    send([0, 255, 0, 0, 0, 0, 0])
