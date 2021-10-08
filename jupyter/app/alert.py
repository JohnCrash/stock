import numpy as np
import copy
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
        self._cooldown = {}
        self._code2rect = {}
        self._globals = {'macd':stock.macdV,'boll':stock.boll,'ma':stock.ma,'rsi':stock.rsi,'cci':stock.cci,'np':np,'stock':stock} #条件判断需要使用的函数
        b,ls = shared.fromRedis('alert')
        if not b:
            ls = {}
        c = datetime.today()
        self._alerts = ls.copy()
        for a in ls.values():
            if c-a[3]>timedelta(days=7):#将太久前的给删除了
                self.deleteAlert(a)
        #将老的格式转换为新格式
        for a in ls.values():
            if type(a[1])==str:
                a[1] = [a[1],'','']
                a[2] = [a[2],'','']
            a[5] = None
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
    def deleteAlert(self,alert):
        """
        从列表中删除报警器
        """
        #将删除的可以保存到数据库中
        if alert is not None and alert[0] in self._alerts:
            del self._alerts[alert[0]]
    def alertLoop(self):
        """
        当有报警被触发后，在主循环中弹出界面。当报警触发后5分钟内不要再次显示该报警
        """
        if stock.isTransDay() and stock.isTransTime():
            R = []
            t = datetime.today()
            for a in self._alerts.values():
                if len(a)>5 and a[5] is not None and a[4]==ENABLE:
                    if a[0] not in self._cooldown or t-self._cooldown[a[0]]>timedelta(seconds=5*60):
                        R.append(a)
            if len(R)>0:
                a = R[0]
                self._cooldown[a[0]] = t #设置打开冷却时间
                def done():
                    pass
                if a[0] in self._code2rect:
                    ax = self._code2rect[a[0]][0]
                    ay = self._code2rect[a[0]][1]
                else:
                    ax = None
                    ay = None
                self._frame.playWave(0,self._frame._sellwav)
                self.openui(a[0],done,ax,ay)
        
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
                        a[5] = None
                        if a[4]==ENABLE:
                            for i in range(3):
                                b,msg = self.testCondition(a[0],a[2][i])
                                if b:
                                    if a[5] is None:
                                        a[5] = [None,None,None]
                                    a[5][i] = datetime.today()
            sdl2.SDL_Delay(10)
            n+=1
    def renderAlert(self,canvas,x,y,w,h,alert,code=None):
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
            if code is not None:
                self._code2rect[code] = (x,y,w,h)
    def openui(self,code,done,ax=None,ay=None,w=1024,h=240):
        """
        打开一个界面用来报警或者编辑报警
        """
        if self._isopen:
            return
        self._isopen = True
        a = copy.copy(self.getAlertByCode(code))
        if a[5] is not None:#如果有报警设置第一个报警
            for j in range(len(a[5])):
                if a[5][j]!=None:
                    i = j
                    break
        else:
            i = 0 
        needAppend = False
        if a is None:
            a = [code,['','',''],['','',''],datetime.today(),ENABLE,None]
            needAppend = True
        desc = a[1] if type(a[1])==str else a[1][i]
        cond = a[2] if type(a[2])==str else a[2][i]
        dw = 24
        th = ui.Themos.UI_TITLE_HEIGHT
        def storeInput2i():
            b,msg = self.testCondition(None,win.getChildByName('cond')._text)
            if msg is None:
                a[1][i] = win.getChildByName('desc')._text
                a[2][i] = win.getChildByName('cond')._text
                win.getChildByName('msg').setLabel('')
                return True
            else:
                win.getChildByName('msg').setLabel(msg)
            return False
        def onok(but):
            if storeInput2i():
                if needAppend:
                    self._alerts.append(a)
                else:
                    self._alerts[code] = a #覆盖
                self.toRedis()
                win.close()
                done()
                self._isopen = False
        def oncancel(but):
            win.close()
            done()
            self._isopen = False
        def ondisable(but):
            if a[4]==ENABLE:
                a[4] = DISABLE
                but.setLabel('解禁')
                win.getChildByName('icon').setImage('alert5.png')
            else:
                a[4] = ENABLE
                but.setLabel('禁用')
                win.getChildByName('icon').setImage('alert2.png')
        def ondelete(but):
            self.deleteAlert(a)
            self.toRedis()
            win.close()
            done()
            self._isopen = False
        def onclear(but): #清除当前输入
            win.getChildByName('desc').setText('')
            win.getChildByName('cond').setText('')
        def updatebuttoncolor():
            for i in range(3):
                win.getChildByName(str(i)).setButtonColor((192,0,0,255) if len(a[1][i])>0 or len(a[2][i])>0 else (192,192,192,255))
        def onswitch(but):
            nonlocal i
            if storeInput2i():
                i = int(but.label())-1
                updatebuttoncolor()
                win.getChildByName('desc').setText(a[1][i])
                win.getChildByName('cond').setText(a[2][i])
                win.getChildByName('icon').setImage('alert_%d.png'%(i+1))
                win.focusChild(win.getChildByName('desc'))
        winps = {'size':(w,h),'title':'%s %s'%(AlertManager.code2com[code][2],code),
            'child':[
            {'class':'input','name':'desc','label':'说明','text':desc,'fontsize':16,'pos':(2*dw+64,dw+th),'size':(w-3*dw-64,dw)},
            {'class':'input','name':'cond','label':'condition','text':cond,'font':'consola','fontsize':16,'pos':(2*dw+64,3*dw+th),'size':(w-3*dw-64,dw)},
            {'class':'label','name':'msg','label':'','font':'zhb','fontcolor':(64,0,0,255),'pos':(2*dw+64,5*dw+th-5),'size':(w-3*dw-64,dw)},
            {'class':'image','name':'icon','img':'alert_%d.png'%(i+1) if a[4]==ENABLE else 'alert5.png','pos':(dw,dw+th),'size':(64,64),'color':(0,0,0,255)},
            {'class':'button','label':'确定','pos':(w-dw-96,h-dw-36),'size':(96,36),'onclick':onok},
            {'class':'button','label':'取消','pos':(w-2*dw-2*96,h-dw-36),'size':(96,36),'onclick':oncancel},
            {'class':'button','label':'禁用' if a[4]==ENABLE else '解禁','pos':(w-3*dw-3*96,h-dw-36),'size':(96,36),'bgcolor':(72,72,72,255),'onclick':ondisable},
            {'class':'button','label':'删除','pos':(w-4*dw-4*96,h-dw-36),'size':(96,36),'bgcolor':(255,128,64,255),'onclick':ondelete},
            {'class':'button','label':'清除','pos':(w-5*dw-5*96,h-dw-36),'size':(96,36),'bgcolor':(255,128,64,255),'onclick':onclear},
            {'class':'button','name':'2','label':'3','pos':(w-6*dw-5*96-48,h-dw-36),'size':(48,36),'onclick':onswitch},
            {'class':'button','name':'1','label':'2','pos':(w-7*dw-5*96-2*48,h-dw-36),'size':(48,36),'onclick':onswitch},
            {'class':'button','name':'0','label':'1','pos':(w-8*dw-5*96-3*48,h-dw-36),'size':(48,36),'onclick':onswitch}]}
        
        if a[5] is not None: #报警设置
            for j in range(len(a[5])):
                if a[5][j] is not None:
                    winps['titlecolor'] = (196,0,0,255)
                    winps['child'][3]['color'] = (255,0,0,255) #icon设置颜色
                    winps['child'][11-j]['bgcolor'] = (255,0,0,255) #2->9 1->10 0->11
        win = ui.window(self._frame,winps)
        updatebuttoncolor()
        if ax is not None:
            win.openAnimation(ax,ay)
    def testCondition(self,code,cond):
        """
        条件中可以出现的变量：k,k60,k30,k15,k5,d,d60,d30,d15,d5
        条件中出现的函数: ma,macd,boll,rsi,cci,
        """
        if len(cond)==0:
            return False,None
        if self._k is not None and code in AlertManager.code2i:
            K = self._k
            D = self._d
            i = AlertManager.code2i[code]
            locals = {'k':K[0][i,:],'k60':K[1][i,:],'k30':K[2][i,:],'k15':K[3][i,:],'k5':K[4][i,:],
                    'd':D[0],'d60':D[1],'d30':D[2],'d15':D[3],'d5':D[4]}
        else:
            K = np.ones((240,))#测试数据
            D = K
            locals = {'k':K,'k60':K,'k30':K,'k15':K,'k5':K,
                    'd':D,'d60':D,'d30':D,'d15':D,'d5':D}            

        try:
            if eval(cond,self._globals,locals):
                return True,None
        except Exception as e:
            #code = alert[0]
            #print(AlertManager.code2com[code][2],alert,str(e))
            msg = "%s"%str(e)
            return False,msg
        return False,None