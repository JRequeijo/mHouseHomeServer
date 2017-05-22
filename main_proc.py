
import time
import os
import getopt
import sys
import socket
import threading
import psutil
from multiprocessing import Process

import proxy_main
import server_main

import ps_socket_utils as sock_util

def usage():
    print "\nUsage: python main_proc.py <option>\n"
    print "Option must be one of the following:"
    print "\t -u or --up -> Start the Home Server"
    print "\t -d or --down -> Shut the Home Server Down"
    print "\t -s or --stat -> Get the Home Server Status\n"


#
#
def home_server_main_process():

    term_event = threading.Event()
    server_term_event = threading.Event()

    proxy_main.register_homeserver()

    server_proc = Process(target=server_main.run_home_server, args=(psutil.Process(), term_event, server_term_event,))
    server_proc.start()
    print "PROXY PROCESS: "+str(os.getpid())
    print "SERVER PROCCESS: "+str(server_proc.pid)

    proxy_main.run_proxy(psutil.Process(server_proc.pid), term_event, server_term_event)

#
#
#############
#### MAIN
try:
    if not sys.argv[1:]:
        usage()
        sys.exit(2)

    opts, args = getopt.getopt(sys.argv[1:], "huds", ["help", "up", "down", "stat"])
except:
    usage()
    sys.exit(2)

code = -1
for opt, arg in opts:
    if opt in ("-h", "--help"):
        usage()
        sys.exit()
    elif opt in ("-u", "--up"):
        code = sock_util.UP
        break
    elif opt in ("-d", "--down"):
        code = sock_util.DOWN
        break
    elif opt in ("-s", "--stat"):
        code = sock_util.STAT
        break
    else:
        usage()
        sys.exit(2)

if code != -1:
    sock = sock_util.create_client_socket(sock_util.SERVER_ADDRESS)
    connected = sock_util.connect_to_socket(sock, sock_util.SERVER_ADDRESS)

    # print "CONNECTED: "+str(connected)
    if code == sock_util.UP:
        if not connected:
            print "\nStarting Home Server..."
            pid = os.fork()
            if pid:
                pass
            else:
                home_server_main_process()

            print "Home Server Started Successfully!\n"
        else:
            sock_util.send_message(sock, sock_util.STAT)
            msg = sock_util.receive_message(sock)
            print "ERROR: Home Server already running"

    if code == sock_util.DOWN:
        if connected:
            print "\nShutting Home Server Down..."
            sock_util.send_message(sock, code)
            msg = sock_util.receive_message(sock)
            if msg == sock_util.ACK:
                print "Home Server is successfully down!\n"
        else:
            print "ERROR: Home Server is not running"

    if code == sock_util.STAT:
        if connected:
            print "\nGetting Home Server Status..."
            sock_util.send_message(sock, code)
            msg = sock_util.receive_message(sock)
            print "\nHome Server Status:"
            print msg
            print "\n"
        else:
            print "ERROR: Home Server is not running"

    if connected:
        sock.close()
else:
    usage()
    