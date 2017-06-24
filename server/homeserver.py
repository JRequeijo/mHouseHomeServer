"""
    This is the Home Server Main CoAP File.
    Here is specified the CoAP server that represents the Home Server Core.
"""
import sys
import logging
import threading
import copy

from coapthon.server.coap import CoAP
from coapthon import defines

from server.idgenerator import IDGenerator
from server.homeserverinfo import HomeServerInfo
from server.devices import DevicesList, DeviceState
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

        logger.info("Starting CoAP Server...")
        CoAP.__init__(self, (self.coapaddress, self.port), self.multicast)

        self.info = HomeServerInfo(self)

        self.devices = DevicesList(self)
        self.id_gen = IDGenerator(self)
        self.services = HomeServerServices(self)
        self.configs = HomeServerConfigs(self)

        logger.info("CoAP Server start on " + self.address + ":" + str(self.port))
        logger.info(self.root.dump())

    #
    ### This method is an override to the original CoAPthon receive_request method
    ### in order to allow the notification of the devices seperately
    def receive_request(self, transaction):
        """
        Handle requests coming from the udp socket.

        :param transaction: the transaction created to manage the request
        """
        with transaction:

            transaction.separate_timer = self._start_separate_timer(transaction)

            self._blockLayer.receive_request(transaction)

            if transaction.block_transfer:
                self._stop_separate_timer(transaction.separate_timer)
                self._messageLayer.send_response(transaction)
                self.send_datagram(transaction.response)
                return

            self._observeLayer.receive_request(transaction)

            self._requestLayer.receive_request(transaction)


            # Here is the difference between the original method and this one
            if transaction.resource is not None and transaction.resource.changed:
                if isinstance(transaction.resource, DeviceState):
                    if transaction.request.source[0] != transaction.resource.device.address:
                        self.notify_owner(transaction.resource)
                    else:
                        self.notify_others(transaction.resource)
                else:
                    self.notify(transaction.resource)

                transaction.resource.changed = False

            elif transaction.resource is not None and transaction.resource.deleted:
                self.notify(transaction.resource)
                transaction.resource.deleted = False

            if (transaction.resource is None) or (not transaction.resource.deleted):
            ########################################################################
                self._observeLayer.send_response(transaction)

                self._blockLayer.send_response(transaction)

                self._stop_separate_timer(transaction.separate_timer)

                self._messageLayer.send_response(transaction)

                if transaction.response is not None:
                    if transaction.response.type == defines.Types["CON"]:
                        self._start_retransmission(transaction, transaction.response)
                    self.send_datagram(transaction.response)
    
    def _retransmit(self, transaction, message, future_time, retransmit_count):
        """
        Thread function to retransmit the message in the future
        :param transaction: the transaction that owns the message that needs retransmission
        :param message: the message that needs the retransmission task
        :param future_time: the amount of time to wait before a new attempt
        :param retransmit_count: the number of retransmissions
        """
        with transaction:
            while retransmit_count < defines.MAX_RETRANSMIT and (not message.acknowledged and not message.rejected) \
                    and not self.stopped.isSet():
                transaction.retransmit_stop.wait(timeout=future_time)
                if not message.acknowledged and not message.rejected and not self.stopped.isSet():
                    retransmit_count += 1
                    future_time *= 2
                    self.send_datagram(message)

            if message.acknowledged or message.rejected:
                message.timeouted = False
            else:
                logger.warning("Give up on message {message}".format(message=message.line_print))
                message.timeouted = True
                if message.observe is not None:
                    self._observeLayer.remove_subscriber(message)

                    for d in self.devices.devices.itervalues():
                        if transaction.request.source[0] == d.address:
                            d.delete()
                            transaction.resource.deleted = True
                            break

            try:
                self.to_be_stopped.remove(transaction.retransmit_stop)
            except ValueError:
                pass
            transaction.retransmit_stop = None
            transaction.retransmit_thread = None

    #
    # This methods were created to modify the behaviour of some
    # other original CoAPthon methods
    def observe_layer_notify(self, resource, root=None):
        """
        Prepare notification for the resource to all interested observers.

        :rtype: list
        :param resource: the resource for which send a new notification
        :param root: deprecated
        :return: the list of transactions to be notified
        """
        ret = []
        if root is not None:
            resource_list = root.with_prefix_resource(resource.path)
        else:
            resource_list = [resource]
        for key in self._observeLayer._relations.keys():
            if self._observeLayer._relations[key].transaction.resource in resource_list:
                if self._observeLayer._relations[key].non_counter > defines.MAX_NON_NOTIFICATIONS \
                        or self._observeLayer._relations[key].transaction.request.type == defines.Types["CON"]:
                    self._observeLayer._relations[key].transaction.response.type = defines.Types["CON"]
                    self._observeLayer._relations[key].non_counter = 0
                elif self._observeLayer._relations[key].transaction.request.type == defines.Types["NON"]:
                    self._observeLayer._relations[key].non_counter += 1
                    self._observeLayer._relations[key].transaction.response.type = defines.Types["NON"]
                self._observeLayer._relations[key].transaction.resource = resource
                ret.append(self._observeLayer._relations[key].transaction)
        return ret

    def notify_owner(self, resource):
        """
        Notifies the observers of a certain resource.

        :param resource: the resource
        """
        # observers = self._observeLayer.notify(resource)
        observers = self.observe_layer_notify(resource)
        logger.debug("Notifying Owner")
        for transaction in observers:
            if transaction.request.source[0] == resource.device.address:
                logger.debug("Notifying: "+transaction.request.source[0])
                with transaction:
                    transaction.response = None
                    transaction = self._requestLayer.receive_request(transaction)
                    if not transaction.resource.deleted:
                        transaction = self._observeLayer.send_response(transaction)
                        transaction = self._blockLayer.send_response(transaction)
                        transaction = self._messageLayer.send_response(transaction)
                        if transaction.response is not None:
                            if transaction.response.type == defines.Types["CON"]:
                                self._start_retransmission(transaction, transaction.response)

                            self.send_datagram(transaction.response)
                            break

    def notify_others(self, resource):
        """
        Notifies the observers of a certain resource.

        :param resource: the resource
        """
        observers = self._observeLayer.notify(resource)
        logger.debug("Notifying Others")
        for transaction in observers:
            if transaction.request.source[0] != resource.device.address:
                logger.debug("Notifying: "+transaction.request.source[0])
                with transaction:
                    transaction.response = None
                    transaction = self._requestLayer.receive_request(transaction)
                    transaction = self._observeLayer.send_response(transaction)
                    transaction = self._blockLayer.send_response(transaction)
                    transaction = self._messageLayer.send_response(transaction)
                    if transaction.response is not None:
                        if transaction.response.type == defines.Types["CON"]:
                            self._start_retransmission(transaction, transaction.response)

                        self.send_datagram(transaction.response)

    #
    # Start the Home Server
    def start(self):
        """
            This method starts the Home Server CoAP server
            (or what can be viewed as the Home Server Core)
        """
        try:
            logger.info("Home Server Started...")

            mon_t = threading.Thread(target=self.devices.monitoring_devices)
            mon_t.start()

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
        sys.exit(0)


    