# Import packages.
import tornado.web, tornado.escape, tornado.options
import datetime
import sqlite3
import re
import json
import traceback

class PlaybackListHandler(tornado.web.RequestHandler):

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

        # Fetch from database.
        try:
            curs = self.queue.conn.cursor()
            curs.execute(
                """
                    select 
                        NAME,
                        UUID,
                        CONFIGURATION_NAME,
                        SECONDS,
                        IS_LOOPED,
                        POSITION
                    from QUEUE
                    order by POSITION asc;
                """.replace("    ","").replace("\n", " ")[1:]
            )
            recordings = curs.fetchall()
            
            curs.close()
        except Exception as e:
            traceback.print_exc()
            raise tornado.web.HTTPError(500, f"Internal database error.")

        # Organize response.
        items  = []
        for recording in recordings:
            tmp = {
                "position": int(recording[5]),
                "name": recording[0],
                "identifier": recording[1],
                "configuration": recording[2],
                "total_secs": int(recording[3]),
                "is_looped": bool(int(recording[4]))
            }
            items.append(tmp)
        resp = {
            "active": self.queue.watchdog_active,
            "items": items
        }

        self.finish(resp)

    async def post(self):

        # Safety switch for queue modification.
        tmp = self.ola.status()["status"]
        if (tmp != "free") and (tmp != "playing"):
            raise tornado.web.HTTPError(400, f"Cannot modify queue while {tmp}.")

        # Fetch query parameters.
        try:
            identifier = self.get_argument("id")
            pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
            if not pattern.match(identifier):
                raise Exception()
            when = self.get_argument("when", "")
            if (when != "") and (when != "now") and (when != "next"):
                raise Exception()
        except Exception as e:
            raise tornado.web.HTTPError(400, "Invalid parameters.")

        # Fetch recording details.
        try:
            connection = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            cursor = connection.cursor()
            cursor.execute(
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
                """.replace("    ","").replace("\n", " ")[1:],
                (identifier,)
            )
            recording = cursor.fetchone()
            if recording is None:
                raise tornado.web.HTTPError(404, "Recording not found.")

            connection.close()
        except tornado.web.HTTPError as e:
            raise e
        except Exception as e:
            traceback.print_exc()
            raise tornado.web.HTTPError(500, f"Internal database error.")

        # Modify queue database.
        try:
            curs = self.queue.conn.cursor()

            # If marked as next, shuffle and add next.
            if when != "":
                curs.execute("update QUEUE set POSITION = POSITION + 1 where POSITION > 0;")
                position = 1

            # Fetch last position number.
            else: 
                curs.execute("select POSITION from QUEUE order by POSITION desc limit 1;")
                tmp = curs.fetchone()
                if tmp is None:
                    position = 1
                else: 
                    position = int(tmp[0]) + 1

            # Add to database.
            curs.execute(
                """
                    insert into QUEUE (POSITION, NAME, UUID, CONFIGURATION_NAME, SECONDS, IS_LOOPED)
                    values (?, ?, ?, ?, ?, 0);
                """.replace("    ","").replace("\n", " ")[1:],
                (position, recording[0], recording[1], recording[2], recording[3])
            )

            curs.close()
        except tornado.web.HTTPError as e:
            raise e
        except Exception as e:
            traceback.print_exc()
            raise tornado.web.HTTPError(500, f"Internal database error.")

        # Play now.
        if when == "now":
            self.ola.stop()

        self.queue.watchdog_active = True

        self.set_status(status_code=200)
        self.finish()

class PlaybackDetailsHandler(tornado.web.RequestHandler):

    def initialize(self, ola, queue):
        self.ola = ola
        self.queue = queue

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "*")

    async def options(self, *args):
        self.set_status(204)
        self.finish()

    async def get(self, position):
        raise tornado.web.HTTPError(400, "Only PUT and DELETE requests accepted on this endpoint.")

    async def put(self, position):

        # Safety switch for queue modification.
        tmp = self.ola.status()["status"]
        if (tmp != "free") and (tmp != "playing"):
            raise tornado.web.HTTPError(400, f"Cannot modify queue while {tmp}.")

        # Fetch query parameters.
        try:
            position = int(position)
            move = self.get_argument("position", "")
            pattern = re.compile(r"^(next|up)$")
            if (move != "") and (not pattern.match(move)):
                raise Exception()
            loop = self.get_argument("loop", "")
            pattern = re.compile(r"^(true|false)$")
            if (loop != "") and (not pattern.match(loop)):
                raise Exception()
            if (move == "") and (loop == ""):
                raise Exception()
        except Exception as e:
            raise tornado.web.HTTPError(400, "Invalid parameters.")

        # Update queue items.
        try:
            curs = self.queue.conn.cursor()

            # Verify that recording exists on the queue.
            curs.execute("select * from QUEUE where POSITION = ?;", (position,))
            tmp = curs.fetchone()
            if tmp is None:
                raise tornado.web.HTTPError(404, "Item not found.")

            # Set to play next.
            if move == "next":
                if position == 1:
                    raise tornado.web.HTTPError(400, "Item is already next in queue.")
                curs.execute("update QUEUE set POSITION = -1 where POSITION = ?;", (position,))
                curs.execute("update QUEUE set POSITION = POSITION - 1 where POSITION > ?;", (position,))
                curs.execute("update QUEUE set POSITION = POSITION + 1 where POSITION > 0;", (position,))
                curs.execute("update QUEUE set POSITION = 1 where POSITION = -1;", (position,))
            
            # Set to play sooner.
            elif move == "up":
                if position == 1:
                    raise tornado.web.HTTPError(400, "Item is already next in queue.")
                curs.execute("update QUEUE set POSITION = -1 where POSITION = ?;", (position,))
                curs.execute("update QUEUE set POSITION = ? where POSITION = ?;", (position, position - 1))
                curs.execute("update QUEUE set POSITION = ? where POSITION = -1;", (position - 1,))

            # Enable looping.
            if loop == "true":
                curs.execute("update QUEUE set IS_LOOPED = 1 where POSITION = ?;", (position,))

            # Disable looping.
            elif loop == "false":
                curs.execute("update QUEUE set IS_LOOPED = 0 where POSITION = ?;", (position,))

            curs.close()
        except tornado.web.HTTPError as e:
            raise e
        except Exception as e:
            traceback.print_exc()
            raise tornado.web.HTTPError(500, f"Internal database error.")

        self.set_status(status_code=200)
        self.finish()

    async def delete(self, position):

        # Safety switch for queue modification.
        tmp = self.ola.status()["status"]
        if (tmp != "free") and (tmp != "playing"):
            raise tornado.web.HTTPError(400, f"Cannot modify queue while {tmp}.")

        # Extract identifying information.
        try:
            position = int(position)
        except Exception as e:
            raise tornado.web.HTTPError(400, "Invalid parameters.")

        try:
            curs = self.queue.conn.cursor()

            # Verify that recording exists on the queue.
            curs.execute("select * from QUEUE where POSITION = ?;", (position,))
            tmp = curs.fetchone()
            if tmp is None:
                raise tornado.web.HTTPError(404, "Item not found.")

            # Delete item from queue.
            curs.execute("delete from QUEUE where POSITION = ?;", (position,))
            curs.execute("update QUEUE set POSITION = POSITION - 1 where POSITION > ?;", (position,))

            curs.close()
        except tornado.web.HTTPError as e:
            raise e
        except Exception as e:
            traceback.print_exc()
            raise tornado.web.HTTPError(500, f"Internal database error.")

        self.set_status(status_code=200)
        self.finish()

class PlaybackStandbyHandler(tornado.web.RequestHandler):

    def initialize(self, queue):
        self.queue = queue

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "*")

    async def options(self, *args):
        self.set_status(204)
        self.finish()

    async def get(self):

        # Use database connection.
        try:
            conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            curs = conn.cursor()

            # Return all sequences.
            curs.execute(
                f"""
                    select
                        RECORDING.NAME,
                        RECORDING.UUID,
                        RECORDING.IS_STANDBY
                    from RECORDING
                    order by RECORDING.NAME desc;
                """,
            )
            sequences = curs.fetchall()
            conn.close()

        except Exception as e:
            traceback.print_exc()
            raise tornado.web.HTTPError(500, f"Internal database error.")

        # Organize response.
        resp = {
            "standby": "",
            "sequences": [
                {
                    "name": "None",
                    "idenitifier": "none"
                }
            ]
        }
        for sequence in sequences:
            tmp = {
                "name": sequence[0],
                "idenitifier": sequence[1]
            }
            resp["sequences"].append(tmp)
            if int(sequence[2]) == 1:
                resp["standby"] = sequence[1]

        self.set_header("Content-Type", "application/json; charset=UTF-8") # tornado doesn't play nice w/ json arrays
        self.finish(json.dumps(resp))

    async def put(self):

        # Fetch query parameters.
        try:
            idenitifier = self.get_argument("id", None)
            if idenitifier is None:
                raise Exception()
        except Exception as e:
            raise tornado.web.HTTPError(400, "Invalid parameters.")

        # Use database connection.
        try:
            conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            curs = conn.cursor()

            # Return all sequences.
            curs.execute("update RECORDING set IS_STANDBY = 0;")
            if str(idenitifier) != "none":
                curs.execute("update RECORDING set IS_STANDBY = 1 where UUID = ?;", (idenitifier,))
                self.queue.watchdog_active = True
            conn.commit()
            conn.close()

        except Exception as e:
            traceback.print_exc()
            raise tornado.web.HTTPError(500, f"Internal database error.")

        self.set_status(status_code=200)
        self.finish()
