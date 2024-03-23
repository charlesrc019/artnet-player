# Import packages.
import tornado.web, tornado.escape, tornado.options
import datetime
import sqlite3
import re
import json
import os
import shutil

class ConfigListHandler(tornado.web.RequestHandler):

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

            # Fetch all configs.
            curs.execute(
                """
                    select
                        CONFIGURATION.NAME,
                        CONFIGURATION.CREATED
                    from CONFIGURATION
                    order by CONFIGURATION.CREATED asc;
                """
            )
            configs = curs.fetchall()

            conn.close()

        except:
            raise tornado.web.HTTPError(500, "Internal database error.")

        # Organize response.
        resp = []
        for config in configs:
            tmp = {
                "name": config[0],
                "created": config[1]
            }
            resp.append(tmp)

        self.set_header("Content-Type", "application/json; charset=UTF-8") # tornado doesn't play nice w/ json arrays
        self.finish(json.dumps(resp))

    async def post(self):

        # Fetch query parameters.
        try:
            name = self.get_argument("name")
            pattern = re.compile(r'^[A-Za-z0-9-_]+$')
            if not pattern.match(name):
                raise Exception()
        except:
            raise tornado.web.HTTPError(400, "Invalid parameters.")

        # Use database connection.
        try:
            conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            curs = conn.cursor()

            # Search for matching configs.
            curs.execute("select ID from CONFIGURATION where NAME = ?;", (name,))
            tmp = curs.fetchone()
            if tmp is not None:
                raise tornado.web.HTTPError(400, "Configuration already exists.")

            # Add new config type.
            curs.execute(
                """
                    insert into CONFIGURATION
                        (NAME, CREATED)
                    values (?, ?);
                """,
                (name, f"{datetime.datetime.now():%Y-%m-%d %H:%m:%S}")
            )

            conn.commit()
            conn.close()
        except tornado.web.HTTPError as e:
            raise e
        except:
            raise tornado.web.HTTPError(500, str(e)) #"Internal database error.")

        # Add new recording dir, if not exists.
        try:
            if not os.path.exists(f"{tornado.options.options.directory}/{name}"):
                os.makedirs(f"{tornado.options.options.directory}/{name}")
        except:
            raise tornado.web.HTTPError(500, "Internal recording error.")

        self.set_status(status_code=200)
        self.finish()

class ConfigDetailsHandler(tornado.web.RequestHandler):

    def initialize(self, queue):
        self.queue = queue

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "*")

    async def options(self, *args):
        self.set_status(204)
        self.finish()

    async def get(self, config):
        raise tornado.web.HTTPError(400, "Only DELETE requests accepted on this endpoint.")

    async def delete(self, config):

        # Check that it is not in the queue.
        try:
            curs = self.queue.conn.cursor()
            curs.execute("select count(*) from QUEUE where CONFIGURATION_NAME = ?;", (config,))
            tmp = curs.fetchone()
            curs.close()
        except:
            raise tornado.web.HTTPError(500, "Internal database error.")
        if int(tmp[0]) > 0:
            raise tornado.web.HTTPError(400, "Cannot delete configuraton while used in the queue.")

        # Use database connection.
        try:
            conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
            curs = conn.cursor()

            # Verify that config exists.
            curs.execute(
                """
                    select CONFIGURATION.ID 
                    from CONFIGURATION 
                    where CONFIGURATION.NAME = ?;
                """,
                (config,)
            )
            tmp = curs.fetchone()
            if tmp is None:
                raise tornado.web.HTTPError(404, "Configuration not found.")

            # Delete sequence.
            curs.execute("delete from RECORDING where CONFIGURATION_ID = ?;", (tmp[0],))
            curs.execute("delete from CONFIGURATION where ID = ?;", (tmp[0],))

            # Remove recording dir.
            shutil.rmtree(f"{tornado.options.options.directory}/{config}")

            conn.commit()
            conn.close()
        except tornado.web.HTTPError as e:
            raise e
        except Exception as e:
            print(str(e))
            raise tornado.web.HTTPError(500, "Internal database error.")
            
        self.set_status(status_code=200)
        self.finish()