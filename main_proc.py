
import time
import os
import getopt
import sys
import socket
import threading
from multiprocessing import Process

from proxy_main import run_proxy
from server_main import run_home_server

UP = 1
DOWN = 2
STAT = 3
ACK = "OK"

server_address = "./homeserver_sock"

def usage():
    print "\nUsage: python main_proc.py <option>\n"
    print "Option must be one of the following:"
    print "\t -u or --up -> Start the Home Server"
    print "\t -d or --down -> Shut the Home Server Down"
    print "\t -s or --stat -> Get the Home Server Status\n"

def create_server_socket(server_address):
    # Make sure the socket does not already exist
    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    return sock

def create_client_socket(server_address):
    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    return sock

def connect_to_socket(sock, server_address, kill_on_exception=False):
    # Connect the socket to the port where the server is listening
    # print >>sys.stderr, 'connecting to %s' % server_address
    try:
        sock.connect(server_address)
        return True
    except socket.error, msg:
        if kill_on_exception:
            print >>sys.stderr, msg
            sys.exit(1)
        else:
            return False

def send_message(sock, code):
    # Send data
    try:
        message = str(code)+"\0"
        # print >>sys.stderr, 'sending "%s"' % message
        sock.sendall(message)
    except:
        print "Unknown Fatal Error"
        sys.exit(1)

def receive_code_message(connection):
    # Receive the data in small chunks and retransmit it
    end = False
    code = None
    while not end:
        data = connection.recv(1)
        # print >>sys.stderr, 'received "%s"' % data
        if data == str(DOWN):
            send_message(connection, ACK)
            code = data
            end = True
        if data == str(STAT):
            send_message(connection, "Proxy: UP\nCoAP Server: UP")
            code = data
            end = True
        if data == "\0":
            end = True
    return int(code)

def receive_message(sock):
    end = False
    message = ""
    while not end:
        data = sock.recv(1)
        if data == "\0":
            end = True
        else:
            message += str(data)

    return message
#
#
def monitor_proxy(term_event, term_lock, creation_event):

    proxy_proc = Process(target=run_proxy)
    proxy_proc.start()
    print "PROXY PROCCESS: "+str(proxy_proc.pid)

    creation_event.set()
    printed = False
    while True:
        if proxy_proc.is_alive():
            pass
        else:
            print "EXIT: "+str(proxy_proc.exitcode)
            if proxy_proc.exitcode != 4:
                print "PROXY is DEAD. Restarting"
                proxy_proc = Process(target=run_proxy)
                proxy_proc.start()
                print "PROXY PROCCESS: "+str(proxy_proc.pid)
                print "PROXY ALIVE AGAIN"
                printed = False
            else:
                term_event.set()
                term_lock.acquire()
                break

        if term_event.isSet():
            term_lock.acquire()
            proxy_proc.terminate()
            break
        else:
            time.sleep(2)

    term_lock.release()

def monitor_coapserver(term_event, term_lock, creation_event):

    creation_event.wait()
    server_proc = Process(target=run_home_server)
    server_proc.start()
    print "SERVER PROCCESS: "+str(server_proc.pid)

    creation_event.clear()
    printed = False
    while True:
        if server_proc.is_alive():
            pass
        else:
            print "SERVER is DEAD. Restarting"
            server_proc = Process(target=run_home_server)
            server_proc.start()
            print "SERVER PROCCESS: "+str(server_proc.pid)
            print "SERVER ALIVE AGAIN"
            printed = False

        if term_event.isSet():
            term_lock.acquire()
            server_proc.terminate()
            break
        else:
            time.sleep(2)

    term_lock.release()

def home_server_main_process():

    term_event = threading.Event()
    term_lock_proxy = threading.Lock()
    term_lock_coapserver = threading.Lock()

    creation_event = threading.Event()

    proxy_mon_thr = threading.Thread(target=monitor_proxy,args=(term_event,\
                                                            term_lock_proxy, creation_event,))
    proxy_mon_thr.start()

    coapserver_mon_thr = threading.Thread(target=monitor_coapserver,args=(term_event,\
                                                        term_lock_coapserver, creation_event))
    coapserver_mon_thr.start()

    create_server_socket(server_address)

    # Bind the socket to the port
    # print >>sys.stderr, 'starting up on %s' % server_address
    sock.bind(server_address)

    # Listen for incoming connections
    sock.listen(1)
    terminate = False
    while not terminate:
        # Wait for a connection
        # print >>sys.stderr, 'waiting for a connection'
        connection, client_address = sock.accept()
        try:
            # print >>sys.stderr, 'connection from', client_address
            code = receive_code_message(connection)
            if code == DOWN:
                print "EXITING"
                term_event.set()
                terminate = True
        finally:
            # Clean up the connection
            connection.close()

    term_lock_proxy.acquire()
    term_lock_coapserver.acquire()
    print "EXIT"
    term_lock_proxy.release()
    term_lock_coapserver.release()
    sys.exit(0)

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
        code = UP
        break
    elif opt in ("-d", "--down"):
        code = DOWN
        break
    elif opt in ("-s", "--stat"):
        code = STAT
        break
    else:
        usage()
        sys.exit(2)

if code != -1:
    sock = create_client_socket(server_address)
    connected = connect_to_socket(sock, server_address)

    # print "CONNECTED: "+str(connected)
    if code == UP:
        if not connected:
            print "\nStarting Home Server..."
            pid = os.fork()
            if pid:
                pass
            else:
                home_server_main_process()

            print "Home Server Started Successfully!\n"
        else:
            send_message(sock, STAT)
            msg = receive_message(sock)
            print "ERROR: Home Server already running"

    if code == DOWN:
        if connected:
            print "\nShutting Home Server Down..."
            send_message(sock, code)
            msg = receive_message(sock)
            if msg == ACK:
                print "Home Server is successfully down!\n"
        else:
            print "ERROR: Home Server is not running"

    if code == STAT:
        if connected:
            print "\nGetting Home Server Status..."
            send_message(sock, code)
            msg = receive_message(sock)
            print "\nHome Server Status:"
            print msg
            print "\n"
        else:
            print "ERROR: Home Server is not running"

    if connected:
        sock.close()
else:
    usage()
    