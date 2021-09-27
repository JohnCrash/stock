from . import vg
from .canvas import Canvas2d
from datetime import datetime
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
class ui:
    MouseDown = 0
    MouseUp = 1
    MouseMove = 2
    def __init__(self):
        pass
    def mouse(self,action,x,y):
        """
        如果成功处理了返回True
        """
        pass
    def render(self,canvas,x,y,w,h):
        pass
class window(ui):
    def __init__(self,app,ps):
        self._child = []
        self._app = app
        self._ps = ps
        self._name = "window%s"%str(datetime.today())
        app.createFrame(x,y,w,h,self._name)
    def render(self):
        canvas,w,h = self._app.beginFrame(self._name)
        if canvas is None:
            self.render(canvas,0,0,w,h)
    def mouse(self,action,x,y):
        for kit in self._child:
            if kit.mouse(action,x,y):
                break
    def render(self,canvas,x,y,w,h):
        for kit in self._child:
            kit.render(canvas,x,y,w,h)
    def close(self):
        """
        关闭窗口界面
        """
        self._app.deleteFrame(self._name)
class label(ui):
    def _init__(self,parent):
        pass
class button(ui):
    def _init__(self,parent):
        pass

class input(ui):
    def _init__(self):
        pass

class image(ui):
    def _init__(self):
        pass
