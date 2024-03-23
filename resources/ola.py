# Import modules.
import tornado.options
import tornado.gen
import logging
import subprocess
import datetime
import concurrent
import time
import os
import traceback

class OLA:

    def __init__(self):
        self.STALE_PATCH_THRESHOLD = 300 #secs
        self.__executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.active_task = None
        self.active_epoch = None
        self.active_details = None
        self.restart_pending = False
        
        # Initialize patching.
        self.is_output = None
        self.last_patch = 0
        self.__patch_output()

    def status(self):
        if self.__executor._work_queue.qsize() == 0:
            if self.active_epoch is not None:
                self.active_task = None
                self.active_epoch = None
                self.active_details = None
            return {"status": "free"}
        else:
            elasped_secs = 0
            if self.active_epoch is not None:
                elasped_secs = round(time.time() - self.active_epoch)
            resp = {
                "status": self.active_task,
                "details": self.active_details,
                "elasped_secs": elasped_secs
            }
            return resp

    def play(self, details):
        if self.status()["status"] == "recording":
            raise Exception("Cannot start playback. A recording is already running.")

        self.__patch_output()

        self.active_task = "playing"
        self.active_epoch = time.time()
        self.active_details = details
        
        cmd = f"ola_recorder -p {tornado.options.options.directory}/{details['configuration']}/{details['identifier']}.ola"
        logging.info(f"PLAY {details['identifier']}")
        self.__executor.submit(subprocess.run, cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.__executor.submit(subprocess.run, "sleep 0", shell=True) # add to queue for tracking

    def record(self, details):
        if self.status()["status"] != "free":
            raise Exception("Cannot start recording. Another progress already running.")

        if self.is_output:
            self.__patch_input()

        self.active_task = "recording"
        self.active_epoch = time.time()
        self.active_details = details

        cmd = f"ola_recorder -r {tornado.options.options.directory}/{details['configuration']}/{details['identifier']}.ola -u {tornado.options.options.universe}"
        logging.info(f"RECORD {details['identifier']}")
        self.__executor.submit(subprocess.run, cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.__executor.submit(subprocess.run, "sleep 0", shell=True) # add to queue for tracking

    def stop(self):

        os.system(f"kill $(ps -C ola_recorder -o pid=)") # yeah... kinda janky but couldn't find better way
        os.system(f"sleep 0")
        logging.info(f"STOP")
        
        self.active_task = None
        self.active_epoch = None
        self.active_details = None

    def __is_stale_patch(self):
        if (time.time() - self.last_patch) > self.STALE_PATCH_THRESHOLD:
            return True
        else:
            return False

    def __unpatch(self):
        os.system(f"ola_patch -d 1 -i -p 0 -u 0 --unpatch")
        os.system(f"ola_patch -d 1 -p 0 -u 0 --unpatch")
        #self.__executor.submit(subprocess.run, "sleep 0", shell=True) # add to queue for tracking; old method

    def __patch_output(self):
        if (not self.is_output) or (self.__is_stale_patch()):
            self.last_patch = time.time()
            self.__unpatch()
            os.system(f"ola_patch -d 1 -p 0 -u 0")
            self.is_output = True

    def __patch_input(self):
        if (self.is_output) or (self.__is_stale_patch()):
            self.last_patch = time.time()
            self.__unpatch()
            os.system(f"ola_patch -d 1 -i -p 0 -u 0")
            self.is_output = False

    def offline_restart(self):

        # Only one pending restart at a time.
        if self.restart_pending:
            return
        else:
            self.restart_pending = True

        # Loop until we find some free time to restart.
        while True:
            if self.active_task == "free":
                logging.info(f"OLA RESTART")
                os.system(f"service olad restart")
                os.system(f"sleep 0")
                self.restart_pending = False
                break
            else:
                tornado.gen.sleep(0.5)


