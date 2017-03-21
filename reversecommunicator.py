#!/usr/bin/env python

from coapthon.server.coap import CoAP
from coapthon.resources.resource import Resource
from utils import error, status, AppError, check_on_body, get_my_ip,\
    AppHTTPError
from coapthon import defines
import json

import requests 
  
class ReverseCommunicator(CoAP):
    def __init__(self):
        self.ip = "224.0.1.187"
        #self.ip = "127.0.0.1"
        self.port = 5683
        self.multicast = True
        
        self.proxy_ip = get_my_ip()
        self.proxy_port = 8080
        
        CoAP.__init__(self, (self.ip, self.port), self.multicast)
        
        self.add_resource("register/", Register(self))
            
        print "Reverse Communicator CoAP Server start on " + self.ip + ":" + str(self.port)
        print self.root.dump()
        
    def start(self):
        try:
            self.listen(10)
        except:
            print "Server Cannot Listen"
            self.close()
            print "Exiting..."
            
    def shutdown(self):
        print "Shutting down server"
        self.close()
        print "Server down"

class Register(Resource):
    def __init__(self, coap_server):
        # initialize CoAP Resource
        super(Register, self).__init__("Register", coap_server, visible=True,
                                            observable=True, allow_children=False)
        
        self.server = coap_server
        self.root_uri = "http://"+str(self.server.proxy_ip)+":"+str(self.server.proxy_port)
    
    
    def render_POST(self, request):
        if(request.content_type is defines.Content_types.get("application/json")):
            
            try:
                body = json.loads(request.payload)
                
                check_on_body(body, ["address", "name", "area", "divisions"])
                
                try:
                    self.payload = self.regist(body)
                    return status(defines.Codes.CREATED, self.payload)
                
                except AppHTTPError as err:
                    print err.code
                    print err.msg
                    return error(err.code, err.msg)
                
                except:
                    return error(defines.Codes.NOT_ACCEPTABLE, "Not Acceptable")
            
            except ValueError:
                print "ERROR: Request payload not json"
                return error(defines.Codes.BAD_REQUEST, "Payload not json")   
            
            except AppError as err:
                print err.msg
                return error(err.code, err.msg)
        else:
            return error(defines.Codes.UNSUPPORTED_CONTENT_FORMAT, 
                         "Request body content format not json")

    def regist(self, request_data):
        headers = {'user-agent': 'app-communicator', 'content-type':'application/json'}
        r = requests.post(self.root_uri+"/register", json = request_data, headers=headers)
        print r.status_code
        if int(r.status_code) >= 400:
            resp = r.json()
            raise AppHTTPError(resp["error_code"], resp["error_msg"])
        
        return r.json()
    