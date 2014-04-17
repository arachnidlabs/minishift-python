#!/usr/bin/env python

import argparse
import BaseHTTPServer
import daemon
import itertools
import logging
from minishift.draw import MCP2210Interface, Canvas, Minishift
import SocketServer
import threading
import urlparse


parser = argparse.ArgumentParser(description="Daemon that drives an array of minishifts.")
parser.add_argument('width', action="store", help="Width in pixels of the minishift array")
parser.add_argument('-d', '--daemonise', action="store_true", help="Run in the background")
parser.add_argument('-V', '--vid', action="store", metavar="VID", help="USB VID for USB interface", default=0x04d8)
parser.add_argument('-P', '--pid', action="store", metavar="PID", help="USB PID for USB interface", default=0xf517)
parser.add_argument('-u', '--usb', action="store_const", dest="interface", const="usb",
                    help="Use USB interface")
parser.add_argument('-p', '--port', action="store", metavar="PORT", default="8000",
                    help="Port and optional host to listen on (eg, 1234, or 0.0.0.0:1234)")


driver = None


class MinishiftDriver(threading.Thread):
    def __init__(self, ms):
        self.text = ""
        self.scroll_interval = None
        self.scroll_times = None
        self.event = threading.Event()

        self.minishift = ms
        super(MinishiftDriver, self).__init__()

    def run(self):
        while True:
            self.event.clear()
            if self.scroll_interval:
                self.do_scroll_text(self.text, self.scroll_interval, self.scroll_times)
            else:
                self.do_display_text(self.text)

    def do_scroll_text(self, text, interval, times):
        canvas = Canvas()
        canvas.write_text(0, text)

        for i in range(times) if times else itertools.count():
            for col in canvas.scroll():
                self.minishift.update(col)
                if self.event.wait(interval):
                    return

        # Scroll the text off the screen
        canvas = Canvas()
        canvas[self.minishift.width - 1] = 0
        for col in canvas.scroll():
            self.minishift.update(col)
            if self.event.wait(interval):
                return
        self.event.wait()

    def do_display_text(self, text):
        canvas = Canvas(self.minishift.width)
        try:
            canvas.write_text(0, text)
        except IndexError:
            pass
        self.minishift.update(canvas)
        self.event.wait()

    def set_text(self, text):
        self.text = text
        self.scroll_interval = None
        self.event.set()

    def scroll_text(self, text, interval, times):
        self.text = text
        self.scroll_interval = interval
        self.scroll_times = times
        self.event.set()


class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        print self.path
        url = urlparse.urlparse(self.path)
        if url.path != '/set':
            self.send_error(404)
            return

        self.set_display(url.query)
        self.send_response(200)

    def do_POST(self):
        url = urlparse.urlparse(self.path)
        if url.path != '/set':
            self.send_error(404)
            return

        try:
            self.set_display(self.rfile.read())
            self.send_response(200)
        except Exception:
            self.log.exception("While %s serving request for %s", self.command, self.path)
            self.send_response(500)

    def set_display(self, qs):
        qs = urlparse.parse_qs(qs)
        text = qs.get('text', [''])[0]
        interval = qs.get('interval', [None])[0]
        times = qs.get('times', [None])[0]
        if interval:
            driver.scroll_text(text, float(interval), int(times) if times else None)
        else:
            driver.set_text(text)


def main(args):
    global driver

    logging.basicConfig(level=logging.DEBUG)

    if args.interface == 'usb' or args.interface is None:
        interface = MCP2210Interface(int(args.vid), int(args.pid))
    else:
        raise ValueError("Unrecognised interface %s" % (args.interface, ))

    driver = MinishiftDriver(Minishift(interface, int(args.width)))
    driver.daemon = True
    driver.start()

    if ':' in args.port:
        ip, port = args.port.split(':')
    else:
        ip = ""
        port = args.port
    port = int(port)

    httpd = SocketServer.TCPServer((ip, port), RequestHandler)
    logging.info("Serving on %s", args.port)
    httpd.serve_forever()


if __name__ == '__main__':
    args = parser.parse_args()
    if args.daemonise:
        with daemon.DaemonContext():
            main(args)
    else:
        main(args)
