import json
import sys

from server.homeserver import HomeServer
import logging.config

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)

try:
    f = open("serverconf.json", "r")
    server_conf = json.load(f)

    server = HomeServer(server_conf["id"], server_conf["name"], server_conf["address"])
    server.start()
except:
    logger.error("Unable to open server configuration file. Server probably not registed.")
    sys.exit()