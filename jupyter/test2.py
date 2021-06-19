from app.nanovg import window,vg
import sdl2
from OpenGL import GL
"""
绘制图表
"""
class Plot:
    def __init__(self):
        pass
    """
    绘制一个线图表
    x可以是时间[(datetime,),...]
    """    
    def line(self,x,y,color,linewidth,linestyle):
        pass
    """
    绘制一个K线图,k = [(open,low,high,close),...] , d = [(datetime,),...]
    """
    def k(self,k,d):
        pass
    """
    绘制柱图
    """
    def bar(self,x,y):
        pass
    """
    用于绘制背景x轴,y轴
    """
    def background(_vg,x,y,w,h):
        pass
    """
    将图表渲染出来
    """
    def render(_vg,x,y,w,h):
        vg.nvgSave(_vg)
        vg.nvgBeginPath(_vg)
        vg.nvgRoundedRect(_vg, 1,1,w-2,h-2, 10)
        vg.nvgFillColor(_vg, vg.nvgRGBA(28,30,34,192))
        vg.nvgFillColor(_vg, vg.nvgRGBA(0,0,0,128))
        vg.nvgFill(_vg)    
        
class MyPlot(window.frame):
    def __init__(self,title,w,h):
        super(MyPlot,self).__init__(title,w,h)
    
    def render(self,dt,w,h):
        vg.nvgBeginFrame(self._vg, w, h, w / h)
        graph.update(dt)
        graph.render(self._vg,5,5)
        vg.nvgSave(self._vg)
        vg.nvgBeginPath(self._vg)
        vg.nvgRoundedRect(self._vg, 1,1,w-2,h-2, 10)
        vg.nvgFillColor(self._vg, vg.nvgRGBA(28,30,34,192))
        vg.nvgFillColor(self._vg, vg.nvgRGBA(0,0,0,128))
        vg.nvgFill(self._vg)    
        vg.nvgEndFrame(self._vg)

    def keyDown(self,event):
        if event.keysym.sym==ord('q'):#sdl2.SDLK_a:
            self.quit()

glwin = MyPlot('图表',640,480)
graph = window.fpsGraph()
glwin.setInterval(10)
glwin.run()
