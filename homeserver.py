#!/usr/bin/env python
from coapthon.server.coap import CoAP


from server.idgenerator import IDGenerator
from server.homeserverinfo import HomeServerInfo
from server.devices import DevicesList

class HomeServer(CoAP):
    def __init__(self, server_id, name, address, areas=[]):

        self.id = server_id
        self.name = name

        self.address = address

        #self.coapaddress = "224.0.1.187"
        self.coapaddress = "192.168.1.67"
        self.port = 5683
        self.multicast = False


        CoAP.__init__(self, (self.coapaddress, self.port), self.multicast)

        self.info = HomeServerInfo(self)

        self.devices = DevicesList(self)
        self.id_gen = IDGenerator(self)

        print "CoAP Server start on " + self.address + ":" + str(self.port)
        print self.root.dump()

    def start(self):
        try:
            self.listen(10)
        except KeyboardInterrupt:
            print "Server Shutdown"
            self.close()
            print "Exiting..."

    def shutdown(self):
        print "Shutting down server"
        self.close()
        print "Server down"
