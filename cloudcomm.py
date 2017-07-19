import threading
import mhouse_cloudcomm

from aws_boto_client import AWSCommunicator

aws_comm = AWSCommunicator()

def register_device_on_cloud_platforms(device):
    mhouse_t = threading.Thread(target=mhouse_cloudcomm.regist_device_on_cloud,\
                                args=(device,))
    mhouse_t.start()

    aws_t = threading.Thread(target=aws_comm.register_new_device,\
                             args=(device.name+"-"+str(device.id),\
                                    device.state))
    aws_t.start()

def unregister_device_from_cloud_platforms(device):
    mhouse_t = threading.Thread(target=mhouse_cloudcomm.unregist_device_from_cloud,\
                                args=(device.id,))
    mhouse_t.start()

    aws_t = threading.Thread(target=aws_comm.unregister_device,\
                             args=(device.name+"-"+str(device.id),))
    aws_t.start()

def notify_cloud_platforms(device):
    mhouse_t = threading.Thread(target=mhouse_cloudcomm.notify_cloud,\
                                args=(device.state,))
    mhouse_t.start()

    aws_t = threading.Thread(target=aws_comm.notify_shadow,\
                                args=(device.name+"-"+str(device.id),\
                                    device.state,))
    aws_t.start()