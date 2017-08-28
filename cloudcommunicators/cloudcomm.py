import threading
import os
import sys

import settings
import mhouse_comm

if settings.AWS_INTEGRATION:
    from aws_comm import AWSCommunicator
    try:
        credentials=(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        aws_communicator = AWSCommunicator(credentials)
    except:
        aws_communicator = AWSCommunicator()

def register_device_on_cloud_platforms(device):
    mhouse_t = threading.Thread(target=mhouse_comm.regist_device_on_cloud,\
                                args=(device,))
    mhouse_t.start()

    if settings.AWS_INTEGRATION:
        aws_t = threading.Thread(target=aws_communicator.register_new_device,\
                                args=(device.name+"-"+str(device.id),\
                                        device.state))
        aws_t.start()

def unregister_device_from_cloud_platforms(device):
    mhouse_t = threading.Thread(target=mhouse_comm.unregist_device_from_cloud,\
                                args=(device.id,))
    mhouse_t.start()

    if settings.AWS_INTEGRATION:
        aws_t = threading.Thread(target=aws_communicator.unregister_device,\
                                args=(device.name+"-"+str(device.id),))
        aws_t.start()

def notify_cloud_platforms(device):
    mhouse_t = threading.Thread(target=mhouse_comm.notify_cloud,\
                                args=(device.state,))
    mhouse_t.start()

    if settings.AWS_INTEGRATION:
        aws_t = threading.Thread(target=aws_communicator.notify_shadow,\
                                    args=(device.name+"-"+str(device.id),\
                                        device.state,))
        aws_t.start()