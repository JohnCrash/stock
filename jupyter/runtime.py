import xueqiu
from datetime import datetime
import time
import os

t = datetime.today()
while t.hour<15:
    try:
        xueqiu.updateAllRT()
        time.sleep(1)
        t = datetime.today()
    except Exception as e:
        print(e)

while True:
    if t.hour==15 and t.minute==5:
        os.execvp('node',('node','./stock/download_script/download.js'))
        break
    elif t.hour==15:
        time.sleep(1)
        t = datetime.today()
    else:
        break
