# Import modules.
import tornado.options
import tornado.gen
import logging
import subprocess
import datetime
import concurrent
import time
import os

class OLA:

    def __init__(self):
        self.__executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.active_task = None
        self.active_epoch = None
        self.active_details = None
        self.restart_pending = False
        
        # Initialize patching.
        self.is_output = None
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

        if not self.is_output:
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
        logging.info(f"STOP")
        
        self.active_task = None
        self.active_epoch = None
        self.active_details = None

    def __patch_output(self):
        #self.__executor.submit(subprocess.run, "ola_patch -d 1 -i -p 0 -u 0 --unpatch", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        #self.__executor.submit(subprocess.run, "sleep 0", shell=True) # add to queue for tracking
        #self.__executor.submit(subprocess.run, "ola_patch -d 1 -p 0 -u 0", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        #self.__executor.submit(subprocess.run, "sleep 0", shell=True) # add to queue for tracking
        os.system(f"ola_patch -d 1 -i -p 0 -u 0 --unpatch")
        os.system(f"ola_patch -d 1 -p 0 -u 0")
        #tornado.gen.sleep(0.1)
        self.is_output = True

    def __patch_input(self):
        #self.__executor.submit(subprocess.run, "ola_patch -d 1 -p 0 -u 0 --unpatch", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        #self.__executor.submit(subprocess.run, "sleep 0", shell=True) # add to queue for tracking
        #self.__executor.submit(subprocess.run, "ola_patch -d 1 -i -p 0 -u 0", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        #self.__executor.submit(subprocess.run, "sleep 0", shell=True) # add to queue for tracking
        os.system(f"ola_patch -d 1 -p 0 -u 0 --unpatch")
        os.system(f"ola_patch -d 1 -i -p 0 -u 0")
        #tornado.gen.sleep(0.1)
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
                os.system(f"service olad restart")
                logging.info(f"--- OLA RESTART ---")
                self.restart_pending = False
                break
            else:
                tornado.gen.sleep(1)


