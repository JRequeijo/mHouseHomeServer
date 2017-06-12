import json
import sys
import logging
import threading
import time
import psutil
import multiprocessing
import Queue


import settings

from server.homeserver import HomeServer

import proxy_main

logging.config.fileConfig(settings.LOGGING_CONFIG_FILE, disable_existing_loggers=False)
logger = logging.getLogger(__name__)

def monitor_proxy(proxy2server_queue, term_event):

    while True:
        try:
            proxy_state = proxy2server_queue.get(True, 5)
            if proxy_state is True:
                print "PROXY is ALIVE"
            else:
                raise Queue.Empty
        except Queue.Empty:
            print "PROXY is DEAD"

        if term_event.is_set():
            print "TERMINATING PROXY MONITORING THREAD"
            break

    sys.exit(0)

def send_heartbeat(server2proxy_queue, term_event):
    while True:
        server2proxy_queue.put(True, True, None)
        print "SERVER Send heartbeat"
        time.sleep(2)

        if term_event.is_set():
            print "TERMINATING SEND HB from HOMESERVER THREAD"
            break

    sys.exit(0)

def homeserver_closure(server, term_event, semphore):
    while True:
        if term_event.is_set():
            print "TERMINATING HOMESERVER"
            server.shutdown()
            break

    semphore.release()
    sys.exit(0)

def run_homeserver(server2proxy_queue, proxy2server_queue, term_event, semphore):

    proxy_mon_thr = threading.Thread(target=monitor_proxy, args=(proxy2server_queue, term_event,))
    proxy_mon_thr.start()

    heartbeat_thr = threading.Thread(target=send_heartbeat, args=(server2proxy_queue, term_event,))
    heartbeat_thr.start()

    try:
        f = open(settings.SERVER_CONFIG_FILE, "r")
        server_conf = json.load(f)

        server = HomeServer(server_conf["id"], server_conf["name"], server_conf["address"])

        end_thread = threading.Thread(target=homeserver_closure, args=(server, term_event, semphore,))
        end_thread.start()

        server.start()
    except IOError:
        logger.error("ERROR: Unable to open server configuration file. Server probably not registed.")
        sys.exit()

    print "HOMESERVER DOWN"
# if __name__ == "__main__":
#     run_home_server()
