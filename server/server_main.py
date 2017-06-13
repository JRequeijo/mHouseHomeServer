import json
import sys
import os
import logging
import signal
my_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(my_dir+"/../")
sys.path.append(my_dir+"/../proxy/")

import settings

from homeserver import HomeServer

logging.config.fileConfig(settings.LOGGING_CONFIG_FILE, disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def check_kill_process(pstring):
    for line in os.popen("ps ax | grep " + pstring + " | grep -v grep"):
        fields = line.split()
        pid = fields[0]
        print pid
        if pid != str(os.getpid()):
            os.kill(int(pid), signal.SIGKILL)

def run_homeserver():


    # check_kill_process("server_main.py")

    logger.info("Starting Home Server...")
    try:
        f = open(settings.SERVER_CONFIG_FILE, "r")
        server_conf = json.load(f)

        server = HomeServer(server_conf["id"], server_conf["name"], server_conf["address"])
        server.start()
    except IOError:
        logger.error("ERROR: Unable to open server configuration file. Server probably not registed.")
        sys.exit()

if __name__ == "__main__":
    run_homeserver()
