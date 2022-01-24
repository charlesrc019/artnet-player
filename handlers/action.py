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

class StatusHandler(tornado.web.RequestHandler):

    def initialize(self, ola):
        self.ola = ola

    async def get(self):
        self.finish(self.ola.status())

class ActionHandler(tornado.websocket.WebSocketHandler):

    def initialize(self, ola):
        self.ola = ola
        self.clients = set()
        self.free_sent = True
        tornado.ioloop.PeriodicCallback(self.status_updater, 1000).start()

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

    # Respond to client requests.
    async def on_message(self, message):

        try:

            event = json.loads(message)
            
            if event["trigger"] == "play":
                tornado.ioloop.IOLoop.current().spawn_callback(self.play, event)

            elif event["trigger"] == "record":
                tornado.ioloop.IOLoop.current().spawn_callback(self.record, event)

            elif event["trigger"] == "stop":
                tornado.ioloop.IOLoop.current().spawn_callback(self.stop)

            else:
                raise Exception("Invalid websocket trigger.")

        except Exception as e:
            logging.error(str(e))

    # Start OLA playback.
    async def play(self, event):

        # Fetch query parameters.
        if "input" not in event:
            raise Exception("Invalid websocket input.")

        # Use database.
        try:
            conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            curs = conn.cursor()

            # Fetch recording details.
            curs.execute(
                """
                    select 
                        RECORDING.NAME,
                        RECORDING.UUID,
                        CONFIGURATION.NAME,
                        RECORDING.SECONDS 
                    from RECORDING 
                    join CONFIGURATION 
                        on RECORDING.CONFIGURATION_ID = CONFIGURATION.ID 
                    where RECORDING.UUID = ?;
                """,
                (event["input"],)
            )
            tmp = curs.fetchone()
            if tmp is None:
                raise Exception("Recording not found.")

            conn.close()
        except:
            raise Exception("Internal database error.")

        # Send playback instructions to OLA.
        details = {
            "name": tmp[0],
            "identifier": tmp[1],
            "configuration": tmp[2],
            "total_secs": tmp[3]
        }
        self.ola.play(details)

    # Start OLA recording.
    def record(self, event):

        # Fetch query parameters.
        pattern = re.compile(r'^[A-Za-z0-9-_]+$')
        if ("input" not in event) or (not pattern.match(event["input"])):
            raise Exception("Invalid websocket input.")

        # Generate and save new record information.
        idenitifier = str(uuid.uuid4())
        try:
            conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            curs = conn.cursor()

            # Confirm that configuration exists.
            curs.execute("select ID from CONFIGURATION where NAME = ?;", (event["input"],))
            tmp = curs.fetchone()
            if tmp is None:
                raise Exception("Configuration not found.")

            # Add new recording dir, if not exists.
            try:
                if not os.path.exists(f"{tornado.options.options.directory}/{event['input']}"):
                    os.makedirs(f"{tornado.options.options.directory}/{event['input']}")
            except:
                raise Exception("Unable to record to folder.")

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

        except:
            raise Exception("Internal database error.")

        # Send recording insturctions to OLA.
        details = {
            "name": name,
            "identifier": idenitifier,
            "configuration": event["input"],
            "total_secs": None
        }
        self.ola.record(details)

    # Stop OLA actions.
    def stop(self):
        canceled_task = self.ola.active_task
        canceled_details = self.ola.active_details

        self.ola.stop()

        # If we just ended recording, do the finish-up.
        if canceled_task == "recording":
            try:
                conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
                curs = conn.cursor()
                curs.execute("select SECONDS from RECORDING where UUID = ?;", (canceled_details["identifier"],))
                tmp = curs.fetchone()
                total_secs = round(time.time() - int(tmp[0]))
                curs.execute("update RECORDING set SECONDS = ?, IN_PROGRESS = 0 where UUID = ?;", (total_secs, canceled_details["identifier"],))
                conn.commit()
                conn.close()
            except:
                raise Exception("Internal database error.")


