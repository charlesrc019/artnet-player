# Import packages.
import tornado.web, tornado.ioloop, tornado.escape, tornado.options, tornado.websocket
import datetime
import logging
import uuid
import sqlite3
import json
import os
import time
import re

class StatusHandler(tornado.websocket.WebSocketHandler):

    def initialize(self, ola):
        self.ola = ola
        self.clients = set()
        self.free_sent = True
        tornado.ioloop.PeriodicCallback(self.status_updater, 1000).start()

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "*")

    async def options(self, *args):
        self.set_status(204)
        self.finish()

    def check_origin(self, origin):
        return True

    def open(self):
        logging.info("New client connected.")
        self.clients.add(self)
        self.write_message(self.ola.status())

    def on_close(self):
        logging.info("Client disconnected.")
        self.clients.remove(self)

    # Periodically send a status update.
    async def status_updater(self):
        status = self.ola.status()
        if (status["status"] != "free") or (not self.free_sent):
            for client in self.clients:
                try:
                    client.write_message(json.dumps(status))
                except Exception as e:
                    print(str(e))
        if status["status"] == "free":
            self.free_sent = True
        else:
            self.free_sent = False

class RecordHandler(tornado.web.RequestHandler):

    def initialize(self, ola):
        self.ola = ola

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "*")

    async def options(self, *args):
        self.set_status(204)
        self.finish()

    async def get(self):
        raise tornado.web.HTTPError(400, "Only POST requests accepted on this endpoint.")

    async def post(self):

        # Fetch query parameters.
        try:
            config = self.get_argument("id")
            pattern = re.compile(r"^[A-Za-z0-9-_]+$")
            if not pattern.match(config):
                raise Exception()
        except:
            raise tornado.web.HTTPError(400, "Invalid parameters.")

        # Check that we aren't doing anything else.
        if self.ola.status()["status"] != "free":
            raise tornado.web.HTTPError(400, "Cannot record. Another task is in progress.")

        # Generate and save new record information.
        idenitifier = str(uuid.uuid4())
        try:
            conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            curs = conn.cursor()

            # Confirm that configuration exists.
            curs.execute("select ID from CONFIGURATION where NAME = ?;", (config,))
            tmp = curs.fetchone()
            if tmp is None:
                raise tornado.web.HTTPError(404, "Configuration not found.")

            # Add new recording dir, if not exists.
            try:
                if not os.path.exists(f"{tornado.options.options.directory}/{config}"):
                    os.makedirs(f"{tornado.options.options.directory}/{config}")
            except:
                raise tornado.web.HTTPError(500, "Internal recording error.")

            # As far as we can tell, things will go pechy when we try to record so safe to add entry.
            timestamp = f"{datetime.datetime.now():%Y-%m-%d %H:%m:%S}"
            name = f"New Recording {timestamp}"
            curs.execute(
                """
                    insert into RECORDING
                        (UUID, CONFIGURATION_ID, NAME, SECONDS, IN_PROGRESS, CREATED)
                    values (?, ?, ?, ?, 1, ?);
                """,
                (idenitifier, tmp[0], name, time.time(), timestamp)
            )

            conn.commit()
            conn.close()
        except tornado.web.HTTPError as e:
            raise e
        except:
            raise tornado.web.HTTPError(500, "Internal database error.")

        # Send recording insturctions to OLA.
        details = {
            "name": name,
            "identifier": idenitifier,
            "configuration": config,
            "total_secs": None
        }
        self.ola.record(details)

        self.set_status(status_code=202)
        self.finish()

class StopHandler(tornado.web.RequestHandler):

    def initialize(self, ola, queue):
        self.ola = ola
        self.queue = queue

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "*")

    async def options(self, *args):
        self.set_status(204)
        self.finish()

    async def get(self):
        raise tornado.web.HTTPError(400, "Only POST requests accepted on this endpoint.")

    async def post(self):
        canceled_task = self.ola.active_task
        canceled_details = self.ola.active_details

        # If currently playing a looped recording, unloop it.
        if canceled_task == "playing":
            if "Looped" in canceled_details["name"]:
                try:
                    curs = self.queue.conn.cursor()
                    curs.execute("update QUEUE set IS_LOOPED = 0 where POSTITION = 0;")
                    curs.close()
                except:
                    raise tornado.web.HTTPError(500, "Internal database error.")

        self.ola.stop()

        # If we just ended recording, do the finish-up.
        if canceled_task == "recording":
            try:

                # Check that we actually recorded something.
                is_valid = False
                with open(f"{tornado.options.options.directory}/{canceled_details['configuration']}/{canceled_details['identifier']}.ola", 'r') as file:
                    tmp = file.read().replace('\n', '')
                    if len(tmp) > 10:
                        is_valid = True

                # Use database
                conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
                curs = conn.cursor()

                # Finish saving valid recordings.
                if is_valid:
                    curs.execute("select SECONDS from RECORDING where UUID = ?;", (canceled_details["identifier"],))
                    tmp = curs.fetchone()
                    total_secs = round(time.time() - int(tmp[0]))
                    curs.execute("update RECORDING set SECONDS = ?, IN_PROGRESS = 0 where UUID = ?;", (total_secs, canceled_details["identifier"],))

                # Delete invalid recordings.
                else:
                    curs.execute("delete from RECORDING where UUID = ?;", (canceled_details["identifier"],))
                    os.remove(f"{tornado.options.options.directory}/{canceled_details['configuration']}/{canceled_details['identifier']}.ola")

                # Close database connection.
                conn.commit()
                conn.close()
            except tornado.web.HTTPError as e:
                raise e
            except:
                raise tornado.web.HTTPError(500, "Internal database error.")

            # Report error.
            if not is_valid:
                raise tornado.web.HTTPError(500, "No data recorded.")

        self.set_status(status_code=202)
        self.finish()