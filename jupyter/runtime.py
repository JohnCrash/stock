import xueqiu
import status
from datetime import datetime
import time
import subprocess
import threading
#import os

#os.chdir('d:/source/stock')
def jupyter():
    subprocess.run(['jupyter','lab'],cwd='d:\\source\\stock\\jupyter')

def jupyter_https():
    subprocess.run(['jupyter','lab'],cwd='d:\\source\\stock\\jupyter\\config')
threading.Thread(target=jupyter).start()
threading.Thread(target=jupyter_https).start()

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
        print("保存资金流向到数据库...")
        xueqiu.sinaFlowRT()
        status.saveflow()      
        print("开始从雪球下载数据")
        for i in range(3):
            r = subprocess.run(['node','d:/source/stock/download_script/download.js'])
            if r.returncode==0:
                break
        print("开始更新数据库...")
        status.update_status(process)
        print("更新完成。")          
        break
    elif t.hour==15:
        time.sleep(1)
        t = datetime.today()
    else:
        break
