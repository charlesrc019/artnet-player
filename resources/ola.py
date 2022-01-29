# Import modules.
import tornado.options
import logging
import subprocess
import datetime
import concurrent
import time
import os

class OLAExecutor:

    def __init__(self):
        self.__executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.active_task = None
        self.active_epoch = None
        self.active_details = None


    def status(self):
        if self.__executor._work_queue.qsize() == 0:
            if self.active_epoch is not None:
                self.active_task = None
                self.active_epoch = None
                self.active_details = None
            return {"status": "free"}
        else:
            elasped_secs = round(time.time() - self.active_epoch)
            resp = {
                "status": self.active_task,
                "details": self.active_details,
                "elasped_secs": elasped_secs
            }
            return resp

    def play(self, details, is_queue = False):
        if self.status()["status"] != "free":
            raise Exception("Cannot start playback. Another OLA process already running.")

        self.active_task = "playing"
        if is_queue:
            self.active_task = "playing queue"
        self.active_epoch = time.time()
        self.active_details = details
        

        cmd = f"ola_recorder -p {tornado.options.options.directory}/{details['configuration']}/{details['identifier']}.ola"
        logging.info(f"PLAY {details['identifier']}")
        self.__executor.submit(subprocess.run, cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.__executor.submit(subprocess.run, "sleep 0", shell=True) # add to queue for tracking

    def record(self, details):
        if self.status()["status"] != "free":
            raise Exception("Cannot start playback. Another OLA process already running.")

        self.active_task = "recording"
        self.active_epoch = time.time()
        self.active_details = details
        

        cmd = f"ola_recorder -r {tornado.options.options.directory}/{details['configuration']}/{details['identifier']}.ola -u {tornado.options.options.universe}"
        logging.info(f"RECORD {details['identifier']}")
        self.__executor.submit(subprocess.run, cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.__executor.submit(subprocess.run, "sleep 0", shell=True) # add to queue for tracking

    def stop(self):
        if self.status()["status"] == "free":
            raise Exception("No OLA process to stop.")

        os.system(f"kill $(ps -C ola_recorder -o pid=)") # yeah... kinda janky but couldn't find better way
        logging.info(f"STOP")
        
        self.active_task = None
        self.active_epoch = None
        self.active_details = None
        


