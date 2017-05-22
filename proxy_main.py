import json
import sys
import logging
import thread
import threading
import time
import os
# import getopt
import psutil

from multiprocessing import Process
from functools import wraps
from bottle import Bottle, run, request, response, abort, debug

from coapthon import defines

import settings
import ps_socket_utils as sock_util
from proxy.register import register
from proxy.communicator import Communicator
from server.homeserver import HomeServer
from utils import AppError, coap2http_code

from server_main import run_home_server

logging.config.fileConfig(settings.LOGGING_CONFIG_FILE, disable_existing_loggers=False)

logger = logging.getLogger("proxylog")


def log_to_logger(fn):
    '''
    Wrap a Bottle request so that a log line is emitted after it's handled.
    (This decorator can be extended to take the desired logger as a param.)
    '''
    @wraps(fn)
    def _log_to_logger(*args, **kwargs):
        actual_response = fn(*args, **kwargs)
        # modify this to log exactly what you need:
        logger.info("From: %s - %s %s %s" % (request.remote_addr, request.method, request.url,\
                                                response.status))
        return actual_response
    return _log_to_logger


proxy = Bottle()
proxy.install(log_to_logger)
# backup = BackupSaver("housebackup.json", house)

comm = Communicator(settings.COAP_ADDR, settings.COAP_PORT)

def save_server_confs(new_name):
    try:
        f = open("serverconf.json", "r")
        data = json.load(f)
        f.close()

        data["name"] = new_name
        f = open("serverconf.json", "w")
        json.dump(data, f)
        f.close()
    except Exception as err:
        logger.error(err.message)
#
# ################  PROXY ENDPOINTS  ##################
# ###### Server Root Endpoints########
@proxy.get("/")
@proxy.get("/info")
def get_info():
    try:
        resp = comm.get("/info", timeout=settings.COMM_TIMEOUT)
    except AppError as err:
        abort(504, err.msg)

    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

@proxy.put("/info")
def update_info():
    if request.headers["content-type"] == "application/json":
        try:
            body = request.json
        except:
            abort(400, "Request body not properly json formated")

        if body is not None:
            try:
                data = {}
                data["name"] = body["name"]

                resp = comm.put("/info", json.dumps(data), timeout=settings.COMM_TIMEOUT)
                resp = comm.get_response(resp)

                err_check = check_error_response(resp)
                if err_check is not None:
                    abort(err_check[0], err_check[1])

                thread.start_new_thread(save_server_confs, (data["name"],))

                return send_response(resp.payload, resp.code)
            except KeyError as err:
                abort(400, "Field ("+err.message+") missing on request json body")
        else:
            abort(400, "Request body formated in json is missing")
    else:
        abort(415, "Request body content format not json")

#
### Server Services Endpoints ###
@proxy.get("/services")
def get_server_services():
    try:
        resp = comm.get("/services", timeout=settings.COMM_TIMEOUT)
    except AppError as err:
        abort(504, err.msg)

    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)


@proxy.put("/services")
def update_server_services():
    if request.headers["content-type"] == "application/json":
        try:
            body = request.json
        except:
            abort(400, "Request body not properly json formated")

        if body is not None:
            try:
                data = {}
                data["SERVICES"] = body["SERVICES"]

                resp = comm.put("/services", json.dumps(data),\
                                                        timeout=settings.COMM_TIMEOUT)
                resp = comm.get_response(resp)

                err_check = check_error_response(resp)
                if err_check is not None:
                    abort(err_check[0], err_check[1])

                return send_response(resp.payload, resp.code)
            except KeyError as err:
                abort(400, "Field ("+err.message+") missing on request json body")
            # except:
            #     abort(500, "Fatal Server Error")
        else:
            abort(400, "Request body formated in json is missing")
    else:
        abort(415, "Request body content format not json")
#
### Server Configs Endpoints ###
@proxy.get("/configs")
def get_server_configurations():
    try:
        resp = comm.get("/configs", timeout=settings.COMM_TIMEOUT)
    except AppError as err:
        abort(504, err.msg)

    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)


@proxy.put("/configs")
def update_server_configurations():
    if request.headers["content-type"] == "application/json":
        try:
            c_type = request.query.get("type")
        except:
            abort(400, "Request query must specify a type of the config to update")
        try:
            body = request.json
        except:
            abort(400, "Request body not properly json formated")

        if body is not None:
            try:
                data = {}
                if c_type in ["SCALAR_TYPES", "ENUM_TYPES", "PROPERTY_TYPES", "DEVICE_TYPES"]:
                    data[c_type] = body[c_type]
                else:
                    abort(400, "Request query must be one of SCALAR_TYPES, ENUM_TYPES, PROPERTY_TYPES or DEVICE_TYPES")

                resp = comm.put("/configs?type="+str(c_type), json.dumps(data),\
                                                        timeout=settings.COMM_TIMEOUT)
                resp = comm.get_response(resp)

                err_check = check_error_response(resp)
                if err_check is not None:
                    abort(err_check[0], err_check[1])

                return send_response(resp.payload, resp.code)
            except KeyError as err:
                abort(400, "Field ("+str(err)+") missing on request json body")
            # except:
            #     abort(500, "Fatal Server Error")
        else:
            abort(400, "Request body formated in json is missing")
    else:
        abort(415, "Request body content format not json")

#
# ###### Devices List Endpoints########
@proxy.get("/devices")
def get_all_devices():
    try:
        resp = comm.get("/devices", timeout=settings.COMM_TIMEOUT)
    except AppError as err:
        abort(504, err.msg)
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

@proxy.post("/devices")
def regist_device():
    if request.headers["content-type"] == "application/json":
        try:
            body = request.json
        except:
            abort(400, "Request body not properly json formated")

        if body is not None:
            try:
                resp = comm.post("/devices", json.dumps(body), timeout=settings.COMM_TIMEOUT)
            except AppError as err:
                abort(504, err.msg)
            resp = comm.get_response(resp)

            err_check = check_error_response(resp)
            if err_check is not None:
                abort(err_check[0], err_check[1])

            return send_response(resp.payload, resp.code)
        else:
            abort(400, "Request body formated in json is missing")
    else:
        abort(415, "Request body content format not json")



#
# ###### Single Device Endpoints########
@proxy.get("/devices/<device_id:int>")
def get_device(device_id):
    try:
        resp = comm.get("/devices/"+str(device_id), timeout=settings.COMM_TIMEOUT)
    except AppError as err:
        abort(504, err.msg)
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

@proxy.delete("/devices/<device_id:int>")
def unregist_device(device_id):
    try:
        resp = comm.delete("/devices/"+str(device_id), timeout=settings.COMM_TIMEOUT)
    except AppError as err:
        abort(504, err.msg)
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

@proxy.put("/devices/<device_id:int>")
def update_device_info(device_id):
    if request.headers["content-type"] == "application/json":
        try:
            body = request.json
        except:
            abort(400, "Request body not properly json formated")

        if body is not None:
            try:
                data = {}
                data["name"] = body["name"]

                resp = comm.put("/devices/"+str(device_id), json.dumps(data), timeout=settings.COMM_TIMEOUT)
                resp = comm.get_response(resp)

                err_check = check_error_response(resp)
                if err_check is not None:
                    abort(err_check[0], err_check[1])

                return send_response(resp.payload, resp.code)
            except ValueError as err:
                abort(400, "Invalid service name ("+body["name"]+")")
            except:
                abort(500, "Fatal Server Error")
        else:
            abort(400, "Request body formated in json is missing")
    else:
        abort(415, "Request body content format not json")

#
# ###### Device State Endpoints########
@proxy.get("/devices/<device_id:int>/state")
def get_device_state(device_id):
    try:
        resp = comm.get("/devices/"+str(device_id)+"/state", timeout=settings.COMM_TIMEOUT)
    except AppError as err:
        abort(504, err.msg)
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

@proxy.put("/devices/<device_id:int>/state")
def change_device_state(device_id):
    if request.headers["content-type"] == "application/json":
        try:
            body = request.json
        except:
            abort(400, "Request body not properly json formated")

        if body is not None:
            try:
                resp = comm.put("/devices/"+str(device_id)+"/state", json.dumps(body), timeout=settings.COMM_TIMEOUT)
            except AppError as err:
                abort(504, err.msg)
            resp = comm.get_response(resp)

            err_check = check_error_response(resp)
            if err_check is not None:
                abort(err_check[0], err_check[1])

            return send_response(resp.payload, resp.code)
        else:
            abort(400, "Request body formated in json is missing")
    else:
        abort(415, "Request body content format not json")


#
# ###### Device Type Endpoints########
@proxy.get("/devices/<device_id:int>/type")
def get_device_type(device_id):
    try:
        resp = comm.get("/devices/"+str(device_id)+"/type", timeout=settings.COMM_TIMEOUT)
    except AppError as err:
        abort(504, err.msg)
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)


#
# ###### Device Services Endpoints########
@proxy.get("/devices/<device_id:int>/services")
def get_device_services(device_id):
    try:
        resp = comm.get("/devices/"+str(device_id)+"/services", timeout=settings.COMM_TIMEOUT)
    except AppError as err:
        abort(504, err.msg)
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

@proxy.put("/devices/<device_id:int>/services")
def update_services_on_device(device_id):
    if request.headers["content-type"] == "application/json":
        try:
            body = request.json
        except:
            abort(400, "Request body not properly json formated")

        if body is not None:
            print body
            if isinstance(body, list):
                try:
                    data = []
                    for n in body:
                        serv = int(n)
                        data.append(serv)

                    resp = comm.put("/devices/"+str(device_id)+"/services", json.dumps(data))
                    resp = comm.get_response(resp)

                    err_check = check_error_response(resp)
                    if err_check is not None:
                        abort(err_check[0], err_check[1])

                    return send_response(resp.payload, resp.code)

                except:
                    abort(400, "Request body must specify a list of service ids in json format")
            else:
                abort(400, "Request body must specify a list of service ids in json format")
        else:
            abort(400, "Request body formated in json is missing")
    else:
        abort(415, "Request body content format not json")

@proxy.post("/devices/<device_id:int>/services")
def add_service_to_device(device_id):
    if request.headers["content-type"] == "application/json":
        try:
            body = request.json
        except:
            abort(400, "Request body not properly json formated")

        if body is not None:
            if isinstance(body, list):
                try:
                    data = []
                    for n in body:
                        serv = int(n)
                        data.append(serv)

                    resp = comm.post("/devices/"+str(device_id)+"/services", json.dumps(data))
                    resp = comm.get_response(resp)

                    err_check = check_error_response(resp)
                    if err_check is not None:
                        abort(err_check[0], err_check[1])

                    return send_response(resp.payload, resp.code)

                except:
                    abort(400, "Request body must specify a list of service ids in json format")
            else:
                abort(400, "Request body must specify a list of service ids in json format")
        else:
            abort(400, "Request body formated in json is missing")
    else:
        abort(415, "Request body content format not json")


@proxy.delete("/devices/<device_id:int>/services")
def delete_service_from(device_id):

    try:
        s_id = request.query.get("id")
        s_id = int(s_id)
    except:
        abort(400, "Request query must specify a service id to delete")

    resp = comm.delete("/devices/"+str(device_id)+"/services?id="+str(s_id))
    resp = comm.get_response(resp)

    err_check = check_error_response(resp)
    if err_check is not None:
        abort(err_check[0], err_check[1])

    return send_response(resp.payload, resp.code)

#
# ######## Helper Functions #######

# #change to use authentication framework
# def authorize(request):
#     if (request.environ.get("REMOTE_ADDR") == get_my_ip()) and (request.headers["user-agent"] == "app-communicator"):
#         return True
#     else:
#         return False

def send_response(data, code=None):
    if code is not None:
        response.status = coap2http_code(code)[0]
    response.set_header("Content-Type", "application/json")
    return data

def check_error_response(response):
    if response.code >= defines.Codes.ERROR_LOWER_BOUND:
        code, phrase = coap2http_code(response.code)

        if response.payload is not None:
            d = json.loads(response.payload)
            return (code, d["error_msg"])
        else:
            return (code, phrase)
    else:
        return None

#
######### Handle Errors #############
@proxy.error(400)
@proxy.error(404)
@proxy.error(403)
@proxy.error(405)
@proxy.error(415)
@proxy.error(500)
@proxy.error(504)
def errorHandler(error):
    return send_response(json.dumps({"error_code": error.status_code, "error_msg": error.body}))

#
####### Initialize Home Server ########
def register_homeserver():
    if not register():
        sys.exit(4)

def monitor_coapserver(server_proc, term_event, server_term_event):

    printed = False
    while True:
        if server_proc.is_running():
            print "Server is ALIVE"
        else:
            print "SERVER is DEAD. Restarting"
            new_server_proc = Process(target=run_home_server, args=(psutil.Process(), term_event, server_term_event,))
            new_server_proc.start()

            server_proc = psutil.Process(new_server_proc.pid)

            print "SERVER PROCCESS: "+str(new_server_proc.pid)
            print "SERVER ALIVE AGAIN"
            printed = False

        if term_event.isSet():
            print "ending server monitor"
            print "Ending Server Process"
            server_proc.terminate()
            break
        else:
            time.sleep(2)

    server_term_event.set()
    sys.exit(0)

def command_line_listener(proxy_proc, term_event, server_term_event):
    sock = sock_util.create_server_socket(sock_util.SERVER_ADDRESS)

    # Bind the socket to the port
    # print >>sys.stderr, 'starting up on %s' % server_address
    sock.bind(sock_util.SERVER_ADDRESS)

    # Listen for incoming connections
    sock.listen(1)
    terminate = False
    while not terminate:
        # Wait for a connection
        # print >>sys.stderr, 'waiting for a connection'
        connection, client_address = sock.accept()
        try:
            # print >>sys.stderr, 'connection from', client_address
            code = sock_util.receive_code_message(connection)
            if code == sock_util.DOWN:
                print "EXITING"
                term_event.set()
                terminate = True
        finally:
            # Clean up the connection
            connection.close()

    print "Waiting for closure"
    server_term_event.wait()
    proxy_proc.terminate()
    print "Proxy Endend"
    sys.exit(0)

def run_proxy(server_proc, term_event, server_term_event):

    coapserver_mon_thr = threading.Thread(target=monitor_coapserver, args=(server_proc, term_event, server_term_event,))
    coapserver_mon_thr.start()

    command_line_listener_thr = threading.Thread(target=command_line_listener, args=(psutil.Process(), term_event, server_term_event,))
    command_line_listener_thr.start()

    debug(settings.DEBUG)
    run(proxy, host=settings.PROXY_ADDR, port=settings.PROXY_PORT, quiet=settings.QUIET)

# if __name__ == "__main__":
#     run_proxy()

