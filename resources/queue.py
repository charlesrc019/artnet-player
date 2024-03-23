# Import modules.
import tornado.options
import sqlite3
import logging
import subprocess
import datetime
import concurrent
import time
import os
import traceback

class Queue:

    def __init__(self, ola):
        self.ola = ola
        self.watchdog_active = False
        self.changed_alert = False
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
        except Exception as e:
            raise Exception("Unable to initialize queue.")
        tornado.ioloop.PeriodicCallback(self.watchdog, 500).start()

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

                        # Process if queue is empty.
                        if (tmp is None) or (int(tmp[0]) == 0): 

                            # Look for standby.
                            try:
                                recs_conn = sqlite3.connect(f"{tornado.options.options.directory}/metadata.db")
                                recs_curs = recs_conn.cursor()
                                recs_curs.execute(
                                    """
                                        select
                                            RECORDING.NAME,
                                            RECORDING.UUID,
                                            CONFIGURATION.NAME,
                                            RECORDING.SECONDS
                                        from RECORDING
                                        join CONFIGURATION 
                                            on RECORDING.CONFIGURATION_ID = CONFIGURATION.ID 
                                        where RECORDING.IS_STANDBY = 1;
                                    """
                                )
                                tmp = recs_curs.fetchone()
                                recs_conn.close()
                            except Exception as e:
                                traceback.print_exc()
                                raise tornado.web.HTTPError(500, f"Internal database error.")

                            # We found a standby.
                            if tmp is not None:
                                tmp = list(tmp)
                                tmp[0] = tmp[0] + " (Standby)"
                            
                            # Turn off watchdog if empty.
                            else:
                                self.watchdog_active = False 
                                return

                        # Process next song if not empty.
                        else:
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
                except Exception as e:
                    traceback.print_exc()
                    raise Exception("Internal database error.")

                rec_name = tmp[0]
                if is_looped:
                    rec_name += " (Loop)"
                details = {
                    "name": rec_name,
                    "identifier": tmp[1],
                    "configuration": tmp[2],
                    "total_secs": tmp[3]
                }
                self.ola.play(details)
                self.changed_alert = True

