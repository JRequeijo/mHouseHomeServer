"""
    This is the main settings file for the HomeServer.
    Here are specified all global variables that can be costumized to allow
    the HomeServer to work differently of its regular behaviour
"""
import utils
import os

__author__ = "Jose Requeijo Dias"

ROOT = os.path.dirname(__file__)


"""
Specification of the HomeServer configurations folder and file names.
Each one of these files stores the main configurations for the HomeServer.
These Files are updated each time the HomeServer start/restart and each time new
configurations are added/updated on the online cloud service.
"""
CONFIGS_ROOT = ROOT+"/config/"

SERVER_CONFIG_FILE = CONFIGS_ROOT+"serverconf.json"
DEVICE_TYPES_CONFIG_FILE = CONFIGS_ROOT+"device_types.json"
PROPERTY_TYPES_CONFIG_FILE = CONFIGS_ROOT+"property_types.json"
VALUE_TYPES_CONFIG_FILE = CONFIGS_ROOT+"value_types.json"
SERVICES_CONFIG_FILE = CONFIGS_ROOT+"services.json"

LOGGING_CONFIG_FILE = CONFIGS_ROOT+"logging.conf"

"""
Specification of the debug and the quiet settings for the HomeServer
Debug setting works to give or not exception stack like responses when an error
occurs instead of only the response error code.
Quiet setting works to enable/disable proxy logging to terminal.
"""
DEBUG = True
QUIET = True

"""
Specification of the IP address and port for the proxy and the CoAP server
"""
PROXY_ADDR = utils.get_my_ip()
PROXY_PORT = 8080

COAP_ADDR = utils.get_my_ip()
COAP_PORT = 5683
COAP_MULTICAST = False


"""
Specification of the default timeouts for the requests between the proxy and the
CoAP Server and for the monitoring of devices by the Home Server. All timeouts
are values on seconds.
"""
COMM_TIMEOUT = 5
DEVICES_MONITORING_TIMEOUT = 15
ENDPOINT_DEFAULT_TIMEOUT = 60

"""
Specification of the cloud service URL and the working offline setting for the
HomeServer.
When the ALLOW_WORKING_OFFLINE is set to False the HomeServer only works if it
has connection with the cloud service specified by the URL. If it is set to True
the HomeServer works without internet connection but the devices are only
reachable from the HomeServer"s REST API
"""
CLOUD_BASE_URL = "http://127.0.0.1:8000/"
ALLOW_WORKING_OFFLINE = False
