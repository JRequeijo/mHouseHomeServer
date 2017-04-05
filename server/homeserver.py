#!/usr/bin/env python
from coapthon.server.coap import CoAP


from server.idgenerator import IDGenerator
from server.homeserverinfo import HomeServerInfo
from server.devices import DevicesList
import logging.config

logger = logging.getLogger(__name__)


class HomeServer(CoAP):
    def __init__(self, server_id, name, address, areas=[]):

        self.id = server_id
        self.name = name

        self.address = address

        #self.coapaddress = "224.0.1.187"
        self.coapaddress = "192.168.1.67"
        self.port = 5683
        self.multicast = False

        logger.info("Starting Home Server...")
        CoAP.__init__(self, (self.coapaddress, self.port), self.multicast)

        self.info = HomeServerInfo(self)

        self.devices = DevicesList(self)
        self.id_gen = IDGenerator(self)

        logger.info("CoAP Server start on " + self.address + ":" + str(self.port))
        logger.info(self.root.dump())

    def start(self):
        try:
            logger.info("Home Server Started...")
            self.listen(10)
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        logger.info("Shutting down server")
        self.close()
        logger.info("Server is down")
