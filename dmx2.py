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
pig = None


def high(duration=BIT):
    return pig_pulse(0, DI, duration)


def low(duration=BIT):
    return pig_pulse(DI, 0, duration)


def create_value(value):
    # start (low for one bit)
    # 8 data bits
    # stop (high for two bits)
    out = []

    def write_pulse():
        if bits:
            if current:
                out.append(high(BIT * bits))
            else:
                out.append(low(BIT * bits))
    value = value << 1 | 1536
    bits = 0
    current = None
    for bit in range(11):
        bit_value = bool(1 << bit & value)
        if bit_value == current:
            bits += 1
            continue
        write_pulse()
        current = bit_value
        bits = 1
    write_pulse()
    return out

# precalculate pulses
pulse_values = [create_value(x) for x in range(256)]


def build_waveform(values):
    # clear pulses
    pulses = []
    # Break (low)
    pulses += low(BREAK)
    # Mark after break (high)
    pulses += high(MAB)
    # Channel data
    for value in values:
        pulses += pulse_values[value]
    # End of data (leave high)
    pulses += high(MTBP)
    return pulses


# set up gpio
if True:
    pig = pi()

    pig.set_mode(PIN_RE, OUTPUT)
    pig.set_mode(PIN_DE, OUTPUT)
    pig.set_mode(PIN_DI, OUTPUT)

    pig.write(PIN_RE, 0)  # disable Receive Enable
    pig.write(PIN_DE, 1)  # enable Driver Enable

    pig.write(PIN_DI, 1)  # high is the rest state


def send(values):
    pig.wave_clear()  # clear any existing waveforms
    pig.wave_add_generic(build_waveform(values))
    wave = pig.wave_create()
    pig.wave_send_once(wave)


class Dmx(protocol.Protocol):

    def connectionMade(self):
        print "Client Connected Detected!"
        # enable keepalive if supported
        try:
            self.transport.setTcpKeepAlive(1)
        except AttributeError:
            pass

    def connectionLost(self, reason):
        print "Client Connection Lost!"

    def dataReceived(self, data):
        data = [int(data[i:i + 2], 16) for i in range(0, len(data), 2)]
        send(data)


class DmxFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Dmx()

if __name__ == '__main__':
    setup_gpio()
    endpoints.serverFromString(reactor, "tcp:%s" % PORT).listen(DmxFactory())
    reactor.run()
