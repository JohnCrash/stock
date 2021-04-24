from datetime import datetime
import time
import sys
import subprocess
import threading
import platform

from app import stock
from app import xueqiu
from app import status
from app import config
from app import ziprt
from app import shared
from app import mylog

if __name__=='__main__':
    #import os
    t = datetime.today()
    #如果是autorun模式仅仅在周1-5的早晨6-9点开机才有效
    if len(sys.argv)>1 and sys.argv[1]=='autorun':
        if t.hour>=6 and t.hour<=15 and t.weekday()>=0:
            pass #继续运行
        else:
            sys.exit() #退出
    log = mylog.init('runtime.log',name='runtime')
    _,download_done_day = shared.fromRedis("last_download_day")
    def process(i):
        pass

    def jupyter():
        subprocess.run(['jupyter','lab'])

    def launapp():
        if t.hour>=6 and t.hour==9 and t.weekday()<5 and t.weekday()>=0:
            print("启动软件并且进行多屏幕布局...")
            subprocess.run(config.ths_app)
            subprocess.run(config.tdx_app)
            subprocess.run(config.chrome_app)

    if platform.platform()[:7]=='Windows':
        print("启动jupyter lab")
        threading.Thread(target=jupyter).start()
        threading.Thread(target=launapp).start()

    while True:
        t = datetime.today()
        if t.hour>=9 and t.hour<15 and stock.isTransDay() and stock.isTransTime():
            try:
                xueqiu.updateAllRT()
                time.sleep(1)
            except Exception as e:
                log.error(str(e))
                print(e)
        elif t.hour>=15 and t.day!=download_done_day and stock.isTransDay():
            if t.hour==15:
                print("5分钟后开始更新数据库...")
                time.sleep(5*60)
            
            try:
                print("保存sina资金流向到数据库...")
                xueqiu.sinaFlowRT()
                status.saveflow()
            except Exception as e:
                mylog.printe(e)
            try:                
                print("将EM资金流存入数据库...")
                xueqiu.emflow2db() #将emflow保存到数据库中
            except Exception as e:
                mylog.printe(e)
            try:                
                print("将EM分类概念K存入数据库...")
                xueqiu.emkline2db() 
            except Exception as e:
                mylog.printe(e)             
            try:
                print("开始从雪球下载数据")
                b = False
                for i in range(3):
                    r = subprocess.run(['node',config.download_js])
                    if r.returncode==0:
                        log.info("done")
                        b = True
                        break
                    else:
                        log.warning("%s下载出现问题"%(config.download_js))
                if not b:
                    print('========xueqiu下载出现问题!==========')
            except Exception as e:
                mylog.printe(e)                 
            #新版本仅仅跟踪msci个股
            print("开始更新缓存...")
            xueqiu.update_today_period([240,60,30,15,5])
            print("将RT数据压缩存盘...")
            ziprt.saveRT()
            ziprt.bxzj2db()
            print("更新完成。")
            download_done_day = t.day
            shared.toRedis(download_done_day,"last_download_day")
        else:
            time.sleep(10)


