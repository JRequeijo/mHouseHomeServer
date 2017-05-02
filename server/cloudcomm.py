
import json
import time

from coapthon import defines
from coapthon.resources.resource import Resource

import settings

from utils import *
from core.devicetypes import DEVICE_TYPES, validate_device_type
from core.services import SERVICES, validate_services
from core.propertytypes import PROPERTY_TYPES
import core.valuetypes as valuetypes

import requests

import thread
import os.path
import logging

logger = logging.getLogger(__name__)

def get_server_configs():
    try:
        f = open(os.path.dirname(__file__) + "/../"+settings.SERVER_CONFIG_FILE, "r")

        file_data = json.load(f)

        check_on_body(file_data, ["email", "password", "id"])

        return file_data
    except:
        logger.error("Server Configuration File Not Found or improperly configured")
        return False

### REVER ISTO MUITO BEM
def regist_device_on_cloud(device):

    data = get_server_configs()
    if data:
        email = data["email"]
        password = data["password"]
        server_id = data["id"]
    else:
        return data

    client = requests.Session()
    try:
        resp = client.head(settings.CLOUD_BASE_URL+"login/")
        csrftoken = resp.cookies["csrftoken"]

        client.headers.update({"Accept":"application/json",\
                "Content-Type":"application/json",\
                "X-CSRFToken":csrftoken})
        client.auth = (email, password)

        try:
            resp = client.get(settings.CLOUD_BASE_URL+"api/devices/")
            regist_done = False
            if resp.status_code == 200:
                js = json.loads(resp.text)
                devices = js["devices"]
                for d in devices:
                    if d["address"] == device.address:
                        device.universal_id = d["id"]
                        try:
                            resp = client.patch(settings.CLOUD_BASE_URL+"api/devices/"\
                                                    +str(d["id"])+"/", data=device.get_json())
                            regist_done = True
                            break
                        except:
                            raise AppError(503)

                if not regist_done:
                    data = device.get_info()
                    data["server"] = server_id
                    try:
                        resp = client.post(settings.CLOUD_BASE_URL+"api/devices/",\
                                                data=json.dumps(data))

                        if resp.status_code == 200:
                            js = json.loads(resp.text)
                            devices = js["devices"]
                            for d in devices:
                                if d["address"] == device.address:
                                    device.universal_id = d["id"]
                                    break

                        elif resp.status_code == 400:
                            js = json.loads(resp.text)
                            try:
                                errs = js["non_field_errors"]
                                for ele in errs:
                                    if "address" in ele:
                                        logger.error("Problems with address")
                            except:
                                logger.error("ERROR DUMMMM")
                    except:
                        AppError(503)
        except:
            raise AppError(503)
    except AppError:
        logger.error("You do not have connection to the internet or the cloud server is down")

### REVER ISTO MUITO BEM
def unregist_device_from_cloud(device_id):

    data = get_server_configs()
    if data:
        email = data["email"]
        password = data["password"]
        server_id = data["id"]
    else:
        return data

    client = requests.Session()
    try:
        resp = client.head(settings.CLOUD_BASE_URL+"login/")
        csrftoken = resp.cookies["csrftoken"]

        client.headers.update({"Accept":"application/json",\
                "Content-Type":"application/json",\
                "X-CSRFToken":csrftoken})
        client.auth = (email, password)

        resp = client.delete(settings.CLOUD_BASE_URL+"api/devices/"+str(device_id))
    except:
        logger.error("You do not have connection to the internet or the cloud server is down")

#
def notify_cloud(device_state):
    print "Notifying Cloud"
    data = get_server_configs()
    if data:
        email = data["email"]
        password = data["password"]
        server_id = data["id"]
    else:
        return data

    client = requests.Session()
    try:
        resp = client.head(settings.CLOUD_BASE_URL+"login/")
        csrftoken = resp.cookies["csrftoken"]

        client.headers.update({"Accept":"application/json",\
                "Content-Type":"application/json",\
                "X-CSRFToken":csrftoken})
        client.auth = (email, password)

        try:
            resp = client.patch(settings.CLOUD_BASE_URL+"api/devices/"\
                                +str(device_state.device.universal_id)\
                                +"/state/?fromserver=true", data=device_state.get_json())
            if resp.status_code == 200:
                print "STATE CHANGED"
        except:
            raise AppError(503)
    except AppError:
        logger.error("You do not have connection to the internet or the cloud server is down")
