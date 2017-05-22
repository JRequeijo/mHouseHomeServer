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

def monitor_proxy(proxy_proc, term_event, server_term_event):

    printed = False
    while True:
        if proxy_proc.is_running():
            print "Proxy is ALIVE"
        else:
            # print "EXIT: "+str(proxy_proc.exitcode)
            # if proxy_proc.exitcode != 4:
            print "PROXY is DEAD. Restarting"
            new_proxy_proc = Process(target=proxy_main.run_proxy, args=(psutil.Process(), term_event, server_term_event,))
            new_proxy_proc.start()

            proxy_proc = psutil.Process(new_proxy_proc.pid)

            print "PROXY PROCCESS: "+str(new_proxy_proc.pid)
            print "PROXY ALIVE AGAIN"
            printed = False
            # else:
            #     term_event.set()
            #     term_lock_proxy.acquire()
            #     break

        time.sleep(2)

    sys.exit(0)

def run_home_server(proxy_proc, term_event, server_term_event):

    proxy_mon_thr = threading.Thread(target=monitor_proxy, args=(proxy_proc, term_event, server_term_event,))
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
