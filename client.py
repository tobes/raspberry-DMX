# Echo client program
import socket
import os
import curses

HOST = '192.168.2.101'    # The remote host
PORT = 50007              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))


def send(data):
    s.sendall(''.join(['{:02X}'.format(x) for x in data]))


def main(win):
    win.nodelay(True)
    key = ""
    while 1:
        win.clear()
        win.addstr("Detected key:")
        win.addstr(str(key))
        try:
            key = win.getkey()
            if key == os.linesep:
                break

            if key == 'a':
                send([0, 0, 0])
            if key == 'b':
                send([255, 255, 255])

        except:
            pass
    s.close()


if __name__ == '__main__':
    curses.wrapper(main)

