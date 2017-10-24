import boto3
import json
import threading
import time
import sys
import os
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

my_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(my_dir+"/../")
sys.path.append(my_dir+"/../server/")

import settings
from utils import AppError
from proxy.communicator import Communicator

class AWSCommunicator(object):

    def __init__(self, credentials=None):
        if credentials is not None and isinstance(credentials, tuple) and len(credentials) == 2:
            self.client = boto3.client("iot",\
                                        aws_access_key_id=credentials[0],\
                                        aws_secret_access_key=credentials[1])
            self.dataclient = boto3.client("iot-data",\
                                        aws_access_key_id=credentials[0],\
                                        aws_secret_access_key=credentials[1])
        else:
            self.client = boto3.client("iot")
            self.dataclient = boto3.client("iot-data")
        
        self.listener_thread = threading.Thread(target=self.run_cloud_shadow_listener)
        self.listener_thread.start()

    def register_new_device(self, device_name, state):
        try:
            resp = self.client.create_thing(thingName=device_name)

            data = {"state":{"desired":state.get_simplified_wanted_state(),
                             "reported":state.get_simplified_current_state()}}
            resp = self.dataclient.update_thing_shadow(thingName=device_name,\
                                                        payload=json.dumps(data))

            print "Device Successfully Registered on AWS"
        except Exception as err:
            print "ERROR: ", err
    
    def unregister_device(self, device_name):
        try:
            resp = self.client.create_thing(thingName=device_name)

            print "Device Successfully Unregistered from AWS"
        except Exception as err:
            print "ERROR: ", err
    
    def notify_shadow(self, device_name, state):
        try:
            data = {"state":{"desired":state.get_simplified_wanted_state(),
                             "reported":state.get_simplified_current_state()}}
            resp = self.dataclient.update_thing_shadow(thingName=device_name,\
                                                        payload=json.dumps(data))

            print "Device State Successfully Updated on AWS"
        except Exception as err:
            print "ERROR: ", err

    def run_cloud_shadow_listener(self):
        comm = Communicator(settings.COAP_ADDR, settings.COAP_PORT)
        last_states = {}
        while 1:
            try:
                resp = comm.get("/devices", timeout=settings.COMM_TIMEOUT)
            except AppError as err:
                abort(err.code, err.msg)
            except:
                abort(500, "Unknown Proxy fatal error")

            resp = comm.get_response(resp)
            devs = json.loads(resp.payload)
            
            for dev in devs["devices"]:
                response = self.dataclient.get_thing_shadow(thingName=dev["name"]+"-"+str(dev["local_id"]))
                state = json.loads(response["payload"].read())["state"]
                try:
                    if last_states[dev["local_id"]] != state["desired"]:
                        print "\n\nUpdate From AWS cloud" 
                        try:
                            resp = comm.put("/devices/"+str(dev["local_id"])+"/state",\
                                            json.dumps(state["desired"]), timeout=settings.COMM_TIMEOUT)
                        except AppError as err:
                            abort(err.code, err.msg)
                        except:
                            abort(500, "Unknown Proxy fatal error")
                except:
                    print "\n\nState From AWS cloud" 
                    print state
                    print "--------------------\n\n"

                last_states[dev["local_id"]] = state["reported"]
            
            time.sleep(5)