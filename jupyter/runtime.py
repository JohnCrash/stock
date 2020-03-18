import xueqiu
import status
from datetime import datetime
import time
import subprocess
import threading

def jupyter():
    subprocess.run(['jupyter','lab'],shell=True)

threading.Thread(target=jupyter).start()

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
print("5分钟后开始更新数据库...")
while True:
    if t.hour==15 and t.minute==5:
        print("开始从雪球下载数据")
        subprocess.run(['node','./stock/download_script/download.js'])
        print("开始更新数据库...")
        status.update_status(process)
        print("更新完成。")
        break
    elif t.hour==15:
        time.sleep(1)
        t = datetime.today()
    else:
        break
