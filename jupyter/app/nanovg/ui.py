import ctypes
import numpy as np
from . import vg,themos
from .canvas import Canvas2d
from datetime import datetime
import sdl2

def one_bezier_curve(a,b,t):
    return (1-t)*a+t*b
def n_bezier_curve(xs,n,k,t):
    if n==1:
        return one_bezier_curve(xs[k],xs[k+1],t)
    else:
        return (1-t)*n_bezier_curve(xs,n-1,k,t)+t*n_bezier_curve(xs,n-1,k+1,t)
def cubic_bezier(x0,y0,x1,y1):
    """
    返回一个函数
    linear : cubic_bezier(0,0,1,1)
    ease-in: cubic_bezier(0.42,0,1,1)
    ease-out:cubic_bezier(0,0,.58,1)
    ease-in-out:cubic_bezier(0.42,0,.58,1)
    """
    n = 100
    xs = [0,x0,x1,1]
    ys = [0,y0,y1,1]
    xy = [0]*(n+1)
    a = []
    for i in range(n+1):
        t = i/n
        x = n_bezier_curve(xs,3,0,t)
        y = n_bezier_curve(ys,3,0,t)
        a.append((x,y))
    def getrange(x):
        for i in range(len(a)):
            if a[i][0]>x:
                break
        return a[i-1][0],a[i-1][1],a[i][0],a[i][1]
    def f(x):
        x0,y0,x1,y1 = getrange(x)
        return one_bezier_curve(y0,y1,(x-x0)/(x1-x0)) #插值
    return f
#ease_out = cubic_bezier(0,0,.3,1)
#ease_in= cubic_bezier(0.7,0,1,1)
ease_in_out = cubic_bezier(0.7,0,.3,1)
"""
使用方法：
childs = [
    {
        "class":"label",
        "label":"输入：",
        "font":"zh",
        "color":"black",
        "fontsize":14,
        "pos":[10,10],
        "size":[320,200]
    },
    {
        "class":"button",
        "label":"OK",
        "font":"zh",
        "color":"black",
        "fontsize":14,
        "pos":[10,10],
        "size":[320,200],
        "onClick":okEvent,
    },    
]
def onEvent(ui,action,param):
    pass
window(app,{"title":"设置报警","child":childs},onEvent)
"""
Themos = themos.ThemosBlack
class ui:
    MouseDown = 0
    MouseUp = 1
    MouseMove = 2
    def __init__(self):
        self._isfocus = False
    def mouse(self,action,x,y):
        """
        如果成功处理了返回True
        """
        return False
    def keydown(self,key):
        return False
    def editing(self,text):
        return False
    def input(self,text):
        return False
    def render(self,canvas):
        pass
    def onloop(self,t,dt):
        return False
    def focus(self,b):
        self._isfocus = b
class window(ui):
    OPENDT = .4 #打开耗时
    def __init__(self,app,ps):
        super().__init__()
        self._app = app
        self._ps = ps
        self._drop = False
        self._name = "window%s"%str(datetime.today())
        pt = ps["pos"]
        size = ps["size"]
        self._focus = None
        self._pt = pt
        self._size = size
        self._opent = 0
        self._openxy = [0,0]
        app.registerHook("event",self.eventCallback)
        app.registerHook("loop",self.onloop)
        app.createFrame(pt[0],pt[1],size[0],size[1],self._name)
        self._child = self.parse(ps)
        self.renderSelf()
        
    def openAnimation(self,x=None,y=None):
        """
        打开动画
        """
        self._opent = window.OPENDT
        if x is not None:
            self._openxy = (x,y)
        else: #从鼠标点击位置弹出
            self._openxy[0],self._openxy[1] = self._app.getCursorPt()
        self._endxy = self._pt
    def parse(self,ps):
        """
        将数据结构转换成对象
        """
        child = []
        if 'child' in ps:
            for c in ps['child']:
                if c['class']=='button':
                    child.append(button(self,c))
                elif c['class']=='label':
                    child.append(label(self,c))
                elif c['class']=='image':
                    child.append(image(self,c))           
                elif c['class']=='input':
                    child.append(input(self,c))
        return child
    def eventCallback(self,name,args):
        event = args[0]
        if event.type==sdl2.SDL_MOUSEMOTION:
            self.mouse(ui.MouseMove,event.motion.x,event.motion.y)
        elif event.type==sdl2.SDL_MOUSEBUTTONDOWN:
            self.mouse(ui.MouseDown,event.motion.x,event.motion.y)
        elif event.type==sdl2.SDL_MOUSEBUTTONUP:
            self.mouse(ui.MouseUp,event.motion.x,event.motion.y)
        elif event.type==sdl2.SDL_KEYDOWN:
            self.keydown(event.key)
        elif event.type==sdl2.SDL_TEXTINPUT:
            self.input(event.text)
        elif event.type==sdl2.SDL_TEXTEDITING:
            self.editing(event.text)
        else:
            return False
        return True
    def editing(self,text):
        if self._focus is not None:
            self._focus.editing(text)
    def input(self,text):
        if self._focus is not None:
            self._focus.input(text)
    def keydown(self,key):
        for kit in self._child:
            if kit.keydown(key):
                break   
    def onloop(self,name,args):
        if self._opent!=0:
            _,dt = args
            if self._opent<0:
                self._opent = 0
                t = 1
            else:
                t = ease_in_out(1-self._opent/window.OPENDT)
                self._opent-=dt
            x = one_bezier_curve(self._openxy[0],self._endxy[0],t)
            y = one_bezier_curve(self._openxy[1],self._endxy[1],t)
            w = one_bezier_curve(1,self._size[0],t)
            h = one_bezier_curve(1,self._size[1],t)
            self._app.movefbo(self._name,x,y,w,h)
        for kit in self._child:
            kit.onloop(*args)
        return True
    def renderSelf(self):
        canvas,w,h = self._app.beginFrame(self._name)
        if canvas is not None:
            self.render(canvas) #绘制窗口
        self._app.endFrame()
    def renderChild(self,child):
        canvas,w,h = self._app.beginFrame(self._name)
        if canvas is not None:
            child.render(canvas) #绘制窗口
        self._app.endFrame()
    def mouse(self,action,mx,my):
        #标题拖动
        x,y = self._pt
        w,h = self._size
        if 'title' in self._ps:
            titleh = 32 if 'titleheight' not in self._ps else self._ps['titleheight']
            if action==ui.MouseDown and mx>x and mx<x+w and my>y and my<y+titleh:
                self._drop = True
                self._dropxy = (mx,my)
            elif self._drop and action==ui.MouseUp:
                self._drop = False
            elif self._drop and action==ui.MouseMove:
                self._pt = (x+mx-self._dropxy[0],y+my-self._dropxy[1])
                self._dropxy = (mx,my)
                self._app.movefbo(self._name,self._pt[0],self._pt[1])
        for kit in self._child:
            if kit.mouse(action,mx-x,my-y):
                break
    def bgcolor(self):
        """
        返回窗口的背景颜色
        """
        return vg.nvgRGBA(*self._ps['bgcolor']) if 'bgcolor' in self._ps else Themos.BG_COLOR
    def titleHeight(self):
        """
        返回窗口的标题高度
        """
        return 32 if 'titleheight' not in self._ps else self._ps['titleheight']
    def rectRound(self):
        """
        返回窗口圆角半径
        """
        return 3 if 'round' not in self._ps else self._ps['round']
    def titleColor(self):
        """
        返回窗口标题颜色
        """
        return vg.nvgRGBA(*self._ps['titlecolor']) if 'titlecolor' in self._ps else Themos.PRICE_COLOR
    def titleFontColor(self):
        """
        返回标题字体颜色
        """
        return Themos.TEXTCOLOR if 'fontcolor' not in self._ps else vg.nvgRGBA(*self._ps['fontcolor'])
    def titleFont(self):
        """
        返回标题字体
        """
        return 'zh' if 'font' not in self._ps else self._ps['font']
    def titleFontSize(self):
        """
        返回标题字体大小
        """
        return 14 if 'fontsize' not in self._ps else self._ps['fontsize']
    def title(self):
        return self._ps['title']
    def render(self,canvas):
        #首先绘制窗口
        w,h = self._ps['size']
        canvas.beginPath() #绘制标题头
        canvas.fillColor(self.bgcolor())
        canvas.roundedRect(0,0,w,h,3)
        canvas.fill()
        canvas.beginPath()
        r = self.rectRound()
        titleh = self.titleHeight()
        canvas.fillColor(self.titleColor())
        canvas.roundedRect(0,0,w,titleh,r)
        canvas.fill()
        canvas.beginPath()
        canvas.fillColor(self.bgcolor())
        canvas.rect(0,titleh-r,w,r)
        canvas.fill()
        canvas.beginPath()
        linearG = canvas.linearGradient(0,titleh-r,0,titleh-r+3*r,vg.nvgRGBA(0,0,0,32),vg.nvgRGBA(0,0,0,0))
        canvas.rect(0,titleh-r,w,3*r)
        canvas.fillPaint(linearG)
        canvas.fill()
        if 'title' in self._ps: #存在标题栏
            canvas.fontFace(self.titleFont())
            canvas.fontSize(self.titleFontSize())
            canvas.fillColor(self.titleFontColor())
            canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_MIDDLE)
            canvas.text(titleh/2,titleh/2,self.title())
        #然后绘制子窗口
        for kit in self._child:
            kit.render(canvas)
    def close(self):
        """
        关闭窗口界面
        """
        self._app.deleteFrame(self._name)
        self._app.unregisterHook("event",self.eventCallback)
    def focusChild(self,child):
        if self._focus is not None and self._focus!=child:
            self._focus.focus(False)
        if self._focus!=child:
            self._focus = child
            self._focus.focus(True)

class label(ui):
    def __init__(self,parent,ps):
        super().__init__()
        self._parent = parent
        self._ps = ps
    def font(self):
        return 'zh' if 'font' not in self._ps else self._ps['font']
    def fontSize(self):
        return 14 if 'fontsize' not in self._ps else self._ps['fontsize']
    def fontColor(self):
        return Themos.TEXTCOLOR if 'fontcolor' not in self._ps else vg.nvgRGBA(*self._ps['fontcolor'])
    def render(self,canvas):
        canvas.fontFace(self.font())
        canvas.fontSize(self.fontSize())
        canvas.fillColor(self.fontColor())
        canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_TOP)
        x,y = self._ps['pos']
        canvas.text(x,y,self._ps['label'])
class button(ui):
    CLICKDT = 0.4 #点击动画时间
    def __init__(self,parent,ps):
        super().__init__()
        self._isdown = False
        self._ismousein = False
        self._parent = parent
        self._ps = ps
        self._dht = 0
    def font(self):
        return 'zh' if 'font' not in self._ps else self._ps['font']
    def fontSize(self):
        return 14 if 'fontsize' not in self._ps else self._ps['fontsize']
    def fontColor(self):
        return Themos.TEXTCOLOR if 'fontcolor' not in self._ps else vg.nvgRGBA(*self._ps['fontcolor']) 
    def buttonColor(self):
        return vg.nvgRGBA(*self._ps['bgcolor']) if 'bgcolor' in self._ps else Themos.BG_COLOR
    def render(self,canvas):
        x,y = self._ps['pos']
        w,h = self._ps['size']
        canvas.beginPath()
        bgc = self.buttonColor()
        if self._ismousein: #加亮
            hsl = vg.rgb2hsl(bgc.c.r,bgc.c.g,bgc.c.b)
            s = 0.2 if self._isdown and self._dht<=0 else 0.1
            bgc = vg.nvgHSL(hsl[0],hsl[1],hsl[2]+(1-hsl[2])*s)
        canvas.fillColor(bgc)
        canvas.roundedRect(x,y,w,h,3)
        canvas.fill()
        if self._dht>0: #绘制点击动画
            canvas.beginPath()
            bgc = self.buttonColor()
            canvas.scissor(x,y,w,h)
            hsl = vg.rgb2hsl(bgc.c.r,bgc.c.g,bgc.c.b)
            bgc = vg.nvgHSL(hsl[0],hsl[1],hsl[2]+(1-hsl[2])*0.2)
            canvas.circle(self._clickpt[0],self._clickpt[1],w*(1-ease_in_out(self._dht/button.CLICKDT)))
            canvas.fillColor(bgc)
            canvas.fill()
            canvas.resetScissor()
        canvas.fontFace(self.font())
        canvas.fontSize(self.fontSize())
        canvas.fillColor(self.fontColor())
        canvas.textAlign(vg.NVG_ALIGN_CENTER|vg.NVG_ALIGN_MIDDLE)
        canvas.text(x+w/2,y+h/2,self._ps['label'])
    def mouse(self,action,mx,my):
        x,y = self._ps['pos']
        w,h = self._ps['size']        
        if action==ui.MouseDown or action==ui.MouseUp:
            if mx>x and mx<x+w and my>y and my<y+h and action==ui.MouseDown:
                self._isdown = True
                self._clickpt = (mx,my)
                self._dht = button.CLICKDT                
                self._parent.focusChild(self)
                self._parent.renderChild(self)
            elif self._isdown:
                self._isdown = False
                self._parent.renderChild(self)
                if 'onclick' in self._ps and mx>x and mx<x+w and my>y and my<y+h:
                    self._ps['onclick']()
        elif action==ui.MouseMove:
            b = self._ismousein
            if mx>x and mx<x+w and my>y and my<y+h:
                 self._ismousein = True
            else:
                self._ismousein = False
            if b!=self._ismousein:
                self._parent.renderChild(self)
    def onloop(self,t,dt):
        if self._dht>0:
            self._dht-=dt
            self._parent.renderChild(self)
class input(ui):
    def __init__(self,parent,ps):
        super().__init__()
        self._parent = parent
        self._ps = ps
        self._text = self._ps['label']
        self._n = 0 #光标后面有多少字符
    def font(self):
        return 'zh' if 'font' not in self._ps else self._ps['font']
    def fontSize(self):
        return 14 if 'fontsize' not in self._ps else self._ps['fontsize']
    def fontColor(self):
        return Themos.TEXTCOLOR if 'fontcolor' not in self._ps else vg.nvgRGBA(*self._ps['fontcolor'])
    def editlineColor(self):
        return Themos.BG_COLOR if 'linecolor' not in self._ps else vg.nvgRGBA(*self._ps['linecolor'])
    def focuslineColor(self):
        return Themos.PRICE_COLOR if 'focuscolor' not in self._ps else vg.nvgRGBA(*self._ps['focuscolor'])
    def render(self,canvas):
        x,y = self._ps['pos']
        w,h = self._ps['size']
        canvas.beginPath()
        canvas.fillColor(self._parent.bgcolor())
        canvas.rect(x,y,w,h)
        canvas.fill()

        canvas.beginPath()
        if self._isfocus:
            canvas.strokeColor(self.focuslineColor())
        else:
            canvas.strokeColor(self.editlineColor())
        canvas.moveTo(x,y+h)
        canvas.lineTo(x+w,y+h)
        canvas.stroke()

        canvas.fontFace(self.font())
        canvas.fontSize(self.fontSize())
        canvas.fillColor(self.fontColor())
        canvas.textLetterSpacing(1)
        canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_MIDDLE)
        canvas.text(x+2,y+h/2,self._text)
        #绘制光标
        if self._isfocus:
            rounds = np.empty((4,),dtype=np.float32)
            txt = self._text if self._n==0 else self._text[:-self._n]
            if len(txt)>0 and txt[-1]==' ':#fixbug 最后一个如果是空格长度计算有问题
                txt = txt[:-1]+'i'
            canvas.textBounds(x+2,y,txt,rounds.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
            canvas.beginPath()
            canvas.strokeColor(vg.nvgRGB(0,0,0))
            canvas.moveTo(rounds[2],y+2)
            canvas.lineTo(rounds[2],y+h-4)
            canvas.stroke()

    def mouse(self,action,mx,my):
        x,y = self._ps['pos']
        w,h = self._ps['size']        
        if action==ui.MouseDown or action==ui.MouseUp:
            if mx>x and mx<x+w and my>y and my<y+h and action==ui.MouseDown:            
                self._parent.focusChild(self)
                self._parent.renderChild(self)
    def editing(self,text):
        return True
    def input(self,text):
        self.insertText(str(text.text,'utf-8'))
        return True
    def keydown(self,key):
        if self._isfocus is True:
            if key.keysym.sym==sdl2.SDLK_BACKSPACE:
                if self._n==0:
                    self._text = self._text[:-1]
                else:
                    self._text = self._text[:-self._n-1]+self._text[-self._n:]
            elif key.keysym.sym==sdl2.SDLK_HOME:
                self._n = len(self._text)
            elif key.keysym.sym==sdl2.SDLK_END:
                self._n = 0
            elif key.keysym.sym==sdl2.SDLK_LEFT:
                if self._n<len(self._text):
                    self._n+=1
            elif key.keysym.sym==sdl2.SDLK_RIGHT:
                if self._n>0:
                    self._n-=1
            elif key.keysym.sym==sdl2.SDLK_DELETE:
                if self._n>0:
                    if -self._n+1<0:
                        self._text = self._text[:-self._n]+self._text[-self._n+1:]
                    else:
                        self._text = self._text[:-self._n]
                    self._n-=1
            #select cute copy past
            self._parent.renderChild(self)
        return False          
    def focus(self, b):
        if b:
            x,y = self._ps['pos']
            w,h = self._ps['size']              
            sdl2.SDL_StartTextInput()
            rc = sdl2.SDL_Rect(-x,y+h,w,w)
            sdl2.SDL_SetTextInputRect(ctypes.byref(rc))
        else:
            sdl2.SDL_StopTextInput()
        super().focus(b)
        self._parent.renderChild(self)
    def insertText(self,txt):
        if self._n==0:
            self._text += txt
        else:
            self._text = self._text[:-self._n]+txt+self._text[-self._n:]
        self._parent.renderChild(self)
class image(ui):
    def __init__(self,parent,ps):
        super().__init__()
        self._parent = parent
        self._ps = ps
        self._img = None
    def render(self,canvas):
        x,y = self._ps['pos']
        w,h = self._ps['size']
        if self._img is None:
            self._img = canvas.createImage("D:/source/stock/jupyter/images/"+self._ps['img'],0)  
        imgw,imgh = canvas.imageSize(self._img)
        canvas.save()
        paint = canvas.imagePattern(x,y,imgw,imgh,0,self._img,1)
        canvas.beginPath()
        #canvas.scale(w/imgw,h/imgh)
        canvas.rect(x,y,imgw,imgh)
        canvas.fillPaint(paint)
        canvas.fill()
        canvas.restore()

def test(self):
    win = None
    def createwin():
        w = window(self,{'pos':((self._w-W)/2,(self._h-H)/2),'size':(W,H),'title':'测试窗口','bgcolor':(220,220,220,255),'font':'zhb','fontcolor':(255,255,255,255),
            'child':[{'class':'label','label':'提示:','pos':(24,48+32),'size':(W-48,48),'fontcolor':(0,0,0,255)},
            {'class':'input','label':'输入','pos':(24,48+32+48),'size':(W-48,24),'fontcolor':(128,128,128,255)},
            {'class':'input','label':'条件','pos':(24,48+32+48+32),'size':(W-48,24),'fontcolor':(128,128,128,255)},
            {'class':'image','img':'xueqiu.png','pos':(24,48+32+48+128),'size':(W-48,48)},
            {'class':'button','label':'关闭','pos':(W-128-24,H-48-24),'size':(128,48),'onclick':onclose},
            {'class':'button','label':'打开','pos':(128-24,H-48-24),'size':(128,48),'onclick':onopen}]})
        return w
    def onclose():
        win.close()
    def onopen():
        nonlocal win
        win.close()
        w = createwin()
        w.openAnimation()   
        win = w
    W = 800
    H = 480
    win = createwin()
    win.openAnimation(0,0)
