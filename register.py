"""
    This is the register file for the HomeServer proxy.
    Here are specified the functions used to register the HomeServer on the cloud
    service and also to fetch the HomeServer configuration data from it.
"""
import json
import sys
import getpass
import re
import logging

import requests

import utils
import settings

__author__ = "Jose Requeijo Dias"

logger = logging.getLogger("proxylog")

def register():
    """
        This function register the HomeServer on the cloud service.
        Firstly it tries to register the HomeServer with the informations stored
        on the HomeServer configuration file. If this fails, it tries to register
        the HomeServer from scratch, asking the user for some informations like
        username and password.
        After the registration process it tries to fetch all the needed configurations
        from the cloud service.

        All these processes only work if the setting ALLOW_WORKING_OFFLINE
        is set to False. If it is setted to True, the HomeServer works without Internet
        connection and without cloud service support/registration.
    """
    try:
        f = open(settings.SERVER_CONFIG_FILE, "r")
        confs = json.load(f)
        f.close()

        settings.HOME_SERVER_ID = confs["id"]
        settings.HOME_SERVER_NAME = confs["name"]
        settings.HOME_SERVER_COAP_ADDRESS = confs["coap_address"]
        settings.HOME_SERVER_COAP_PORT = confs["coap_port"]
        settings.HOME_SERVER_PROXY_ADDRESS = confs["proxy_address"]
        settings.HOME_SERVER_PROXY_PORT = confs["proxy_port"]
        settings.USER_PASSWORD = confs["password"]
        settings.USER_EMAIL = confs["email"]

        if register_from_file():
            settings.WORKING_OFFLINE = False
            return get_configs() and get_services()

        elif settings.ALLOW_WORKING_OFFLINE:
            settings.WORKING_OFFLINE = True
            logger.info("Working Offline")
            return True
    except IOError:
        if register_from_scratch():
            settings.WORKING_OFFLINE = False
            return get_configs() and get_services()

        elif settings.ALLOW_WORKING_OFFLINE:
            settings.WORKING_OFFLINE = True
            logger.info("Working Offline")
            return True
    except KeyError as err:
        logger.error("Home Server configurations file improperly setted. "+str(err)+" is missing.")
        return False
    except:
        logger.error("Unknown Fatal Home Server Error!")
        return False

def register_from_file():
    """
        This function regist the HomeServer with the informations stored
        on the HomeServer configuration file. If the HomeServer is already registered
        on the cloud service this syncronizes all the HomeServer informations with it.
    """

    email = settings.USER_EMAIL
    password = settings.USER_PASSWORD
    server_id = settings.HOME_SERVER_ID

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
            data = {}
            data["name"] = settings.HOME_SERVER_NAME
            data["coap_address"] = settings.HOME_SERVER_COAP_ADDRESS
            data["coap_port"] = settings.HOME_SERVER_COAP_PORT
            data["proxy_address"] = settings.HOME_SERVER_PROXY_ADDRESS
            data["proxy_port"] = settings.HOME_SERVER_PROXY_PORT
            data["timeout"] = settings.HOME_SERVER_TIMEOUT

            resp = client.patch(base_url+"api/servers/"+str(server_id)+"/?fromserver=true",\
                                data=json.dumps(data))
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
            data = {}
            data["name"] = settings.HOME_SERVER_NAME
            data["coap_address"] = settings.HOME_SERVER_COAP_ADDRESS
            data["coap_port"] = settings.HOME_SERVER_COAP_PORT
            data["proxy_address"] = settings.HOME_SERVER_PROXY_ADDRESS
            data["proxy_port"] = settings.HOME_SERVER_PROXY_PORT
            data["multicast"] = settings.COAP_MULTICAST
            data["timeout"] = settings.HOME_SERVER_TIMEOUT

            try:
                resp = client.post(base_url+"api/servers/", data=json.dumps(data))
            except:
                logger.error("You do not have connection to the internet or the cloud server is down")
                return False

            if resp.status_code == 200:
                f = open(settings.SERVER_CONFIG_FILE, "w")
                js = json.loads(resp.text)
                for ele in js["servers"]:
                    if ele["coap_address"] == data["coap_address"]:
                        serv = ele
                        break

                serv["email"] = email
                serv["password"] = password
                json.dump(serv, f)
                f.close()
                logger.info("Server Registed Successfully")
                return True
            else:
                logger.error("Error ("+ str(resp.status_code)+"): "+str(resp.text))
                
                logger.error("Please check if data on "+settings.SERVER_CONFIG_FILE+\
                                " file is correct. If you prefer you can delete that file to register from scratch.")
                return False

def register_from_scratch():
    """
        This function regist the HomeServer from scratch, i.e. it asks the user for
        all the neede registration information. If a HomeServer is already registered
        on the cloud service with the information given by the user, it raises an error.
    """
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
                
                coap_ip_addr = settings.COAP_ADDR
                coap_port = settings.COAP_PORT
                multicast = settings.COAP_MULTICAST

                proxy_ip_addr = settings.PROXY_ADDR
                proxy_port = settings.PROXY_PORT

                if utils.validate_IPv4(coap_ip_addr):
                    data["coap_address"] = coap_ip_addr
                    data["coap_port"] = coap_port
                    data["multicast"] = multicast
                else:
                    print "Invalid CoAP Server IP address"
                
                if utils.validate_IPv4(proxy_ip_addr):
                    data["proxy_address"] = proxy_ip_addr
                    data["proxy_port"] = proxy_port
                    ip_ok = True
                else:
                    print "Invalid Proxy IP address"


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
                data["timeout"] = settings.HOME_SERVER_TIMEOUT
                resp = client.post(base_url+"api/servers/", data=json.dumps(data),\
                                    auth=(email, password))
            except:
                print "ERROR: You do not have connection to the internet or the cloud server is down"
                return False

            if resp.status_code == 200:
                print "Server Registed Successfully"
                try:
                    f = open(settings.SERVER_CONFIG_FILE, "w")
                    js = json.loads(resp.text)

                    for serv in js["servers"]:
                        if serv["coap_address"] == coap_ip_addr:
                            confs = serv
                            break

                    confs["email"] = email
                    confs["password"] = password
                    json.dump(confs, f)
                    f.close()

                    settings.HOME_SERVER_ID = confs["id"]
                    settings.HOME_SERVER_NAME = confs["name"]
                    settings.HOME_SERVER_COAP_ADDRESS = confs["coap_address"]
                    settings.HOME_SERVER_COAP_PORT = confs["coap_port"]
                    settings.HOME_SERVER_PROXY_ADDRESS = confs["proxy_address"]
                    settings.HOME_SERVER_PROXY_PORT = confs["proxy_port"]
                    settings.USER_PASSWORD = confs["password"]
                    settings.USER_EMAIL = confs["email"]

                    reg_ok = True
                except:
                    print "ERROR: Could not create "+settings.SERVER_CONFIG_FILE+" file."
                    sys.exit()
            else:
                js = json.loads(resp.text)
                if "coap_address" in js.keys():
                    print "ERROR ("+ str(resp.status_code)+"): "+str(js["coap_address"][0])
                    ip_ok = False
                    sys.exit(1)
                elif "name" in js.keys():
                    print "ERROR ("+ str(resp.status_code)+"): "+str(js["name"][0])
                    name_ok = False

                elif "detail" in js.keys():
                    print "ERROR ("+ str(resp.status_code)+"): "+str(js["detail"][0])
                    email_ok = False
                    cred_ok = False
                
                else:
                    print "ERROR ("+ str(resp.status_code)+"): "+str(resp.text)

    return True


def get_configs():
    """
        This function fetches all the needed HomeServer configurations from
        the cloud service and store them to the configuration files specified
        on the settings file.
    """
    core_configs_url = settings.CLOUD_BASE_URL+"api/configs/"
    email = settings.USER_EMAIL
    password = settings.USER_PASSWORD

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

def get_services():
    """
        This function fetches all the user services present on
        the cloud service and store them to the configuration file specified
        on the settings file.
    """
    services_url = settings.CLOUD_BASE_URL+"api/services/"
    email = settings.USER_EMAIL
    password = settings.USER_PASSWORD

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
