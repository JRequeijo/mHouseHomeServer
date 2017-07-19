import boto3
import json


class AWSCommunicator(object):

    def __init__(self):
        self.client = boto3.client("iot")
        self.dataclient = boto3.client("iot-data")

    def register_new_device(self, device_name, state):
        try:
            resp = self.client.create_thing(thingName=device_name)
            print resp

            data = {"state":{"desired":state.get_simplified_wanted_state(),
                             "reported":state.get_simplified_current_state()}}
            resp = self.dataclient.update_thing_shadow(thingName=device_name,\
                                                        payload=json.dumps(data))
            print resp

            print "Device Successfully Registered on AWS"
        except Exception as err:
            print "ERROR: ", err
    
    def unregister_device(self, device_name):
        try:
            resp = self.client.create_thing(thingName=device_name)
            print resp

            print "Device Successfully Unregistered from AWS"
        except Exception as err:
            print "ERROR: ", err
    
    def notify_shadow(self, device_name, state):
        try:
            data = {"state":{"desired":state.get_simplified_wanted_state(),
                             "reported":state.get_simplified_current_state()}}
            resp = self.dataclient.update_thing_shadow(thingName=device_name,\
                                                        payload=json.dumps(data))
            print resp

            print "Device State Successfully Updated on AWS"
        except Exception as err:
            print "ERROR: ", err
