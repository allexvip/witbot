import threading
import os

th1 = threading.Thread(target=os.system, args=('python run_client.py',))
th2 = threading.Thread(target=os.system, args=('python run_bot.py',))
#lock = threading.Lock()
th1.start()
th2.start()

th1.join()
th2.join()

