'''
ArtNet Playback Server
Record and playback ArtNet lighting sequences via OpenOLA and an HTTP API.

Created: 2022
Authors: charlesrc19

Copyright (c) 2022 Simplifize Consulting
'''

# Import modules.
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.options
import logging
import subprocess
import sys
import signal
import threading
import logging
import os

# Import subfiles.
from handlers.configurations import ConfigListHandler, ConfigDetailsHandler
from handlers.recordings import RecordingListHandler, RecordingDetailsHandler
from handlers.action import StatusHandler, ActionHandler
from resources.ola import OLAExecutor

# Define initial options.
tornado.options.define("port", help="port where the service can be reached", type=int, default=8080)
tornado.options.define("directory", help="directory where data is stored", type=str, default=f"{os.path.dirname(os.path.realpath(__file__))}/data")
tornado.options.define("universe", help="ArtNet universe(s) to record (comma-seperated)", type=str, default="0")
tornado.options.parse_command_line()

# Initialize IO loop.
def main():

    # Register the signal handler
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    # Configure logging.
    tornado.log.enable_pretty_logging()

    # Begin OLA connection instance.
    ola = OLAExecutor()

    # Add data directory, if not exists.
    try:
        if not os.path.exists(tornado.options.options.directory):
            os.makedirs(tornado.options.options.directory)
    except:
        raise Exception("Unable to access data folder.")
    
    # Define routes and behaviors.
    application = tornado.web.Application(
        [
            (r'/api/configurations/(.*)', ConfigDetailsHandler),
            (r'/api/configurations', ConfigListHandler),
            (r'/api/recordings/(.*)', RecordingDetailsHandler),
            (r'/api/recordings', RecordingListHandler),
            (r'/api/action', ActionHandler, {"ola": ola}),
            (r'/status', StatusHandler, {"ola": ola})
        ],
        debug=True
    )
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(tornado.options.options.port)

    # Start loop
    logging.info(f"Starting server on {tornado.options.options.port}...")
    tornado.ioloop.IOLoop.current().start()
    logging.info("Server shutting down...")

def sig_handler(sig, frame):
    io_loop = tornado.ioloop.IOLoop.instance()
    if io_loop.current()._thread_identity == threading.get_ident():
        io_loop.add_callback_from_signal(stop_tornado)
    else:
        sys.exit()

def stop_tornado():
    io_loop = tornado.ioloop.IOLoop.instance()
    io_loop.stop()

# Main.
if __name__ == "__main__":
    main()