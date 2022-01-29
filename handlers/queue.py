# Import packages.
import tornado.web, tornado.escape, tornado.options
import datetime
import sqlite3
import re
import json

class QueueHandler(tornado.web.RequestHandler):
    

    def initialize(self, ola, cache):
        self.ola = ola
        self.cache = cache
        if not self.cache.watchdog_running:
            tornado.ioloop.PeriodicCallback(self.watchdog, 100).start()
            self.cache.watchdog_running = True

    def watchdog(self):
        if self.cache.active:
            if self.ola.status()["status"] == "free":
                try:
                    curs = self.cache.conn.cursor()

                    # Check if looped.
                    curs.execute("select IS_LOOPED from QUEUE where POSITION = 0;")
                    tmp = curs.fetchone()
                    is_looped = False
                    if tmp is not None:
                        is_looped = bool(int(tmp[0]))

                    # Move forward if not looped.
                    if not is_looped:
                        curs.execute("delete from QUEUE where POSITION = 0;")
                        curs.execute("select count(*) from QUEUE;")
                        tmp = curs.fetchone()
                        if (tmp is None) or (int(tmp[0]) == 0): # special case to turn off watchdog if empty
                            self.cache.active = False
                            return
                        curs.execute("select * from QUEUE;")

                        while (True):
                            curs.execute("update QUEUE set POSITION = POSITION - 1;")
                            curs.execute("select NAME, UUID, CONFIGURATION_NAME, SECONDS from QUEUE where POSITION = 0;")
                            tmp = curs.fetchone()
                            if tmp is not None:
                                break

                    # Loop if enabled.
                    else:
                        curs.execute("select NAME, UUID, CONFIGURATION_NAME, SECONDS from QUEUE where POSITION = 0;")
                        tmp = curs.fetchone()

                    curs.close()
                except:
                    raise Exception("Internal database error.")

                details = {
                    "name": tmp[0],
                    "identifier": tmp[1],
                    "configuration": tmp[2],
                    "total_secs": tmp[3]
                }
                self.ola.play(details, is_queue=True)

    async def get(self):

        # Fetch from database.
        try:
            curs = self.cache.conn.cursor()
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
        except:
            raise tornado.web.HTTPError(500, "Internal database error.")

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
            "active": self.cache.active,
            "items": items
        }

        self.finish(resp)

    async def post(self):

        # Fetch query parameters.
        try:
            identifier = self.get_argument("id")
            pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
            if not pattern.match(identifier):
                raise Exception()
            is_next = False
            tmp = self.get_argument("next", "")
            if (tmp != "") and (tmp != "true"):
                raise Exception()
            if tmp == "true":
                is_next = True
        except:
            raise tornado.web.HTTPError(400, "Invalid parameters.")

        # Use database.
        try:
            connection = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            cursor = connection.cursor()

            # Fetch recording details.
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
        except:
            raise tornado.web.HTTPError(500, "Internal database error.")

        try:
            curs = self.cache.conn.cursor()

            # If marked as next, shuffle and add next.
            if is_next:
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

            # Add to queue database.
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
        except:
            raise tornado.web.HTTPError(500, "Internal database error.")


        # Automatically activate queue, if song is added to it.
        self.cache.active = True

        self.set_status(status_code=202)
        self.finish()

    async def put(self):

        # Fetch query parameters.
        try:
            new_status = self.get_argument("active", "")
            pattern = re.compile(r"^(true|false)$")
            if (new_status != "") and (not pattern.match(new_status)):
                raise Exception()
            position = self.get_argument("pos", -1)
            if (position != -1):
                position = int(position)
            move = self.get_argument("position", "")
            pattern = re.compile(r"^(next|up)$")
            if (move != "") and (not pattern.match(move)):
                raise Exception()
            loop = self.get_argument("loop", "")
            pattern = re.compile(r"^(true|false)$")
            if (loop != "") and (not pattern.match(loop)):
                raise Exception()
            if (move == "") and (loop == "") and (new_status == ""):
                raise Exception()
            if ((move != "") or (loop != "")) and (position == -1):
                raise Exception()
        except:
            raise tornado.web.HTTPError(400, "Invalid parameters.")

        # Set status.
        if new_status == "true":
            self.cache.active = True
        elif new_status == "false":
            self.cache.active = False
            try:
                curs.execute("delete from QUEUE where POSITION = 0;")
                self.cache.conn.commit()
            except:
                raise tornado.web.HTTPError(500, "Internal database error.")

        # Update queue items.
        try:
            curs = self.cache.conn.cursor()

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
        except:
            raise tornado.web.HTTPError(500, "Internal database error.")

        self.set_status(status_code=202)
        self.finish()

    async def delete(self):

        # Extract identifying information.
        try:
            position = int(self.get_argument("pos"))
        except:
            raise tornado.web.HTTPError(400, "Invalid item.")

        try:
            curs = self.cache.conn.cursor()

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
        except:
            raise tornado.web.HTTPError(500, "Internal database error.")

        self.set_status(status_code=202)
        self.finish()