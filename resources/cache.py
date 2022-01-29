# Import modules.
import tornado.options
import sqlite3
import logging
import subprocess
import datetime
import concurrent
import time
import os

class QueueCache:

    def __init__(self):
        self.active = False
        self.watchdog_running = False
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
            