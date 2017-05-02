import requests
import json
import socket
import getopt
import sys
import getpass
import re
import utils
import logging

import settings

logger = logging.getLogger("proxylog")

def register():
    try:
        f = open(settings.SERVER_CONFIG_FILE, "r")
        confs = json.load(f)
        f.close()
        if registerFromFile(confs):
            settings.WORKING_OFFLINE = False
            return get_configs(confs) and get_services(confs)

        elif settings.ALLOW_WORKING_OFFLINE:
            settings.WORKING_OFFLINE = True
            logger.info("Working Offline")
            return True
    except:
        if registerFromScratch():
            f = open(settings.SERVER_CONFIG_FILE, "r")
            confs = json.load(f)
            f.close()
            settings.WORKING_OFFLINE = False
            return get_configs(confs) and get_services(confs)

        elif settings.ALLOW_WORKING_OFFLINE:
            settings.WORKING_OFFLINE = True
            logger.info("Working Offline")
            return True

def registerFromFile(confs):
    data = {}
    data["address"] = confs["address"]
    data["name"] = confs["name"]

    email = confs["email"]
    password = confs["password"]

    base_url = settings.CLOUD_BASE_URL

    with requests.Session() as client:
        try:
            # Retrieve the CSRF token first
            resp = client.head(base_url+"login/")  # sets cookie
            csrftoken = resp.cookies["csrftoken"]
        except:
            logger.error("You do not have connection to the internet or the cloud server is down")
            return False

        client.headers.update({"Accept":"application/json",\
                    "Content-Type":"application/json",\
                    "X-CSRFToken":csrftoken})

        client.auth = (email, password)
        try:
            resp = client.get(base_url+"api/servers/"+str(confs["id"])+"/")
        except:
            logger.error("You do not have connection to the internet or the cloud server is down")
            return False

        if resp.status_code == 200:
            f = open(settings.SERVER_CONFIG_FILE, "w")
            js = json.loads(resp.text)
            js["email"] = email
            js["password"] = password
            json.dump(js, f)
            f.close()
            logger.info("Server Info Retrieved Successfully")
            return True
        else:
            try:
                resp = client.post(base_url+"api/servers/", data=json.dumps(data))
            except:
                logger.error("You do not have connection to the\
                            internet or the cloud server is down")
                return False

            if resp.status_code == 200:
                f = open(settings.SERVER_CONFIG_FILE, "w")
                js = json.loads(resp.text)
                for ele in js["servers"]:
                    if ele["address"] == data["address"]:
                        serv = ele
                        break

                serv["email"] = email
                serv["password"] = password
                json.dump(serv, f)
                f.close()
                logger.info("Server Registed Successfully")
                return True
            else:
                js = json.loads(resp.text)
                if "address" in js.keys():
                    logger.error("Error ("+ str(resp.status_code)+"): "+str(js["address"][0]))

                if "name" in js.keys():
                    logger.error("Error ("+ str(resp.status_code)+"): "+str(js["name"][0]))

                if "detail" in js.keys():
                    logger.error("Error ("+ str(resp.status_code)+"): "+str(js["detail"][0]))

                logger.error("Please check if data on "+settings.SERVER_CONFIG_FILE+\
                                " file is correct. If you prefer you can delete that\
                                 file to register from scratch.")
                return False

def registerFromScratch():

    print "\nStarting Server Configuration from Scratch\n" 

    base_url = settings.CLOUD_BASE_URL

    with requests.Session() as client:
        try:
            # Retrieve the CSRF token first
            resp = client.head(base_url+"login/")  # sets cookie
            csrftoken = resp.cookies["csrftoken"]
        except:
            print "ERROR: You do not have connection to the internet or the cloud server is down"
            return False

        EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

        client.headers.update({"Accept":"application/json",\
                    "Content-Type":"application/json",\
                    "X-CSRFToken":csrftoken})

        data = {}
        reg_ok = False
        ip_ok = False
        name_ok = False
        cred_ok = False
        email_ok = False
        while not reg_ok:
            while not ip_ok:
                # ip_addr = raw_input("Enter your server IP address: ")
                # ip_addr = ip_addr.strip()
                ip_addr = utils.get_my_ip()

                if utils.validate_IPv4(ip_addr):
                    data["address"] = ip_addr
                    ip_ok = True
                else:
                    print "Invalid IP address"


            while not name_ok:
                name = raw_input("Choose your server name: ")
                name = name.strip()
                if name != "":
                    data["name"] = name
                    name_ok = True
                else:
                    print "Name ca not be blank"

            while not cred_ok:
                while not email_ok:
                    email = raw_input("Enter your email address: ")
                    email = email.strip()

                    if not EMAIL_REGEX.match(email):
                        print "Invalid email formatting. Try again."
                    else:
                        email_ok = True

                password = getpass.getpass(prompt="Enter your password: ")
                password = password.strip()

                cred_ok = True

            try:
                resp = client.post(base_url+"api/servers/", data=json.dumps(data),\
                                    auth=(email, password))
            except:
                print "ERROR: You do not have connection to\
                            the internet or the cloud server is down"
                return False

            if resp.status_code == 201:
                print "Server Registed Successfully"
                try:
                    f = open(settings.SERVER_CONFIG_FILE, "w")
                    js = json.loads(resp.text)
                    js["email"] = email
                    js["password"] = password
                    json.dump(js, f)
                    f.close()
                    reg_ok = True
                except:
                    print "ERROR: Could not create "+settings.SERVER_CONFIG_FILE+" file."
                    sys.exit()
            else:
                js = json.loads(resp.text)
                if "address" in js.keys():
                    print "ERROR ("+ str(resp.status_code)+"): "+str(js["address"][0])
                    ip_ok = False

                if "name" in js.keys():
                    print "ERROR ("+ str(resp.status_code)+"): "+str(js["name"][0])
                    name_ok = False

                if "detail" in js.keys():
                    print "ERROR ("+ str(resp.status_code)+"): "+str(js["detail"][0])
                    email_ok = False
                    cred_ok = False

    return True


def get_configs(confs):

    core_configs_url = settings.CLOUD_BASE_URL+"api/configs/"
    email = confs["email"]
    password = confs["password"]

    with requests.Session() as client:
        client.headers = {"Accept":"application/json"}
        client.auth = (email, password)
        try:
            # Retrieve the CSRF token first
            resp = client.get(core_configs_url)
            js = json.loads(resp.text)
        except:
            print "ERROR: You do not have connection to the internet or the cloud server is down"
            return False

        try:
            logger.info("Getting configurations: (device_types)")
            device_types_file = open(settings.DEVICE_TYPES_CONFIG_FILE, "w")
            data = {}
            data["DEVICE_TYPES"] = js["device_types"]
            json.dump(data, device_types_file)
            device_types_file.close()
        except:
            logger.error("Could not open/create "+settings.DEVICE_TYPES_CONFIG_FILE+" file")
            return False

        try:
            logger.info("Getting configurations: (value_types)")
            value_types_file = open(settings.VALUE_TYPES_CONFIG_FILE, "w")
            data = {}
            data["SCALAR_TYPES"] = js["value_types"]["scalars"]
            data["ENUM_TYPES"] = js["value_types"]["enums"]

            for e in data["ENUM_TYPES"]:
                ch = e["choices"]
                e["choices"] = {}
                for ele in ch:
                    for ele1 in js["value_types"]["choices"]:
                        if ele1["id"] == ele:
                            e["choices"][str(ele1["name"])] = ele1["value"]
                        if ele1["id"] == e["default_value"]:
                            e["default_value"] = ele1["name"]

            json.dump(data, value_types_file)
            value_types_file.close()
        except:
            logger.error("Could not open/create "+settings.VALUE_TYPES_CONFIG_FILE+" file")
            return False

        try:
            logger.info("Getting configurations: (property_types)")
            property_types_file = open(settings.PROPERTY_TYPES_CONFIG_FILE, "w")
            data = {}
            data["PROPERTY_TYPES"] = js["property_types"]
            json.dump(data, property_types_file)
            property_types_file.close()
        except:
            logger.error("Could not open/create "+settings.PROPERTY_TYPES_CONFIG_FILE+" file")
            return False
    return True

def get_services(confs):

    services_url = settings.CLOUD_BASE_URL+"api/services/"
    email = confs["email"]
    password = confs["password"]

    with requests.Session() as client:
        client.headers = {"Accept":"application/json"}
        client.auth = (email, password)
        try:
            # Retrieve the CSRF token first
            resp = client.get(services_url)
            js = json.loads(resp.text)
        except:
            print "ERROR: You do not have connection to the internet or the cloud server is down"
            return False

        try:
            logger.info("Getting Services")
            services_file = open(settings.SERVICES_CONFIG_FILE, "w")
            data = {}
            data["SERVICES"] = js["services"]
            json.dump(data, services_file)
            services_file.close()
        except:
            logger.error("Could not open/create "+settings.SERVICES_CONFIG_FILE+" file")
            return False

    return True
