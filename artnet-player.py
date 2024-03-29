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
import sqlite3
import logging
import subprocess
import sys
import signal
import threading
import logging
import os
import traceback

# Import subfiles.
from handlers.configurations import ConfigListHandler, ConfigDetailsHandler
from handlers.recordings import RecordingListHandler, RecordingDetailsHandler
from handlers.actions import StatusHandler, RecordHandler, StopHandler #PlayHandler
from handlers.playback import PlaybackListHandler, PlaybackDetailsHandler, PlaybackStandbyHandler
from resources.ola import OLA
from resources.queue import Queue

# Define initial options.
tornado.options.define("port", help="port where the service can be reached", type=int, default=8080)
tornado.options.define("directory", help="directory where data is stored (no trailing backslash)", type=str, default=f"{os.path.dirname(os.path.realpath(__file__))}/data")
tornado.options.define("universe", help="ArtNet universe(s) to record (comma-seperated)", type=str, default="0")
tornado.options.parse_command_line()

# Initialize IO loop.
def main():

    # Configure logging.
    tornado.log.enable_pretty_logging()

    # Add data directory, if not exists.
    try:
        if not os.path.exists(tornado.options.options.directory):
            os.makedirs(tornado.options.options.directory)
        if not os.path.exists(f"{tornado.options.options.directory}/metadata.db"):
            with open(f"{os.path.dirname(os.path.realpath(__file__))}/resources/metadata.sql", 'r') as file:
                sql_statements = file.read().replace('\n', '').split(";")
            conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            curs = conn.cursor()
            for sql_statement in sql_statements:
                curs.execute(sql_statement)
            conn.commit()
            conn.close()
    except Exception as e:
        raise Exception("Unable to access data folder.")

    # Begin resource instances.
    ola = OLA()
    queue = Queue(ola)

    # Define routes and behaviors.
    application = tornado.web.Application(
        [
            (r'/api/configurations/(.*)', ConfigDetailsHandler, {"queue": queue}),
            (r'/api/configurations', ConfigListHandler),
            (r'/api/recordings/(.*)', RecordingDetailsHandler, {"queue": queue}),
            (r'/api/recordings', RecordingListHandler),
            (r'/api/playback/standby', PlaybackStandbyHandler, {"queue": queue}),
            (r'/api/playback/(.*)', PlaybackDetailsHandler, {"ola": ola, "queue": queue}),
            (r'/api/playback', PlaybackListHandler, {"ola": ola, "queue": queue}),
            (r'/api/record', RecordHandler, {"ola": ola}),
            #(r'/api/play', PlayHandler, {"ola": ola}),
            (r'/api/stop', StopHandler, {"ola": ola, "queue": queue}),
            (r'/api/status', StatusHandler, {"ola": ola}),
            (
                r'/(.*)',
                tornado.web.StaticFileHandler,
                {
                    "path": f"{os.path.dirname(os.path.realpath(__file__))}/dist",
                    "default_filename":"index.html"
                }
            )
        ],
        debug=False
    )
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(tornado.options.options.port)

    # Start loop
    logging.info(f"Starting server on {tornado.options.options.port}...")
    tornado.ioloop.IOLoop.current().start()
    logging.info("Server shutting down...")

# Main.
if __name__ == "__main__":
    main()
