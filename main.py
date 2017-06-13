from multiprocessing import Process

import proxy.proxy_main as proxy
import server.server_main as server

proxy.register_homeserver()
#
####### Initialize Home Server ########
server_proc = Process(target=server.run_homeserver)
server_proc.start()

proxy.run_proxy(False)

server_proc.join()
