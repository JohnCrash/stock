import xueqiu
import status
from datetime import datetime
import time
import subprocess
import threading
import platform
import config
import mylog
#import os
log = mylog.init('runtime.log',name='runtime')
download_done_day = -1
def process(i):
    pass

def jupyter():
    subprocess.run(['jupyter','lab'])

if platform.platform()[:7]=='Windows':
    print("启动jupyter lab")
    threading.Thread(target=jupyter).start()

while True:
    t = datetime.today()
    if t.hour>=9 and t.hour<15:
        try:
            xueqiu.updateAllRT()
            time.sleep(1)
        except Exception as e:
            log.error(str(e))
            print(e)
    elif t.hour==15 and t.day!=download_done_day:
        print("5分钟后开始更新数据库...")
        time.sleep(5*60)
        print("保存资金流向到数据库...")
        try:
            xueqiu.sinaFlowRT()
            status.saveflow()      
        except Exception as e:
            log.error(str(e))
            print(e)
        print("开始从雪球下载数据")
        for i in range(3):
            r = subprocess.run(['node',config.download_js])
            if r.returncode==0:
                log.info("done")
                break
            else:
                log.warning("%s下载出现问题"%(config.download_js))
        print("开始更新数据库...")
        status.update_status(process)
        print("更新完成。")          
        download_done_day = t.day
    else:
        time.sleep(10)
