import json
import sys

from homeserver import HomeServer

# from server.communicator import Communicator
# from utils import AppError
# from exceptions import ValueError, KeyError
# from coapthon import defines
# from server.config import *

try:
    f = open("serverconf.json", "r")
    server_conf = json.load(f)

    print "Starting Home Server..."
    server = HomeServer(server_conf["id"], server_conf["name"], server_conf["address"])
    server.start()
    print "Home Server started."
except:
    print "ERROR: Unable to open server configuration file. Server probably not registed."
    sys.exit()