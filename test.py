
import time
import os
import getopt
import sys
import socket
import threading
import multiprocessing
import psutil
from multiprocessing import Process, Queue, Semaphore

#
#

def func(term_event):
    print "Start thread 1"
    time.sleep(5)
    raise Exception


def func2(term_event):
    print "start thread 2"
    while not term_event.is_set():
        pass

term_event = threading.Event()

thr1 = threading.Thread(target=func, args=(term_event,))
thr1.start()

thr2 = threading.Thread(target=func2, args=(term_event,))
thr2.start()

end = False
while not end:
    thr1.join(1)
    if not thr1.is_alive():
        thr1 = threading.Thread(target=func, args=(term_event,))
        thr1.start()
    else:
        print "thread 1 is alive"

    thr2.join(1)
    if not thr2.is_alive():
        thr2 = threading.Thread(target=func2, args=(term_event,))
        thr2.start()
    else:
        print "thread 2 is alive"
