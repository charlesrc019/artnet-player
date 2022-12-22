# Import packages.
import tornado.web, tornado.escape, tornado.options
import datetime
import sqlite3
import re
import json
import os
import shutil

class RecordingListHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "*")

    async def options(self, *args):
        self.set_status(204)
        self.finish()

    async def get(self):

        # Fetch query parameters.
        try:
            query = self.get_argument("query", "")
            config = self.get_argument("config", "")
            pattern = re.compile(r"^[A-Za-z0-9-_]+$")
            if (config != "") and (not pattern.match(config)):
                raise Exception()
        except:
            raise tornado.web.HTTPError(400, "Invalid parameters.")

        # Set query parameters.
        query_sql = ""
        query_input = ()
        if query != "":
            query_sql = "and (RECORDING.NAME like ? or RECORDING.NOTES like ? or RECORDING.UUID like ?)"
            query_input = (f"%{query}%", f"%{query}%", f"%{query}%")
        config_sql = ""
        if config != "":
            config_sql = f"and CONFIGURATION_NAME = '{config}'"

        # Use database connection.
        try:
            conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            curs = conn.cursor()

            # Search for matching sequences.
            curs.execute(
                f"""
                    select
                        RECORDING.NAME,
                        RECORDING.UUID,
                        CONFIGURATION.NAME,
                        RECORDING.SECONDS,
                        RECORDING.NOTES,
                        RECORDING.CREATED
                    from RECORDING
                    join CONFIGURATION
                        on RECORDING.CONFIGURATION_ID = CONFIGURATION.ID
                    where RECORDING.IN_PROGRESS = 0
                    {query_sql}
                    {config_sql}
                    order by RECORDING.CREATED desc;
                """,
                query_input
            )
            sequences = curs.fetchall()

            conn.close()

        except:
            raise tornado.web.HTTPError(500, "Internal database error.")

        # Organize response.
        resp = []
        for sequence in sequences:
            tmp = {
                "name": sequence[0],
                "identifier": sequence[1],
                "configuration": sequence[2],
                "seconds": int(sequence[3]),
                "duration": f"{str(int(int(sequence[3]) / 60))}:{str(int(sequence[3]) % 60)}",
                "notes": sequence[4],
                "created": sequence[5]
            }
            resp.append(tmp)

        self.set_header("Content-Type", "application/json; charset=UTF-8") # tornado doesn't play nice w/ json arrays
        self.finish(json.dumps(resp))

class RecordingDetailsHandler(tornado.web.RequestHandler):

    def initialize(self, queue):
        self.queue = queue

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "*")

    async def options(self, *args):
        self.set_status(204)
        self.finish()

    async def get(self, identifier):
        raise tornado.web.HTTPError(400, "Only PUT and DELETE requests accepted on this endpoint.")

    async def put(self, identifier):

        # Fetch query parameters.
        try:
            name = self.get_argument("name", None)
            notes = self.get_argument("notes", None)
            if (name is None) and (notes is None):
                raise Exception()
        except:
            raise tornado.web.HTTPError(400, "Invalid parameters.")

        # Use database connection.
        try:
            conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            curs = conn.cursor()

            # Verify that recording exists.
            curs.execute(
                """
                    select RECORDING.ID 
                    from RECORDING 
                    where RECORDING.UUID = ? 
                """,
                (identifier,)
            )
            tmp = curs.fetchone()
            if tmp is None:
                raise tornado.web.HTTPError(404, "Recording not found.")

            # Update sequence.
            if name is not None:
                curs.execute("update RECORDING set NAME = ? where UUID = ?;", (name, identifier))
            if notes is not None:
                curs.execute("update RECORDING set NOTES = ? where UUID = ?;", (notes, identifier))

            conn.commit()
            conn.close()
        except tornado.web.HTTPError as e:
            raise e
        except:
            raise tornado.web.HTTPError(500, "Internal database error.")

        self.set_status(status_code=202)
        self.finish()

    async def delete(self, identifier):

        # Check that it is not in the queue.
        try:
            curs = self.queue.conn.cursor()
            curs.execute("select * from QUEUE where UUID = ?;", (identifier,))
            tmp = curs.fetchall()
            curs.close()
        except:
            raise tornado.web.HTTPError(500, "Internal database error.")
        if tmp is not None:
            raise tornado.web.HTTPError(400, "Cannot delete recording while it is in the queue.")

        # Use database connection.
        try:
            conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            curs = conn.cursor()

            # Verify that sequence exists.
            curs.execute(
                """
                    select CONFIGURATION.NAME 
                    from RECORDING 
                    join CONFIGURATION
                        on RECORDING.CONFIGURATION_ID = CONFIGURATION.ID
                    where RECORDING.UUID = ? ;
                """,
                (identifier,)
            )
            tmp = curs.fetchone()
            if tmp is None:
                raise tornado.web.HTTPError(404, "Recording not found.")

            # Delete sequence.
            curs.execute("delete from RECORDING where UUID = ?;", (identifier,))
            os.remove(f"{tornado.options.options.directory}/{tmp[0]}/{identifier}.ola")

            conn.commit()
            conn.close()
        except tornado.web.HTTPError as e:
            raise e
        except:
            raise tornado.web.HTTPError(500, "Internal database error.")

        self.set_status(status_code=202)
        self.finish()
