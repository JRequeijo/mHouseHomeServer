import json
import sys
import logging

import settings

from server.homeserver import HomeServer

logging.config.fileConfig(settings.LOGGING_CONFIG_FILE, disable_existing_loggers=False)
logger = logging.getLogger(__name__)

def run_home_server():
    try:
        f = open(settings.SERVER_CONFIG_FILE, "r")
        server_conf = json.load(f)

        server = HomeServer(server_conf["id"], server_conf["name"], server_conf["address"])
        server.start()
    except:
        logger.error("ERROR: Unable to open server configuration file. Server probably not registed.")
        sys.exit()

if __name__ == "__main__":
    run_home_server()