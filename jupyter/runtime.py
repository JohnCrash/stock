import xueqiu
import status
from datetime import datetime
import time
import subprocess
import threading
"""
def jupyter():
    subprocess.run(['jupyter','lab'])

threading.Thread(target=jupyter).start()
"""
t = datetime.today()
while t.hour<15:
    try:
        xueqiu.updateAllRT()
        time.sleep(1)
        t = datetime.today()
    except Exception as e:
        print(e)
def process(i):
    pass
while True:
    if t.hour==15 and t.minute==5:
        subprocess.run(['node','./stock/download_script/download.js'])
        status.update_status(process)
        break
    elif t.hour==15:
        time.sleep(1)
        t = datetime.today()
    else:
        break
