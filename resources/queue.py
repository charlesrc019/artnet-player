# Import modules.
import tornado.options
import sqlite3
import logging
import subprocess
import datetime
import concurrent
import time
import os

class Queue:

    def __init__(self, ola):
        self.ola = ola
        self.watchdog_active = False
        try:
            self.conn = sqlite3.connect(":memory:", isolation_level = None)
            #self.conn.set_trace_callback(print)
            curs = self.conn.cursor()
            curs.execute(
                """
                    create table QUEUE (
                        POSITION integer not null,
                        UUID text not null,
                        NAME text not null,
                        CONFIGURATION_NAME text not null,
                        SECONDS integer not null,
                        IS_LOOPED integer not null
                    );  
                """.replace("    ","").replace("\n", " ")[1:]
            )
            curs.close()
        except:
            raise Exception("Unable to initialize queue.")
        tornado.ioloop.PeriodicCallback(self.watchdog, 100).start()

    def watchdog(self):
        if self.watchdog_active:
            ola_status = self.ola.status()["status"]

            # Simple switch if we are now free to play.
            if ola_status == "free":
                try:
                    curs = self.conn.cursor()

                    # Check if looped.
                    is_looped = False
                    curs.execute("select IS_LOOPED from QUEUE where POSITION = 0;")
                    tmp = curs.fetchone()
                    if tmp is not None:
                        is_looped = bool(int(tmp[0]))

                    # Move forward if not looped.
                    if not is_looped:
                        curs.execute("delete from QUEUE where POSITION = 0;")
                        curs.execute("select count(*) from QUEUE;")
                        tmp = curs.fetchone()
                        if (tmp is None) or (int(tmp[0]) == 0): # special case to turn off watchdog if empty
                            self.watchdog_active = False
                            return
                        #curs.execute("select * from QUEUE;")

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

                rec_name = tmp[0]
                if is_looped:
                    rec_name += " (Looped)"
                details = {
                    "name": rec_name,
                    "identifier": tmp[1],
                    "configuration": tmp[2],
                    "total_secs": tmp[3]
                }
                self.ola.play(details)

