# -*- coding: utf-8 -*-
# http://www.jonshouse.co.uk/rpidmx512.cgi

from twisted.internet import protocol, reactor, endpoints

from pigpio import pi, pulse as pig_pulse, OUTPUT


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

pulses = []


def high(duration=BIT):
    pulses.append(pig_pulse(0, DI, duration))


def low(duration=BIT):
    pulses.append(pig_pulse(DI, 0, duration))


def channel(value):
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


pig = pi()
# enable pins FIXME move out of Dmx
pig.set_mode(PIN_RE, OUTPUT)
pig.set_mode(PIN_DE, OUTPUT)
pig.set_mode(PIN_DI, OUTPUT)

pig.write(PIN_RE, 0)  # disable Receive Enable
pig.write(PIN_DE, 1)  # enable Driver Enable

pig.write(PIN_DI, 1)  # high is the rest state

def send(values):
    pig.wave_clear()  # clear any existing waveforms
    build(values)
    pig.wave_add_generic(pulses)
    wave = pig.wave_create()
    pig.wave_send_once(wave)


class Dmx(protocol.Protocol):

    def connectionMade(self):
        print "Client Connected Detected!"
        ### enable keepalive if supported
        try:
            self.transport.setTcpKeepAlive(1)
        except AttributeError: pass

    def connectionLost(self, reason):
        print "Client Connection Lost!"

    def dataReceived(self, data):
        data = [int(data[i:i+2], 16) for i in range(0, len(data), 2)]
        send(data)


class DmxFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Dmx()

setup_pig()
endpoints.serverFromString(reactor, "tcp:%s" % PORT).listen(DmxFactory())
reactor.run()
