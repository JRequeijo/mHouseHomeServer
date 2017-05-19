import socket
import os
import sys

UP = 1
DOWN = 2
STAT = 3
ACK = "OK"

SERVER_ADDRESS = "./homeserver_sock"

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