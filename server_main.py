import json
import sys
import logging
import threading
import time
import psutil
from multiprocessing import Process

import settings

from server.homeserver import HomeServer

import proxy_main

logging.config.fileConfig(settings.LOGGING_CONFIG_FILE, disable_existing_loggers=False)
logger = logging.getLogger(__name__)

def monitor_proxy(proxy_proc, term_event, term_lock_proxy, term_lock_server):

    printed = False
    while True:
        if proxy_proc.is_running():
            pass
        else:
            print "EXIT: "+str(proxy_proc.exitcode)
            if proxy_proc.exitcode != 4:
                print "PROXY is DEAD. Restarting"
                proxy_proc = Process(target=proxy_main.run_proxy, args=(psutil.Process(), term_event, term_lock_server,))
                proxy_proc.start()
                print "PROXY PROCCESS: "+str(proxy_proc.pid)
                print "PROXY ALIVE AGAIN"
                printed = False
            else:
                term_event.set()
                term_lock_proxy.acquire()
                break

        if term_event.isSet():
            term_lock_proxy.acquire()
            proxy_proc.terminate()
            break
        else:
            time.sleep(2)

    term_lock_proxy.release()

def run_home_server(proxy_proc, term_event, term_lock_proxy, term_lock_server):

    proxy_mon_thr = threading.Thread(target=monitor_proxy, args=(proxy_proc, term_event,\
                                                         term_lock_proxy, term_lock_server,))
    proxy_mon_thr.start()

    try:
        f = open(settings.SERVER_CONFIG_FILE, "r")
        server_conf = json.load(f)

        server = HomeServer(server_conf["id"], server_conf["name"], server_conf["address"])
        server.start()
    except:
        logger.error("ERROR: Unable to open server configuration file. Server probably not registed.")
        sys.exit()

# if __name__ == "__main__":
#     run_home_server()
