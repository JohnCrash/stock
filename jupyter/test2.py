from app.nanovg import window,vg
from app import monitor,xueqiu,stock
from datetime import date,datetime,timedelta
import numpy as np
import math
import sdl2
from OpenGL import GL
import ctypes
"""
绘制图表
"""
class Plot:
    c_float_p = ctypes.POINTER(ctypes.c_float)
    AXISCOLOR = vg.nvgRGBf(0,0,0)
    GRIDCOLOR = vg.nvgRGBf(0.8,0.8,0.8)
    TEXTCOLOR = vg.nvgRGBf(0,0,0)
    def __init__(self):
        self._x = None
        self._xlabels = None
        self._y = []
        self._title = ''
        self._xticks = None
        self._yticks = None
        self._area = [0,0,0,0]
        self._border =[0,0,0,0]
        self._grid = False
    def setx(self,x,labels=None):
        """
        设置x轴数据,labels=[(i,label),...]
        """
        self._x  = x
        self._xlabels = labels
    def plot(self,y,color=vg.nvgRGBA(0,0,0,255),linewidth=1,linestyle=None,label=None):
        """
        绘制线型图表
        """
        self._y.append((y,color,linewidth,linestyle,label)) #0 y,1 color,2 linewidth,3 linestyle,4 label
    def setTitle(self,title):
        self._title = title
    def clear(self):
        self._x = None
        self._y = []
    def prepareRender(self,x,y,w,h):
        """
        渲染前的准备
        """
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
        for yp in self._y:
            y = yp[0]
            self._ymax = max(self._ymax,y.max())
            self._ymin = min(self._ymin,y.min())
        self._oymin,self._oymax = self._ymin,self._ymax
        #扩大一点y范围
        h = self._ymax-self._ymin
        self._ymax+=0.05*h
        self._ymin-=0.05*h
        self._yk = 1/(self._ymax-self._ymin)
        self._yb = -self._ymin*self._yk
        if self._grid:
            if self._xticks is None:
                self._xticks = np.linspace(self._oxmin,self._oxmax,8)
            if self._yticks is None:
                self._yticks = np.linspace(self._oymin,self._oymax,8)
    def setTicks(self,xticks=None,yticks=None):
        """
        设置x,y轴的网格线
        """
        self._xticks = xticks
        self._yticks = yticks
    def setGrid(self,b):
        """
        自动添加网格线
        """
        self._grid = b

    def setBorderSpace(self,right,left,top,bottom):
        """
        设置图表边框预留的空间
        """
        self._border[0] = right
        self._border[1] = left
        self._border[2] = top
        self._border[3] = bottom
    def plotRect(self):
        """
        返回图表矩形区域
        """
        x0 = self._area[0]+self._border[0]
        y0 = self._area[1]+self._border[2]
        w0 = self._area[2]-self._border[0]-self._border[1]
        h0 = self._area[3]-self._border[2]-self._border[3]        
        return x0,y0,w0,h0
    def xAxis2wx(self,x):
        """
        从x轴数据空间映射到屏幕x坐标
        """
        x0,y0,w0,h0 = self.plotRect()
        wx = w0*(x*self._xk+self._xb)+x0
        return wx
    def yAxis2wy(self,y):
        """
        从y轴数据空间映射到屏幕y坐标
        """
        x0,y0,w0,h0 = self.plotRect()
        wy = h0*(1-(y*self._yk+self._yb))+y0 #y反转
        return wy
    def x2AxisLabel(self,x):
        return "%.2f"%x
    def y2AxisLabel(self,y):
        return "%.2f"%y
    def renderAxis(self,canvas):
        """
        渲染背景于坐标，包括标题
        """
        a = self._area
        b = self._border
        x0,y0,w0,h0 = self.plotRect()
        canvas.beginPath()
        canvas.rect(x0,y0,w0,h0)
        #canvas.fillColor(vg.nvgRGBA(255,255,255,255))
        canvas.strokeColor(Plot.AXISCOLOR)
        canvas.stroke()
        canvas.fontFace("zh")
        canvas.fontSize(13.0)
        canvas.fillColor(Plot.TEXTCOLOR)
        if self._xticks is not None:
            canvas.textAlign(vg.NVG_ALIGN_CENTER|vg.NVG_ALIGN_TOP)
            for ox in self._xticks:
                x = self.xAxis2wx(ox)
                if x>x0 and x<x0+w0:
                    canvas.beginPath()
                    canvas.strokeColor(Plot.GRIDCOLOR)
                    canvas.moveTo(x,y0)
                    canvas.lineTo(x,y0+h0)
                    canvas.stroke()
                    canvas.text(x,y0+h0+2,self.x2AxisLabel(ox))
        if self._yticks is not None:
            canvas.textAlign(vg.NVG_ALIGN_RIGHT|vg.NVG_ALIGN_MIDDLE)
            for oy in self._yticks:
                y = self.yAxis2wy(oy)
                if y>y0 and y<y0+h0:
                    canvas.beginPath()
                    canvas.strokeColor(Plot.GRIDCOLOR)
                    canvas.moveTo(x0,y)
                    canvas.lineTo(x0+w0,y)
                    canvas.stroke()
                    canvas.text(x0-2,y,self.y2AxisLabel(oy))
        canvas.textAlign(vg.NVG_ALIGN_CENTER|vg.NVG_ALIGN_TOP)
        canvas.fontSize(18)
        canvas.text(x0+w0/2,y0+2,self._title)
    """
    将图表渲染出来
    """
    def render(self,canvas,x0,y0,w,h):
        self.prepareRender(x0,y0,w,h)
        self.renderAxis(canvas)

        
        xy = np.empty((len(self._x),2),dtype=np.float32)
        xy[:,0] = self.xAxis2wx(self._x) #w*(self._x*self._xk+self._xb)+x0
        pts = xy.ctypes.data_as(Plot.c_float_p)
        for yp in self._y:
            y = yp[0]
            color = yp[1]
            linewidth = yp[2]
            linestyle = yp[3]
            label = yp[4]
            canvas.beginPath()
            canvas.strokeColor(color)
            canvas.strokeWidth(linewidth)
            xy[:,1] = self.yAxis2wy(y)#xy[:,1] = h*(y*self._yk+self._yb)+y0
            canvas.line(pts,len(self._x),linestyle)
            canvas.stroke()
        
        canvas.restore()

def strong2color(s):
    """
    将强度映射成颜色 s = [-1,1]
    """
    rgb = []
    for b in range(255,0,-1):#紫色到红到
        rgb.append((255,0,b))
    for g in range(255): #红到黄
        rgb.append((255,g,0))
    for r in range(255,0,-1): #红到绿
        rgb.append((r,255,0))
    for b in range(255): #绿的青
        rgb.append((0,255,b))
    if s>1:
        s=1
    if s<-1:
        s=-1
    i = int((1-(s+1)/2)*(len(rgb)-1))

    return rgb[i]
class MyPlot(window.frame):
    def __init__(self,title,w,h):
        super(MyPlot,self).__init__(title,w,h)
        self._myplot = Plot()
        self._volplot = Plot()
        #x = np.arange(100)
        #y = np.sin(x*4*np.pi/200)
        #y2 = np.cos(x*4*np.pi/200)
        k,d = monitor.get_rt(4)
        companys = xueqiu.get_company_select()
        #y = x#np.sin(x)
        for i in range(len(companys)):
            com = companys[i]
            if com[1]=='SH000001':
                self._myplot.setTitle(com[2])
                x = np.arange(len(d))
                self._myplot.setx(x)
                self._myplot.plot(k[i,:,0])
                ma60 = stock.ma(k[i,:,0],60)
                self._myplot.plot(ma60,color=vg.nvgRGBf(1,0.4,0.2),linestyle=(4,2,0))
                self._volplot.setx(x)
                hug = np.copy(k[i,:,3]+k[i,:,4])
                hug[hug!=hug]=0
                self._volplot.plot(hug,color=vg.nvgRGBf(1,0,1),linewidth=3,linestyle=(4,2,0))
                ting = np.copy(k[i,:,6])
                ting[ting!=ting]=0
                self._volplot.plot(ting,color=vg.nvgRGBf(0,0,0.6))
        self._myplot.setGrid(True)
        self._volplot.setGrid(True)
        self._volplot.setBorderSpace(80,0,0,0)
        self._myplot.setBorderSpace(80,0,0,50)
    def render(self,dt,w,h):
        self._canvas.beginFrame(w, h, w / h)
        #self._myplot.render(self._canvas,15,15,w-30,h/2)
        #self._volplot.render(self._canvas,15,h/2-15,w-30,h/2-30)
        cvs = self._canvas
        for x in range(0,1000,10):
            cvs.beginPath()
            c = strong2color(2*(x/1000-0.5))
            r = 0.9
            cvs.fillColor(vg.nvgRGB(int(c[0]*r),int(c[1]*r),int(c[2]*r)))
            cvs.rect(x,50,10,50)
            cvs.fill()

        graph.update(dt)
        graph.render(self._canvas,5,5)
        self._canvas.endFrame()

    def keyDown(self,event):
        if event.keysym.sym==ord('q'):#sdl2.SDLK_a:
            self.quit()

glwin = MyPlot('图表',640,480)
graph = window.fpsGraph()
glwin.setInterval(10)
glwin.run()
