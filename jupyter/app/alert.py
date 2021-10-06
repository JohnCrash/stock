import numpy as np
from .nanovg import ui
from . import xueqiu,stock,shared,mylog,trend
from datetime import date,datetime,timedelta

class AlertManager:
    """
    用来管理报警
    """
    code2com = xueqiu.get_company_code2com()
    def __init__(self,frame):
        self._frame = frame
        b,ls = shared.fromRedis('alert')
        if not b:
            ls = []
        c = datetime.today()
        self._alerts = ls.copy()
        for a in ls:
            if c-a[3]>timedelta(days=7):#将太久前的给删除了
                self.deleteAlert(a)
    def getAlertByCode(self,code):
        """
        返回对应的报警设置，[[0.code,1.txt,2.cond,3.ts,4.state],..]
        """
        R = []
        for a in self._alerts:
            if a[0]==code:
                R.append(a)
        return R
    def editAlert(self,alert,x,y):
        """
        打开操作界面。x,y 弹出起点
        alert = [code,txt,cond,ts,state],如果只有[code,]将创建一个新的
        """
    def deleteAlert(self,alert):
        """
        从列表中删除报警器
        """
        #将删除的可以保存到数据库中
        self._alerts.remove(alert)
    def alertLoop(self,condf):
        """
        报警循环，将现有报警放入如条件函数判断是不是达到报警条件
        condf(code,cond)
        """
    def openui(self,alert,ax=None,ay=None,w=1024,h=240):
        """
        打开一个界面用来报警或者编辑报警
        """
        dw = 24
        th = ui.Themos.UI_TITLE_HEIGHT
        def onok(but):
            win.close()
        def oncancel(but):
            win.close()
        win = ui.window(self._frame,{'size':(w,h),'title':'%s %s'%(AlertManager.code2com[alert[0]][2],alert[0]),
            'child':[
            {'class':'input','label':'说明','pos':(2*dw+128,dw+th),'size':(w-3*dw-128,dw)},
            {'class':'input','label':'条件','pos':(2*dw+128,3*dw+th),'size':(w-3*dw-128,dw)},
            {'class':'image','img':'alert1.png','pos':(dw,dw+th),'size':(128,128),'color':(0,0,0,1)},
            {'class':'button','label':'确定','pos':(w-dw-96,h-dw-36),'size':(96,36),'onclick':onok},
            {'class':'button','label':'取消','pos':(w-2*dw-2*96,h-dw-36),'size':(96,36),'onclick':oncancel}]})
        if ax is not None:
            win.openAnimation(ax,ay)
        
