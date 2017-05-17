"""
    This is the Home Server Main CoAP File.
    Here is specified the CoAP server that represents the Home Server Core.
"""
import logging

from coapthon.server.coap import CoAP

from server.idgenerator import IDGenerator
from server.homeserverinfo import HomeServerInfo
from server.devices import DevicesList
from server.services import HomeServerServices
from server.serverconfigs import HomeServerConfigs

import settings

__author__ = "Jose Requeijo Dias"

logger = logging.getLogger(__name__)


class HomeServer(CoAP):
    """
        This is the Home Server Main CoAP Class.
        It is the CoAP server that represents the Home Server Core.
    """
    def __init__(self, server_id, name, address):

        self.id = server_id
        self.name = name

        self.address = address

        self.coapaddress = settings.COAP_ADDR
        self.port = settings.COAP_PORT
        self.multicast = settings.COAP_MULTICAST

        logger.info("Starting Home Server...")
        CoAP.__init__(self, (self.coapaddress, self.port), self.multicast)

        self.info = HomeServerInfo(self)

        self.devices = DevicesList(self)
        self.id_gen = IDGenerator(self)
        self.services = HomeServerServices(self)
        self.configs = HomeServerConfigs(self)

        logger.info("CoAP Server start on " + self.address + ":" + str(self.port))
        logger.info(self.root.dump())

    def start(self):
        """
            This method starts the Home Server CoAP server
            (or what can be viewed as the Home Server Core)
        """
        try:
            logger.info("Home Server Started...")
            self.listen(10)
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """
            This method shuts down the Home Server CoAP server
            (or what can be viewed as the Home Server Core)
        """
        logger.info("Shutting down server")
        self.close()
        logger.info("Server is down")
