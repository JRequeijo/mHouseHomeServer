"""
    This is the communicator file for the HomeServer proxy.
    Here are specified the communicator class, used to interconnect proxy and CoAP server
    and a helper Response class, used to ease the management of CoAP responses
"""
from coapthon.client.helperclient import HelperClient
from coapthon import defines
from utils import AppError

__author__ = "Jose Requeijo Dias"

class Communicator(object):
    """
        This represents a CoAP communicator. It is used to establish connections
        and send data to the CoAP server.
    """
    def __init__(self, host, port=5683):

        self.host = host
        self.port = port
        self.client = None

    def start(self):
        """
            This method starts a new communicator.
        """
        self.client = HelperClient(server=(self.host, self.port))

    def stop(self):
        """
            This method stops a communicator.
        """
        self.client.stop()

    def restart(self):
        """
            This method restarts a communicator.
        """
        self.stop()
        self.start()

    def get(self, path, timeout=None):
        """
            This method send a get message to the resource specified by path
            on the CoAP server. It waits timeout seconds to receive the response 
            to the get call.
        """
        try:
            self.start()
            resp = self.client.get(path, timeout=timeout)
        except:
            self.stop()
            raise AppError(504, "Connection Timeout. Home Server is down.")

        self.stop()

        return resp

    def post(self, path, payload, timeout=None):
        """
            This method send a post message to the resource specified by path
            on the CoAP server with the payload JSON message. It waits timeout
            seconds to receive the response to the post call.
        """
        try:
            self.start()
            resp = self.client.post(path, (defines.Content_types["application/json"],\
                                        payload), timeout=timeout)
        except:
            self.stop()
            raise AppError(504, "Connection Timeout. Home Server is down.")
        self.stop()

        return resp

    def put(self, path, payload="", timeout=None):
        """
            This method send a put message to the resource specified by path
            on the CoAP server with the payload JSON message. It waits timeout
            seconds to receive the response to the put call.
        """
        try:
            self.start()
            resp = self.client.put(path, (defines.Content_types["application/json"],\
                                    payload), timeout=timeout)
        except:
            self.stop()
            raise AppError(504, "Connection Timeout. Home Server is down.")
        self.stop()

        return resp

    def delete(self, path, timeout=None):
        """
            This method send a delete message to the resource specified by path
            on the CoAP server. It waits timeout seconds to receive the response
            to the delete call.
        """
        try:
            self.start()
            resp = self.client.delete(path, timeout=timeout)
        except:
            self.stop()
            raise AppError(504, "Connection Timeout. Home Server is down.")
        self.stop()

        return resp

    def discover(self, path, timeout=None):
        """
            This method send a discover message to the resource specified by path
            on the CoAP server. It waits timeout seconds to receive the response
            to the discover call.
        """
        try:
            self.start()
            resp = self.client.discover(path, timeout=timeout)
        except:
            self.stop()
            raise AppError(504, "Connection Timeout. Home Server is down.")
        self.stop()

        return resp

    def get_response(self, data):
        """
            This method use the data received in response to a call, to
            construct a Response object that can be easily used to manage the
            response data.
        """
        return Response(data)


class Response(object):
    """
        This represents a Response to a call made by the communicator to the
        CoAP server.
    """
    def __init__(self, data):
        self.payload = data.payload
        self.code = data.code
        self.content_type = [k for k in defines.Content_types if defines.Content_types[k] == data.content_type]
        self.content_type = self.content_type[0]

    def data(self):
        """
            This method returns a dictionary with a simple representation of the data received.
        """
        return {"payload":self.payload, "code":self.code, "content-type":self.content_type}

    def __str__(self):
        return "\nPayload:"+str(self.payload)+"\nCode:"+\
                    str(self.code)+"\nContent-Type:"+str(self.content_type)+"\n"
