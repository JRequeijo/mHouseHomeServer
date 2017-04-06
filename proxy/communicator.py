#!/usr/bin/env python
from coapthon.client.helperclient import HelperClient
from coapthon import defines
from utils import AppError

class Communicator: 
    def __init__(self, host, port=5683):

        self.host = host
        self.port = port
        self.client = None

    def start(self):
        self.client = HelperClient(server=(self.host, self.port))

    def stop(self):
        self.client.stop()

    def restart(self):
        self.stop()
        self.start()

    def get(self, path, timeout=None):
        try:
            self.start()
            resp = self.client.get(path, timeout=timeout)
        except:
            self.stop()
            raise AppError(504, "Connection Timeout. Home Server is down.")

        self.stop()

        return resp

    def post(self, path, payload, timeout=None):
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
        try:
            self.start()
            resp = self.client.delete(path, timeout=timeout)
        except:
            self.stop()
            raise AppError(504, "Connection Timeout. Home Server is down.")
        self.stop()

        return resp

    def discover(self, path, timeout=None):
        try:
            self.start()
            resp = self.client.discover(path, timeout=timeout)
        except:
            self.stop()
            raise AppError(504, "Connection Timeout. Home Server is down.")
        self.stop()

        return resp

    def get_response(self, data):
        return Response(data)


class Response:
    def __init__(self, data):
        self.payload = data.payload
        self.code = data.code
        self.content_type = [k for k in defines.Content_types if defines.Content_types[k] == data.content_type]
        self.content_type = self.content_type[0]
    
    def data(self):
        return {"payload":self.payload, "code":self.code, "content-type":self.content_type}
    
    def __str__(self):
        return "\nPayload:"+str(self.payload)+"\nCode:"+str(self.code)+"\nContent-Type:"+str(self.content_type)+"\n"