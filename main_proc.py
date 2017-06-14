import threading
import sys

import proxy.proxy_main as proxy
import server.server_main as server
from register import register

if not register():
    sys.exit(4)

thr1 = threading.Thread(target=server.run_homeserver)
thr1.start()

thr2 = threading.Thread(target=proxy.run_proxy)
thr2.start()

end = False
while not end:
    thr1.join(1)
    if not thr1.is_alive():
        thr1 = threading.Thread(target=server.run_homeserver)
        thr1.start()

    thr2.join(1)
    if not thr2.is_alive():
        thr2 = threading.Thread(target=proxy.run_proxy)
        thr2.start()
