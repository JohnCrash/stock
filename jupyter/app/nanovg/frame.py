import ctypes
from ctypes import c_int
from OpenGL import GL
import sdl2
import math
import numpy as np
from sdl2 import video,events,sdlmixer
from sdl2.timer import SDL_GetTicks
from . import vg
from .canvas import Canvas2d

class app:
    """
    定义一个基本的VG窗口类
    初始化字体
    """
    FCCOLOR = vg.nvgRGB(200,200,200)
    ICONBG = vg.nvgRGB(64,64,64)
    ICONCOLOR = vg.nvgRGB(196,196,196)
    CAPTION_HEIGHT = 32
    def __init__(self,title,w,h,style=sdl2.SDL_WINDOW_OPENGL|sdl2.SDL_WINDOW_BORDERLESS):#sdl2.SDL_WINDOW_OPENGL|sdl2.SDL_WINDOW_RESIZABLE):
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            raise RuntimeError('SDL_Init')
        
        sdlmixer.Mix_Init(sdlmixer.MIX_INIT_OGG)
        sdlmixer.Mix_OpenAudio(22050,sdlmixer.MIX_DEFAULT_FORMAT,2,4096)

        self._window = sdl2.SDL_CreateWindow(title.encode('utf-8'),
                                    sdl2.SDL_WINDOWPOS_UNDEFINED,
                                    sdl2.SDL_WINDOWPOS_UNDEFINED, w, h,
                                    style)
        if not self._window:
            raise RuntimeError('SDL_CreateWindow')
        self._context = sdl2.SDL_GL_CreateContext(self._window)
        sdl2.SDL_GL_MakeCurrent(self._window,self._context)
        if vg.glewInit()!=vg.GLEW_OK:
            raise RuntimeError('glewInit')
        self._canvas = Canvas2d()
        self._running = True
        self._fps = 0
        self._interval = -1
        self._clearColor = (1,1,1,1)
        sdl2.SDL_GL_SetSwapInterval(0)
        self.loadDemoData()
        self._mouseini = -1
        self._windowns = True
        self._windowstyle = style
        self._windowtitle = ''
        self._delayupdate = False
        self._windowx,self._windowy = 0,0
        self._windoww,self._windowh = w,h
        self.fullScreen()
        w,h = c_int(),c_int()
        video.SDL_GetWindowSize(self._window, ctypes.byref(w), ctypes.byref(h))
        self._fbos = {}
        self._updatefbo = False
        self._w = w.value
        self._h = h.value        
        self.createFrame(0,0,w.value,app.CAPTION_HEIGHT,'title')
        self.setInterval(60)
    def createFrame(self,x,y,w,h,name=None):
        fbo = self._canvas.createFramebuffer(w,h,vg.NVG_IMAGE_REPEATX | vg.NVG_IMAGE_REPEATY)
        self._fbos[name] = (x,y,w,h,fbo,name)
        return self._fbos[name]
    def deleteFrame(self,name):
        if name in self._fbos:
            fbo = self._fbos[name]
            del self._fbos[name]
            self._canvas.deleteFramebuffer(fbo[4])
    def getFrame(self,name):
        if name in self._fbos:
            return self._fbos[name]
        else:
            return None
    def beginFrame(self,name):
        if name in self._fbos:
            fbo = self._fbos[name]
            self._updatefbo = True
            self._canvas.bindFramebuffer(fbo[4])
            GL.glViewport(0,0,fbo[2],fbo[3])
            self._canvas.beginFrame(fbo[2],fbo[3],1)
            return self._canvas,fbo[2],fbo[3]
        else:
            return None,None,None
    def endFrame(self):
        self._canvas.endFrame()
    def movefbo(self,name,x,y):
        if name in self._fbos:
            fbo = self._fbos[name]
            self._updatefbo = True
            fbo[0] = x
            fbo[1] = y
    def loadWave(self,fn):
        path = '/'.join(str.split(__file__,'\\')[:-1])
        f = "%s/static/%s"%(path,fn)
        return sdlmixer.Mix_LoadWAV(f.encode('utf-8'))
    def setMixVolume(self,ch,vo=1):
        sdlmixer.Mix_Volume(ch,int(vo*sdlmixer.MIX_MAX_VOLUME))
    def playWave(self,channel,wav,n=0):
        sdlmixer.Mix_PlayChannel(channel,wav,n)
    def loadMusic(self,fn):
        path = '/'.join(str.split(__file__,'\\')[:-1])
        f = "%s/static/%s"%(path,fn)
        return sdlmixer.Mix_LoadMUS(f.encode('utf-8'))        
    def playMusic(self,wav):
        sdlmixer.Mix_PlayMusic(wav,1)
    def setWindowTitle(self,title):
        if self._windowstyle&sdl2.SDL_WINDOW_BORDERLESS:
            self._windowtitle = title
            self.renderCaption()
        else:
            self._windowtitle = title
            sdl2.SDL_SetWindowTitle(self._window,title.encode('utf-8'))
    def delayUpdate(self):
        self._delayupdate = True
    def quit(self):
        self._running = False
    def keyDown(self,event):
        pass
    def keyUp(self,event):
        pass
    def handleEvent(self,event):
        return False
    def onWindowEvent(self,event):
        if event.window.event==sdl2.SDL_WINDOWEVENT_SIZE_CHANGED:
            self.update()
        elif event.window.event==sdl2.SDL_WINDOWEVENT_SHOWN:
            self.update()
    def run(self):
        event = sdl2.SDL_Event()
        prevt = 0
        acc = 0
        while self._running:
            while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
                if not self.handleEvent(event):
                    if event.type == sdl2.SDL_QUIT:
                        self.quit()
                    elif event.type == sdl2.SDL_KEYDOWN:
                        #ptr = ctypes.cast(event, events.SDL_KeyboardEvent)
                        self.keyDown(event)
                    elif event.type == sdl2.SDL_KEYUP:
                        self.keyUp(event)
                    elif event.type==sdl2.SDL_WINDOWEVENT:
                        self.onWindowEvent(event)                        
                    elif event.type==sdl2.SDL_MOUSEMOTION:
                        self.onMouseMotion(event)
                    elif event.type==sdl2.SDL_MOUSEBUTTONDOWN:
                        self.onMouseDown(event)
                    elif event.type==sdl2.SDL_MOUSEBUTTONUP:
                        self.onMouseUp(event)

            t = SDL_GetTicks()/1000.
            dt = t-prevt
            prevt = t
            self.onLoop(t,dt)
            if (self._interval>0 and acc>self._interval) or self._delayupdate:
                acc = 0
                self.update(dt)
                self._delayupdate = False
            acc+=dt
            sdl2.SDL_Delay(10)
        sdl2.SDL_GL_DeleteContext(self._context)
        sdl2.SDL_DestroyWindow(self._window)
        sdlmixer.Mix_CloseAudio()
        sdlmixer.Mix_Quit()
        sdl2.SDL_Quit()
        
    def setInterval(self,r):
        """
        控制渲染频率
        """
        self._fps = r
        if r>0:
            self._interval = 1./r
        else:
            self._interval = -1

    def setClearColor(self,c):#rgba 0-1
        self._clearColor = c
    def onLoop(self,t,dt):
        """
        主循环事件
        """
        pass
    def onMouseMotion(self,event):
        if self._windowstyle&sdl2.SDL_WINDOW_BORDERLESS:
            mx=event.motion.x
            my=event.motion.y
            old = self._mouseini
            self._mouseini = -1
            if my<app.CAPTION_HEIGHT:
                w = self._w
                h = app.CAPTION_HEIGHT
                for i in range(3):
                    xx = w-(3-i)*h
                    if mx<xx+h and mx>xx:
                        self._mouseini = i
                        break
            if old!=self._mouseini:
                self.renderCaption()
    def onMouseDown(self,event):
        pass
    def fullScreen(self):
        m = sdl2.SDL_DisplayMode()
        sdl2.SDL_GetDesktopDisplayMode(0,ctypes.byref(m))
        self._windowx,self._windowy = c_int(),c_int()
        sdl2.SDL_GetWindowPosition(self._window,ctypes.byref(self._windowx),ctypes.byref(self._windowy))
        sdl2.SDL_SetWindowPosition(self._window,0,0)
        self._windoww,self._windowh = c_int(),c_int()
        sdl2.SDL_GetWindowSize(self._window, ctypes.byref(self._windoww), ctypes.byref(self._windowh))
        sdl2.SDL_SetWindowSize(self._window,m.w,m.h-1) #如果不减去1 窗口切换更新会发生闪烁
    def restoreWindow(self):
        sdl2.SDL_SetWindowPosition(self._window,self._windowx.value,self._windowy.value)
        sdl2.SDL_SetWindowSize(self._window,self._windoww.value,self._windowh.value)
    def onMouseUp(self,event):
        if event.button.button==sdl2.SDL_BUTTON_LEFT and self._windowstyle&sdl2.SDL_WINDOW_BORDERLESS:
            mx=event.button.x
            my=event.button.y
            if my<app.CAPTION_HEIGHT:
                w = self._w
                h = app.CAPTION_HEIGHT
                for i in range(3):
                    xx = w-(3-i)*h
                    if mx<xx+h and mx>xx:
                        if i==0: #最新化
                            sdl2.SDL_MinimizeWindow(self._window)
                        elif i==1: #最大化
                            if self._windowns:
                                #sdl2.SDL_MaximizeWindow(self._window)
                                self.fullScreen()
                            else:
                                self.restoreWindow()
                            self._windowns = not self._windowns
                        elif i==2: #关闭
                            self.quit()
                        break        
    def drawIcon(self,x,y,w,h,id,b):
        x+=b
        y+=b
        w-=2*b
        h-=2*b
        with self._canvas as c:
            c.beginPath()
            c.strokeWidth(2)
            c.strokeColor(app.ICONCOLOR)
            if id==0: #最小化
                c.moveTo(x,y+h*2/3)
                c.lineTo(x+w,y+h*2/3)
            elif id==1: #最大化
                c.rect(x,y,w,h)
            elif id==2: #关闭
                c.moveTo(x,y)
                c.lineTo(x+w,y+h)
                c.moveTo(x+w,y)
                c.lineTo(x,y+h)
            c.stroke()
    def renderCaption(self):
        c,w,h = self.beginFrame('title')
        x,y = 0,0
        c.beginPath()
        c.fillColor(self._clearColor)
        c.rect(x,y,w,h)
        c.fill()        
        for i in range(3):
            xx = w-(3-i)*h
            if self._mouseini==i: #绘制选中背景
                c.beginPath()
                c.fillColor(app.ICONBG)
                c.rect(xx,y,h,h)
                c.fill()
            self.drawIcon(xx,y,h,h,i,10)

        c.fontFace('zh')
        c.fontSize(16)
        c.fillColor(app.FCCOLOR)
        c.textAlign(vg.NVG_ALIGN_CENTER|vg.NVG_ALIGN_MIDDLE)
        c.text(w/2,h/2,self._windowtitle)
        self.endFrame()
    def render(self,canvas,x,y,w,h):
        pass
    def update(self,dt=0):
        if self._updatefbo or self._delayupdate:
            w,h = c_int(),c_int()
            video.SDL_GetWindowSize(self._window, ctypes.byref(w), ctypes.byref(h))
            self._w = w.value            
            fbWidth,fbHeight = w.value,h.value
            vg.nvgluBindFramebuffer(None) #默认FBO
            GL.glViewport(0, 0, fbWidth, fbHeight)
            canvas = self._canvas
            canvas.beginFrame(fbWidth,fbHeight,1)
            for k in self._fbos:
                fbo = self._fbos[k]
                canvas.beginPath()
                cfp = canvas.imagePattern(fbo[0],fbo[1],fbo[2],fbo[3],0,fbo[4].contents.image,1)
                canvas.fillPaint(cfp)
                canvas.rect(fbo[0],fbo[1],fbo[2],fbo[3])
                canvas.fill()
            self.render(canvas,0,0,w.value,h.value)
            canvas.endFrame()
            sdl2.SDL_GL_SwapWindow(self._window)
            self._updatefbo = False

    def loadDemoData(self):
        data = {}
        data['images'] = []
        path = '/'.join(str.split(__file__,'\\')[:-1])

        data['fontIcons'] = self._canvas.createFont("icons", "%s/static/entypo.ttf"%path)
        if data['fontIcons'] == -1:
            print("Could not add font icons.\n")
            return -1

        data['fontNormal'] = self._canvas.createFont("sans", "%s/static/Roboto-Regular.ttf"%path)
        if data['fontNormal'] == -1:
            print("Could not add font italic.\n")
            return -1

        data['fontBold'] = self._canvas.createFont("sans-bold", "%s/static/Roboto-Bold.ttf"%path)
        if data['fontBold'] == -1:
            print("Could not add font bold.\n")
            return -1

        data['fontEmoji'] = self._canvas.createFont("emoji", "%s/static/NotoEmoji-Regular.ttf"%path)
        if data['fontEmoji'] == -1:
            print("Could not add font emoji.\n")
            return -1

        zh = self._canvas.createFont("zh", "c:/windows/fonts/msyh.ttc")
        if zh == -1:
            print("Could not add font zh.\n")
            return -1
        zhb = self._canvas.createFont("zhb", "c:/windows/fonts/msyhbd.ttc")
        if zhb == -1:
            print("Could not add font zhb.\n")
            return -1        
        self._canvas.addFallbackFontId(data['fontNormal'], data['fontEmoji'])
        self._canvas.addFallbackFontId(data['fontBold'], data['fontEmoji'])
        return data    

class fpsGraph:
    def __init__(self):
        self._values = [0]*100
        self._head = 0
    def update(self,frameTime):
        self._head = (self._head+1)%100
        self._values[self._head] = frameTime
    def getGraphAverage(self):
        avg = 0
        for i in range(100):
            avg += self._values[i]
        return avg/100.
    def render(self,canvas,x,y):
        avg = self.getGraphAverage()
        w = 200
        h = 35
        canvas.beginPath()
        canvas.rect(x,y, w,h)
        canvas.fillColor(vg.nvgRGBA(0,0,0,128))
        canvas.fill()
        canvas.beginPath()
        canvas.moveTo(x, y+h)

        for i in range(100):
            v = 1.0 / (0.00001 + self._values[(self._head+i) % 100])
            if v > 80.0:
                v = 80.0
            vx = x + (float(i)/(100-1)) * w
            vy = y + h - ((v / 80.0) * h)
            canvas.lineTo(vx, vy)
        
        canvas.lineTo(x+w, y+h)
        canvas.fillColor(vg.nvgRGBA(255,192,0,128))
        canvas.fill()

        canvas.fontFace("sans")

        canvas.fontSize(15.0)
        canvas.textAlign(vg.NVG_ALIGN_RIGHT|vg.NVG_ALIGN_TOP)
        canvas.fillColor(vg.nvgRGBA(240,240,240,255))
        s = "%.2f FPS"%(1.0 / avg)
        canvas.text(x+w-3,y+3, s)
        canvas.fontSize(13.)
        canvas.textAlign(vg.NVG_ALIGN_RIGHT|vg.NVG_ALIGN_BASELINE)
        canvas.fillColor(vg.nvgRGBA(240,240,240,160))
        s = "%.2f ms"%(avg * 1000.0)
        canvas.text(x+w-3,y+h-3, s)

def pone(a,f=math.ceil):
    """
    保留数a一位精度,例如0.123 返回0.2 如果将f=math.floor就是0.1
    """
    if a<0:
        a = -a
    if a==0:
        return 0,1
    lg = math.log10(a)
    if lg>0:
        n = math.pow(10,lg-int(lg))
        e = int(lg)
    elif lg<0:
        n = math.pow(10,lg-int(lg)+1)
        e = int(lg)-1
    return f(n)*math.pow(10,e),e
def precision(a,e):
    """
    截断精度一下的数字例如，0.1233,-1 返回0.1
    """
    return int(a/math.pow(10,e))*math.pow(10,e)

class Plot:
    """
    绘制图表
    """
    LINE = 1
    K = 2
    BAR = 3
    c_float_p = ctypes.POINTER(ctypes.c_float)
    AXISCOLOR = vg.nvgRGBf(0,0,0)
    GRIDCOLOR = vg.nvgRGBf(0.8,0.8,0.8)
    TEXTCOLOR = vg.nvgRGBf(0,0,0)
    def __init__(self):
        self._x = None
        self._xlabels = None
        self._y = []
        self._hline = []
        self._vline = []
        self._lwscale = 1
        self._title = ''
        self._xticks = None
        self._yticks = None
        self._xtickshow = True
        self._ytickshow = True
        self._xtickangle = 0
        self._ytickangle = 0
        self._area = [0,0,0,0] #作图区大小
        self._border = [0,0,0,0] #图表矩形外预留空间 
        self._inner = [0,0,0,0] #图表矩形内预留空间 
        self._gridx = False
        self._gridy = False
        self._xe = None
        self._ye = None
        self._xk = None
        self._xb = None
        self._titleColor = None
        self._titleSize = 14
        self._themos = Plot
    def setThemos(self,themos):
        self._themos = themos
    def setx(self,x,labels=None):
        """
        设置x轴数据,labels=[(i,label),...]
        """
        self._x  = x
        self._xlabels = labels
    def plot(self,y,color=vg.nvgRGBA(0,0,0,255),linewidth=1,linestyle=None,label=None,style=LINE):
        """
        绘制线型图表
        """
        self._xk = None
        self._xb = None
        self._y.append((y,color,linewidth,linestyle,label,style)) #0 y,1 color,2 linewidth,3 linestyle,4 label
    def hline(self,y,color=vg.nvgRGBA(0,0,0,255),linewidth=1,linestyle=None):
        """
        绘制横线
        """
        self._xk = None
        self._xb = None
        self._hline.append((y,color,linewidth,linestyle))
    def vline(self,x,color=vg.nvgRGBA(0,0,0,255),linewidth=1,linestyle=None):
        """
        绘制竖线
        """
        self._xk = None
        self._xb = None
        self._vline.append((x,color,linewidth,linestyle))
    def setTitle(self,title):
        self._title = title
    def setTitleColor(self,c):
        self._titleColor = c
    def setTitleSize(self,s):
        self._titleSize = s
    def clear(self):
        """
        清除图表中的全部曲线，重新设置数据
        """
        self._x = None
        self._y = []
        self._hline = []
        self._vline = []
        self._ye = None
        self._xe = None
        self._xticks = None
        self._yticks = None
    def prepareRender(self,x,y,w,h):
        """
        渲染前的准备
        """
        if self._x is None or len(self._x)==0:
            return
        self._area[0]=x
        self._area[1]=y
        self._area[2]=w
        self._area[3]=h
        self._xmax = self._x.max()
        self._xmin = self._x.min()
        self._oxmin,self._oxmax = self._xmin,self._xmax
        self._xk = 1/(self._xmax-self._xmin)
        self._xb = -self._xmin*self._xk
        self._ymax = -1e10
        self._ymin = 1e10
        hasbar = False
        for yp in self._y:
            y = yp[0]
            ynan = y[y==y] #如果数据中存在NaN max()将返回NaN
            if len(ynan)>0:
                self._ymax = max(self._ymax,ynan.max())
                self._ymin = min(self._ymin,ynan.min())
            if yp[5]==Plot.BAR:
                hasbar = True
        if hasbar and self._ymin>0:
             self._ymin = 0

        self._oymin,self._oymax = self._ymin,self._ymax
        #扩大一点y范围
        h = self._ymax-self._ymin
        self._ymax+=0.05*h
        self._ymin-=0.05*h
        self._yk = 1/(self._ymax-self._ymin)
        self._yb = -self._ymin*self._yk
        if self._gridx:
            if self._xticks is None and self._oxmax-self._oxmin>0:
                delta,self._xe = pone((self._oxmax-self._oxmin)/10) #_ye是精度
                bi = precision(self._oxmin-self._oxmin%delta,self._xe)
                self._xticks = np.arange(bi,self._oxmax,delta)
        if self._gridy:
            if self._yticks is None and self._oymax-self._oymin>0:
                delta,self._ye = pone((self._oymax-self._oymin)/10) #_ye是精度
                bi = precision(self._oymin-self._oymin%delta,self._ye)
                self._yticks = np.arange(bi,self._oymax,delta)
    def setTicks(self,xticks=None,yticks=None):
        """
        设置x,y轴的网格线
        可以是形如[x0,x1,...]或者[(x0,txt0),...]
        """
        self._xticks = xticks
        self._yticks = yticks
    def setTicksAngle(self,ax=0,ay=0):
        self._xtickangle = vg.nvgDegToRad(ax)
        self._ytickangle = vg.nvgDegToRad(ay)
    def setGrid(self,xb,yb):
        """
        自动添加网格线
        """
        self._gridx =xb
        self._gridy =yb
    def setAxisVisiable(self,bx,by):
        self._xtickshow = bx
        self._ytickshow = by
    def setOuterSpace(self,right,left,top,bottom):
        """
        设置图表外边框预留的空间
        """
        self._border[0] = right
        self._border[1] = left
        self._border[2] = top
        self._border[3] = bottom
    def setInnerSpace(self,right,left,top,bottom):
        """
        设置图表内边框预留的空间
        """       
        self._inner[0] = right
        self._inner[1] = left
        self._inner[2] = top
        self._inner[3] = bottom         
    def plotRect(self):
        """
        返回图表矩形区域
        """
        x0 = self._area[0]+self._border[0]
        y0 = self._area[1]+self._border[2]
        w0 = self._area[2]-self._border[0]-self._border[1]
        h0 = self._area[3]-self._border[2]-self._border[3]        
        return x0,y0,w0,h0
    def calcxkxb(self):
        if self._xk is None:
            self._xmax = self._x.max()
            self._xmin = self._x.min()
            self._oxmin,self._oxmax = self._xmin,self._xmax
            self._xk = 1/(self._xmax-self._xmin)
            self._xb = -self._xmin*self._xk
    def xAxis2wx(self,x):
        """
        从x轴数据空间映射到屏幕x坐标
        """
        self.calcxkxb()
        x0,y0,w0,h0 = self.plotRect()
        x0+=self._inner[0]
        w0-=self._inner[0]+self._inner[1]
        wx = w0*(x*self._xk+self._xb)+x0
        return wx      
    def wx2x(self,wx):
        """
        将屏幕坐标映射到数据
        """
        self.calcxkxb()
        x0,y0,w0,h0 = self.plotRect()
        x0+=self._inner[0]
        w0-=self._inner[0]+self._inner[1]
        return ((wx-x0)/w0-self._xb)/self._xk
    def yAxis2wy(self,y):
        """
        从y轴数据空间映射到屏幕y坐标
        """
        self.calcxkxb()
        x0,y0,w0,h0 = self.plotRect()
        y0+=self._inner[2]
        h0-=self._inner[2]+self._inner[3]
        wy = h0*(1-(y*self._yk+self._yb))+y0 #y反转
        return wy
    def wy2y(self,wy):
        self.calcxkxb()
        x0,y0,w0,h0 = self.plotRect()
        y0+=self._inner[2]
        h0-=self._inner[2]+self._inner[3]
        return (1-(wy-y0)/h0-self._yb)/self._yk
    def x2AxisLabel(self,x):
        if self._xe is None:
            return str(x)
        else:
            if self._xe<0:
                fmt = "%%.%df"%abs(self._xe)
            else:
                fmt = "%.0f"
            return fmt%x
    def y2AxisLabel(self,y):
        if self._ye is None:
            return str(y)
        else:
            if self._ye<0:
                fmt = "%%.%df"%abs(self._ye)
            else:
                if self._ye>3:
                    y = int(y/math.pow(10,self._ye))
                fmt = "%.0f"
            return fmt%y
    def renderAxis(self,canvas):
        """
        渲染背景于坐标，包括标题
        """
        a = self._area
        b = self._border
        x0,y0,w0,h0 = self.plotRect()
        canvas.strokeWidth(1)
        canvas.beginPath()
        canvas.rect(x0,y0,w0,h0)
        #canvas.fillColor(vg.nvgRGBA(255,255,255,255))
        canvas.strokeColor(self._themos.AXISCOLOR)
        canvas.stroke()
        canvas.fontFace("sans")
        canvas.fontSize(13.0)
        canvas.fillColor(self._themos.TEXTCOLOR)
        if self._xticks is not None:
            if self._xtickangle==0:
                canvas.textAlign(vg.NVG_ALIGN_CENTER|vg.NVG_ALIGN_TOP)
            else:
                if self._xtickangle>0:
                    canvas.textAlign(vg.NVG_ALIGN_RIGHT|vg.NVG_ALIGN_TOP)
                else:
                    canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_TOP)
            for ox in self._xticks:
                if type(ox)==tuple:
                    x = self.xAxis2wx(ox[0])
                    txt = ox[1]
                else:
                    x = self.xAxis2wx(ox)
                    txt = self.x2AxisLabel(ox)                    
                if x>x0 and x<x0+w0:
                    canvas.beginPath()
                    canvas.strokeColor(self._themos.GRIDCOLOR)
                    canvas.moveTo(x,y0)
                    canvas.lineTo(x,y0+h0)
                    canvas.stroke()
                    if self._xtickshow:
                        canvas.translate(x,y0+h0+2)
                        canvas.rotate(-self._xtickangle)
                        canvas.text(0,0,txt)
                        canvas.resetTransform()
        if self._yticks is not None:
            canvas.textAlign(vg.NVG_ALIGN_RIGHT|vg.NVG_ALIGN_MIDDLE)
            for oy in self._yticks:
                if type(oy)==tuple:
                    y = self.xAxis2wx(oy[0])
                    txt = oy[1]
                else:
                    y = self.xAxis2wx(oy)
                    txt = self.y2AxisLabel(oy)                   
                y = self.yAxis2wy(oy)
                if y>y0 and y<y0+h0:
                    canvas.beginPath()
                    canvas.strokeColor(self._themos.GRIDCOLOR)
                    canvas.moveTo(x0,y)
                    canvas.lineTo(x0+w0,y)
                    canvas.stroke()
                    if self._ytickshow:
                        canvas.translate(x0-2,y)
                        canvas.rotate(-self._ytickangle)
                        canvas.text(0,0,txt)
                        canvas.resetTransform()
            if self._ye is not None and self._ye>3: #绘制坐标指数
                canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_TOP)
                canvas.text(x0,y0,"1e%d"%self._ye)
        if self._titleColor is not None:
            canvas.fillColor(self._titleColor)
        canvas.textAlign(vg.NVG_ALIGN_CENTER|vg.NVG_ALIGN_TOP)
        canvas.fontFace("zh")
        canvas.fontSize(self._titleSize)
        canvas.text(x0+w0/2,y0+4,self._title)
    def setLineWidthScale(self,sc=1):
        self._lwscale = sc
    """
    将图表渲染出来
    """
    def render(self,canvas,x0,y0,w,h):
        self.prepareRender(x0,y0,w,h)
        self.renderAxis(canvas)
        if self._x is None or len(self._x)==0:
            return
        xy = np.empty((len(self._x),2),dtype=np.float32)
        xy[:,0] = self.xAxis2wx(self._x) #w*(self._x*self._xk+self._xb)+x0
        for yp in self._y:
            y = yp[0]
            color = yp[1]
            linewidth = yp[2]
            linestyle = yp[3]
            label = yp[4]
            type1 = yp[5]
            if type1==Plot.LINE:
                canvas.beginPath()
                canvas.strokeColor(color)
                canvas.strokeWidth(linewidth*self._lwscale)
                xy[:,1] = self.yAxis2wy(y) #xy[:,1] = h*(y*self._yk+self._yb)+y0
                #数据使用NaN分段
                fz = False
                bi = 0
                for i in range(len(self._x)):
                    if xy[i,1]==xy[i,1]:
                        if not fz:
                            bi = i
                            fz = True
                    else:#is NaN
                        if fz:
                            pts = xy[bi:i].ctypes.data_as(Plot.c_float_p)
                            canvas.line(pts,i-bi,linestyle)
                        fz = False
                if fz:
                    pts = xy[bi:i+1].ctypes.data_as(Plot.c_float_p)
                    canvas.line(pts,i+1-bi,linestyle)
                canvas.stroke()
            elif type1==Plot.K: #分别对应0 open 1 high 2 low 3 close
                Y = self.yAxis2wy(y) #xy[:,1] = h*(y*self._yk+self._yb)+y0
                RED  = self._themos.RED_KCOLOR
                GREEN = self._themos.GREEN_KCOLOR
                WHITE = self._themos.BG_COLOR
                dx = xy[1,0]-xy[0,0]-2
                for i in range(len(self._x)):
                    x = xy[i,0]
                    k = Y[i]
                    canvas.beginPath()
                    canvas.strokeColor(RED if k[3]<k[0] else GREEN)
                    canvas.strokeWidth(1*self._lwscale)
                    canvas.moveTo(x,k[2])
                    canvas.lineTo(x,k[1])
                    canvas.stroke()
                    canvas.beginPath()
                    canvas.rect(x-dx/2,k[0],dx,k[3]-k[0])
                    if k[3]<k[0]:
                        canvas.fillColor(WHITE)
                        canvas.fill()
                        canvas.stroke()
                    else:
                        canvas.fillColor(GREEN)
                        canvas.fill()
            elif type1==Plot.BAR: #条形图
                Y = self.yAxis2wy(y)
                oy = self.yAxis2wy(0)
                dx = xy[1,0]-xy[0,0]-2
                for i in range(len(self._x)):
                    x = xy[i,0]
                    canvas.beginPath()
                    if type(color)==list:
                        canvas.fillColor(color[i])
                    else:
                        canvas.fillColor(color)
                    canvas.rect(x-dx/2,oy,dx,Y[i]-oy)
                    canvas.fill()
        if len(self._hline)>0 or len(self._vline)>0:
            xy = np.empty((2,2),dtype=np.float32)
            xy[0,0] = self.xAxis2wx(self._x.min())
            xy[1,0] = self.xAxis2wx(self._x.max())
            for hl in self._hline:
                xy[:,1] = self.yAxis2wy(hl[0])
                canvas.beginPath()
                canvas.strokeColor(hl[1])
                canvas.strokeWidth(hl[2]*self._lwscale)
                pts = xy.ctypes.data_as(Plot.c_float_p)
                canvas.line(pts,2,hl[3])
                canvas.stroke()
            """
            xy[0,1] = self.xAxis2wx(self._y.min())
            xy[1,1] = self.xAxis2wx(self._y.max())
            for hl in self._vline:
                xy[:,0] = self.xAxis2wx(hl[0])
                canvas.beginPath()
                canvas.strokeColor(hl[1])
                canvas.strokeWidth(hl[2]*self._lwscale)
                pts = xy.ctypes.data_as(Plot.c_float_p)
                canvas.line(pts,2,hl[3])
                canvas.stroke()               
            """
         
        canvas.restore()