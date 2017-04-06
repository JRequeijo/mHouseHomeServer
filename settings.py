### Home Server Main Settings ###
import utils

## Configurations root folder and files declaration
CONFIGS_ROOT = "config/"

SERVER_CONFIG_FILE = CONFIGS_ROOT+"serverconf.json"
DEVICE_TYPES_CONFIG_FILE = CONFIGS_ROOT+"device_types.json"
PROPERTY_TYPES_CONFIG_FILE = CONFIGS_ROOT+"property_types.json"
VALUE_TYPES_CONFIG_FILE = CONFIGS_ROOT+"value_types.json"
SERVICES_CONFIG_FILE = CONFIGS_ROOT+"services.json"

LOGGING_CONFIG_FILE = CONFIGS_ROOT+"logging.conf"

## Debugging and Quiet options
DEBUG = True
QUIET = True

## Proxy IP address and port
PROXY_ADDR = utils.get_my_ip()
PROXY_PORT = 8080

## CoAP Server IP Address and Port
COAP_ADDR = "192.168.1.67"    # "224.0.1.187"
COAP_PORT = 5683
COAP_MULTICAST = False


## Communicator Default Timeout
COMM_TIMEOUT = 2

## Online Platform base URL
CLOUD_BASE_URL = "http://127.0.0.1:8000/"
