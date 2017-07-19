"""
    This is the Cloud Communicator File.
    Here are specified all the functions that communicate back
    with the cloud service, i.e. all the functions that transform
    the Home Server in a cloud service client and interact with it.
"""
import json
import logging
import requests
import time 

import settings
from utils import AppError

__author__ = "Jose Requeijo Dias"

logger = logging.getLogger(__name__)

def sendServerAliveSignaltoCloud(server):
    while not server.stopped.isSet():
        time.sleep(10)
        print "Send Server Alive to Cloud"
        try:
            email = settings.USER_EMAIL
            password = settings.USER_PASSWORD
            server_id = settings.HOME_SERVER_ID
        except:
            logger.error("Settings file not properly configured. Probably Home Server registration improperly done.")
            return False

        client = requests.Session()
        try:
            resp = client.head(settings.CLOUD_BASE_URL+"login/")
            csrftoken = resp.cookies["csrftoken"]

            client.headers.update({"Accept":"application/json",\
                    "Content-Type":"application/json",\
                    "X-CSRFToken":csrftoken})
            client.auth = (email, password)

            try:
                resp = client.patch(settings.CLOUD_BASE_URL+"api/servers/"\
                                    +str(server_id)\
                                    +"/state/?fromserver=true", data=json.dumps({"status":"running"}))
                if resp.status_code == 200:
                    print "ALIVE SENT"
            except:
                raise AppError(503)
        except AppError:
            logger.error("You do not have connection to the internet or the cloud server is down")
        except Exception as err:
            print "ERROR: ", err

### REVER ISTO MUITO BEM
def regist_device_on_cloud(device):
    """
        This method tries to register a new device on the cloud server.
        If the device already exists, it synchronizes the information overall system.
    """
    try:
        email = settings.USER_EMAIL
        password = settings.USER_PASSWORD
        server_id = settings.HOME_SERVER_ID
    except:
        logger.error("Settings file not properly configured. Probably Home Server registration improperly done.")
        return False

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
                        device.services.services = d["services"]
                        device.name = d["name"]
                        try:
                            resp = client.patch(settings.CLOUD_BASE_URL+"api/devices/"\
                                                    +str(d["id"])+"/?fromserver=true", data=device.get_json())
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
    """
        This method tries to unregister a new device on the cloud server.
    """
    try:
        email = settings.USER_EMAIL
        password = settings.USER_PASSWORD
        server_id = settings.HOME_SERVER_ID
    except:
        logger.error("Settings file not properly configured. Probably Home Server registration improperly done.")
        return False

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
    """
        This method notifies the cloud service about changes on the
        devices or Home Server states/informations.
    """

    print "Notifying Cloud"
    try:
        email = settings.USER_EMAIL
        password = settings.USER_PASSWORD
        server_id = settings.HOME_SERVER_ID
    except:
        logger.error("Settings file not properly configured. Probably Home Server registration improperly done.")
        return False

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
                                +"/state/?fromserver=true", data=json.dumps({"current_state":device_state.state}))
            if resp.status_code == 200:
                print "STATE CHANGED"
        except:
            raise AppError(503)
    except AppError:
        logger.error("You do not have connection to the internet or the cloud server is down")
