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
        self.active = False
        self.skip = False
        self.last_status = ""
        try:
            self.conn = sqlite3.connect(":memory:", isolation_level = None)
            #self.conn.set_trace_callback(print)
            curs = self.conn.cursor()
            curs.execute(
                """
                    create table QUEUE (
                        POSITION integer not null unique,
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
        if self.active:
            ola_status = self.ola.status()["status"]

            # Simple switch if we are now free to play.
            if (ola_status == "free") or (self.skip):
                try:
                    curs = self.conn.cursor()

                    # Check if looped, if not skipped.
                    is_looped = False
                    if not self.skip: 
                        curs.execute("select IS_LOOPED from QUEUE where POSITION = 0;")
                        tmp = curs.fetchone()
                        if tmp is not None:
                            is_looped = bool(int(tmp[0]))
                    else:
                        self.skip = False

                    # Move forward if not looped.
                    if not is_looped:
                        curs.execute("delete from QUEUE where POSITION = 0;")
                        curs.execute("select count(*) from QUEUE;")
                        tmp = curs.fetchone()
                        if (tmp is None) or (int(tmp[0]) == 0): # special case to turn off watchdog if empty
                            self.active = False
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
                self.ola.play(details, from_queue=True)
            
            # Remove top entry if switched to manual.
            elif (self.last_status == "playing queue") and (ola_status == "playing"):
                try:
                    curs = self.conn.cursor()
                    curs.execute("delete from QUEUE where POSITION = 0;")
                    curs.close()
                except:
                    raise Exception("Internal database error.")

            # Update last status.
            self.last_status = ola_status
