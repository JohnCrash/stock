#from app import tool
import threading
import time
import sys
isrun = True
def loop1():
    global isrun
    while isrun:
        print('i am loop1')
        time.sleep(1)

def loop2():
    global isrun
    while isrun:
        print('i am loop2')
        time.sleep(1)

threading.Thread(target=loop1).start()
threading.Thread(target=loop2).start()

sys.exit(0)
