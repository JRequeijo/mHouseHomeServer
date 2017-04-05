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

## Communicator Default Timeout
COMM_TIMEOUT = 2