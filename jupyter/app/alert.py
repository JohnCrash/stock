import numpy as np
import threading
import sdl2
from .nanovg import ui,vg
from . import xueqiu,stock,shared,mylog,trend
from datetime import date,datetime,timedelta

ENABLE = 1
DISABLE = 0
class AlertManager:
    """
    用来管理报警
    """
    code2com = xueqiu.get_company_code2com()
    code2i = xueqiu.get_company_code2i()
    def __init__(self,frame):
        self._frame = frame
        self._k = None
        self._d = None
        self._isopen = False
        self._globals = {'macd':stock.macdV,'boll':stock.boll,'ma':stock.ma,'rsi':stock.rsi,'cci':stock.cci,'np':np,'stock':stock} #条件判断需要使用的函数
        b,ls = shared.fromRedis('alert')
        if not b:
            ls = {}
        c = datetime.today()
        self._alerts = ls.copy()
        for a in ls.values():
            if c-a[3]>timedelta(days=7):#将太久前的给删除了
                self.deleteAlert(a)
        #0 ENABLE 1 DISABLE 2 ALERT 3 STROKE 4 WRONG
        self._imgs = [frame.loadImage('alert%d.png'%n) for n in [2,5,1,4,3]]
        #开启一个后台测试线程
        threading.Thread(target=self.test_loop).start()
    def toRedis(self):
        shared.toRedis(self._alerts,'alert')
    def getAlertByCode(self,code):
        """
        返回对应的报警设置，[[0.code,1.txt,2.cond,3.ts,4.state,5.active ts],..] 5检测成立触发时间
        """
        return self._alerts[code] if code in self._alerts else None
    def addAlert(self,code,txt,cond,state=ENABLE):
        self._alerts[code] = [code,txt,cond,datetime.today(),state,None]
    def deleteAlert(self,alert):
        """
        从列表中删除报警器
        """
        #将删除的可以保存到数据库中
        if alert is not None and alert[0] in self._alerts:
            del self._alerts[alert[0]]
    def alertLoop(self,condf):
        """
        报警循环，将现有报警放入如条件函数判断是不是达到报警条件
        condf(code,cond)
        """
    def test_loop(self):
        n = 0
        ot = 0
        while self._frame._running:
            if n>1000 and len(self._alerts)>0: #10秒检查一次
                n = 0
                b,t = shared.fromRedis('runtime_update')
                if b and t!=ot:
                    ot = t
                    k,d = xueqiu.get_period_k(240)
                    k60,d60 = xueqiu.get_period_k(60)
                    k30,d30 = xueqiu.get_period_k(30)
                    k15,d15 = xueqiu.get_period_k(15)
                    k5,d5 = xueqiu.get_period_k(5)
                    self._k = (k,k60,k30,k15,k5)
                    self._d = (d,d60,d30,d15,d5)
                    for a in self._alerts.values():
                        if a[4]==ENABLE:
                            b,msg = self.testCondition(a)
                            if b:
                                a[5] = datetime.today()
            sdl2.SDL_Delay(10)
            n+=1
    def renderAlert(self,canvas,x,y,w,h,alert):
        """
        绘制报警
        """
        if alert is not None:
            canvas.save()
            canvas.beginPath()
            if alert[4]==ENABLE:
                img = self._imgs[0]
            else:
                img = self._imgs[1]
            paint = canvas.imagePattern(x,y,w,h,0,img,1)
            if len(alert)>5 and alert[5] is not None:
                color = vg.nvgRGB(255,0,0)
            else:
                color = vg.nvgRGB(255,255,255)
            paint.innerColor = color
            canvas.fillPaint(paint)
            canvas.rect(x,y,w,h)
            canvas.fill()
            canvas.restore()
    def openui(self,code,done,ax=None,ay=None,w=1024,h=240):
        """
        打开一个界面用来报警或者编辑报警
        """
        if self._isopen:
            return
        self._isopen = True
        a = self.getAlertByCode(code)
        if a is not None:
            desc = a[1]
            cond = a[2]
            state = a[4]
        else:
            desc = ''
            cond = ''
            state = ENABLE
        dw = 24
        th = ui.Themos.UI_TITLE_HEIGHT
        def onok(but):
            if a is not None:
                #在修改前做一次检查看看有没有错误
                A = [code,win.getChildByName('desc')._text,win.getChildByName('cond')._text,datetime.today(),state,None]
                b,msg = self.testCondition(A)
                if msg is None:
                    a[1] = win.getChildByName('desc')._text
                    a[2] = win.getChildByName('cond')._text
                    a[4] = state
                else:
                    win.getChildByName('msg').setLabel(msg)
                    return
            else:
                A = [code,win.getChildByName('desc')._text,win.getChildByName('cond')._text,datetime.today(),state,None]
                b,msg = self.testCondition(A)
                if msg is None:
                    self.addAlert(code,win.getChildByName('desc')._text,win.getChildByName('cond')._text,state)
                else:
                    win.getChildByName('msg').setLabel(msg)
                    return
            self.toRedis()
            win.close()
            done()
            self._isopen = False
        def oncancel(but):
            win.close()
            done()
            self._isopen = False
        def ondisable(but):
            nonlocal state
            if state==ENABLE:
                state = DISABLE
                but.setLabel('解禁')
                win.getChildByName('icon').setImage('alert5.png')
            else:
                state = ENABLE
                but.setLabel('禁用')
                win.getChildByName('icon').setImage('alert2.png')
        def ondelete(but):
            self.deleteAlert(a)
            self.toRedis()
            win.close()
            done()
            self._isopen = False
        winps = {'size':(w,h),'title':'%s %s'%(AlertManager.code2com[code][2],code),
            'child':[
            {'class':'input','name':'desc','label':'说明','text':desc,'pos':(2*dw+128,dw+th),'size':(w-3*dw-128,dw)},
            {'class':'input','name':'cond','label':'条件','text':cond,'pos':(2*dw+128,3*dw+th),'size':(w-3*dw-128,dw)},
            {'class':'label','name':'msg','label':'','font':'zhb','fontcolor':(128,0,0,255),'pos':(2*dw+128,5*dw+th),'size':(w-3*dw-128,dw)},
            {'class':'image','name':'icon','img':'alert2.png' if state==ENABLE else 'alert5.png','pos':(dw,dw+th),'size':(128,128),'color':(0,0,0,255)},
            {'class':'button','label':'确定','pos':(w-dw-96,h-dw-36),'size':(96,36),'onclick':onok},
            {'class':'button','label':'取消','pos':(w-2*dw-2*96,h-dw-36),'size':(96,36),'onclick':oncancel},
            {'class':'button','label':'禁用' if state==ENABLE else '解禁','pos':(w-3*dw-3*96,h-dw-36),'size':(96,36),'bgcolor':(72,72,72,255),'onclick':ondisable},
            {'class':'button','label':'删除','pos':(w-4*dw-4*96,h-dw-36),'size':(96,36),'bgcolor':(255,128,64,255),'onclick':ondelete}]}
        if a is not None and len(a)>5 and a[5] is not None:
            winps['titlecolor'] = (196,0,0,255)
            winps['child'][3]['img'] = 'alert1.png'
            winps['child'][3]['color'] = (196,0,0,255)
        win = ui.window(self._frame,winps)
        if ax is not None:
            win.openAnimation(ax,ay)
    def testCondition(self,alert):
        """
        条件中可以出现的变量：k,k60,k30,k15,k5,d,d60,d30,d15,d5
        条件中出现的函数: ma,macd,boll,rsi,cci,
        """
        if len(alert[2])==0:
            return False,None
        if self._k is not None:
            K = self._k
            D = self._d
            i = AlertManager.code2i[alert[0]]
            locals = {'k':K[0][i,:],'k60':K[1][i,:],'k30':K[2][i,:],'k15':K[3][i,:],'k5':K[4][i,:],
                    'd':D[0],'d60':D[1],'d30':D[2],'d15':D[3],'d5':D[4]}
        else:
            K = np.ones((240,))#测试数据
            D = K
            locals = {'k':K,'k60':K,'k30':K,'k15':K,'k5':K,
                    'd':D,'d60':D,'d30':D,'d15':D,'d5':D}            

        try:
            if eval(alert[2],self._globals,locals):
                return True,None
        except Exception as e:
            #code = alert[0]
            #print(AlertManager.code2com[code][2],alert,str(e))
            msg = "%s"%str(e)
            return False,msg
        return False,None