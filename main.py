import sys
from multiprocessing import Process

import proxy.proxy_main as proxy
import server.server_main as server
from cloudcommunicators.register import register

if not register():
    sys.exit(4)

#
####### Initialize Home Server ########
server_proc = Process(target=server.run_homeserver)
server_proc.start()

proxy.run_proxy()

server_proc.join()
