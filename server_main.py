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

def monitor_proxy(server_alive_event, proxy_alive_event, term_event, server_term_event):

    printed = False
    while True:
        if proxy_alive_event.wait(2):
            print "Proxy is ALIVE"
            proxy_alive_event.clear()
        else:
            # print "EXIT: "+str(proxy_proc.exitcode)
            # if proxy_proc.exitcode != 4:
            print "PROXY is DEAD. Restarting"
            new_proxy_proc = Process(target=proxy_main.run_proxy, args=(psutil.Process(), server_alive_event, proxy_alive_event, term_event, server_term_event,))
            new_proxy_proc.start()

            print "PROXY PROCCESS: "+str(new_proxy_proc.pid)
            print "PROXY ALIVE AGAIN"
            printed = False
            # else:
            #     term_event.set()
            #     term_lock_proxy.acquire()
            #     break

        # time.sleep(2)

    sys.exit(0)

def send_heartbeat(alive_event):
    while True:
        if not alive_event.isSet():
            print "SERVER Send heartbeat"
            alive_event.set()

def run_home_server(server_alive_event, proxy_alive_event, term_event, server_term_event):

    proxy_mon_thr = threading.Thread(target=monitor_proxy, args=(server_alive_event, proxy_alive_event, term_event, server_term_event,))
    proxy_mon_thr.start()

    heartbeat_thr = threading.Thread(target=send_heartbeat, args=(server_alive_event,))
    heartbeat_thr.start()

    try:
        f = open(settings.SERVER_CONFIG_FILE, "r")
        server_conf = json.load(f)

        server = HomeServer(server_conf["id"], server_conf["name"], server_conf["address"])
        server.start()
    except IOError:
        logger.error("ERROR: Unable to open server configuration file. Server probably not registed.")
        sys.exit()

# if __name__ == "__main__":
#     run_home_server()
