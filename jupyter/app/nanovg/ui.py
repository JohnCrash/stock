from . import vg,themos
from .canvas import Canvas2d
from datetime import datetime
import sdl2
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
        pass
    def mouse(self,action,x,y):
        """
        如果成功处理了返回True
        """
        return False
    def render(self,canvas):
        pass
class window(ui):
    def __init__(self,app,ps):
        self._app = app
        self._ps = ps
        self._drop = False
        self._name = "window%s"%str(datetime.today())
        pt = ps["pos"]
        size = ps["size"]
        self._pt = pt
        self._size = size
        app.registerHook("event",self.eventCallback)
        app.createFrame(pt[0],pt[1],size[0],size[1],self._name)
        self._child = self.parse(ps)
        self.renderSelf()
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
        else:
            return False
        return True

    def renderSelf(self):
        canvas,w,h = self._app.beginFrame(self._name)
        if canvas is not None:
            self.render(canvas) #绘制窗口
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
    def render(self,canvas):
        #首先绘制窗口
        w,h = self._ps['size']
        canvas.beginPath() #绘制标题头
        canvas.fillColor(vg.nvgRGBA(*self._ps['bgcolor']) if 'bgcolor' in self._ps else Themos.BG_COLOR)
        canvas.roundedRect(0,0,w,h,3)
        canvas.fill()
        canvas.beginPath()
        r = 3 if 'round' not in self._ps else self._ps['round']
        titleh = 32 if 'titleheight' not in self._ps else self._ps['titleheight']
        canvas.fillColor(vg.nvgRGBA(*self._ps['titlecolor']) if 'titlecolor' in self._ps else Themos.PRICE_COLOR)
        canvas.roundedRect(0,0,w,titleh,r)
        canvas.fill()
        canvas.beginPath()
        canvas.fillColor(vg.nvgRGBA(*self._ps['bgcolor']) if 'bgcolor' in self._ps else Themos.BG_COLOR)
        canvas.rect(0,titleh-r,w,r)
        canvas.fill()
        canvas.beginPath()
        linearG = canvas.linearGradient(0,titleh-r,0,titleh-r+3*r,vg.nvgRGBA(0,0,0,32),vg.nvgRGBA(0,0,0,0))
        canvas.rect(0,titleh-r,w,3*r)
        canvas.fillPaint(linearG)
        canvas.fill()
        if 'title' in self._ps: #存在标题栏
            canvas.fontFace('zh' if 'font' not in self._ps else self._ps['font'])
            canvas.fontSize(14 if 'fontsize' not in self._ps else self._ps['fontsize'])
            canvas.fillColor(Themos.TEXTCOLOR if 'fontcolor' not in self._ps else vg.nvgRGBA(*self._ps['fontcolor']))
            canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_MIDDLE)
            canvas.text(titleh/2,titleh/2,self._ps['title'])
        #然后绘制子窗口
        for kit in self._child:
            kit.render(canvas)
    def close(self):
        """
        关闭窗口界面
        """
        self._app.deleteFrame(self._name)
        self._app.unregisterHook("event",self.eventCallback)
class label(ui):
    def __init__(self,parent,ps):
        self._parent = parent
        self._ps = ps
    def render(self,canvas):
        canvas.fontFace('zh' if 'font' not in self._ps else self._ps['font'])
        canvas.fontSize(14 if 'fontsize' not in self._ps else self._ps['fontsize'])
        canvas.fillColor(Themos.TEXTCOLOR if 'fontcolor' not in self._ps else vg.nvgRGBA(*self._ps['fontcolor']))
        canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_TOP)
        x,y = self._ps['pos']
        canvas.text(x,y,self._ps['label'])
class button(ui):
    def __init__(self,parent,ps):
        self._isdown = False
        self._parent = parent
        self._ps = ps
    def render(self,canvas):
        x,y = self._ps['pos']
        w,h = self._ps['size']
        canvas.beginPath()
        if self._isdown:
            canvas.fillColor(vg.nvgRGBA(*self._ps['downcolor']) if 'downcolor' in self._ps else Themos.GREEN_COLOR)
        else:
            canvas.fillColor(vg.nvgRGBA(*self._ps['bgcolor']) if 'bgcolor' in self._ps else Themos.BG_COLOR)
        canvas.roundedRect(x,y,w,h,3)
        canvas.fill()

        canvas.fontFace('zh' if 'font' not in self._ps else self._ps['font'])
        canvas.fontSize(14 if 'fontsize' not in self._ps else self._ps['fontsize'])
        canvas.fillColor(Themos.TEXTCOLOR if 'fontcolor' not in self._ps else vg.nvgRGBA(*self._ps['fontcolor']))
        canvas.textAlign(vg.NVG_ALIGN_CENTER|vg.NVG_ALIGN_MIDDLE)
        canvas.text(x+w/2,y+h/2,self._ps['label'])
    def mouse(self,action,mx,my):
        if action==ui.MouseDown or action==ui.MouseUp:
            x,y = self._ps['pos']
            w,h = self._ps['size']
            if mx>x and mx<x+w and my>y and my<y+h and action==ui.MouseDown:
                self._isdown = True
                self._parent.renderSelf()
            elif self._isdown:
                self._isdown = False
                self._parent.renderSelf()
                if 'onclick' in self._ps and mx>x and mx<x+w and my>y and my<y+h:
                    self._ps['onclick']()
class input(ui):
    def __init__(self,parent,ps):
        self._parent = parent
        self._ps = ps
        self._img = vg.nvgCreateImage(ps['img'],0)
    def render(self,canvas):
        x,y = self._ps['pos']
        w,h = self._ps['size']        
        imgw,imgh = canvas.imageSize(self._img)
        paint = canvas.imagePattern(0,0,imgw,imgh,0,self._img,1)
        canvas.beginPath()
        canvas.scale(w/imgw,h/imgh)
        canvas.rect(x,y,imgw,imgh)
        canvas.fillPaint(paint)
        canvas.fill()

class image(ui):
    def __init__(self,parent,ps):
        self._parent = parent
        self._ps = ps
    def render(self,canvas):
        pass

def test(self):
    def onclose():
        win.close()        
    win = window(self,{'pos':((self._w-320)/2,(self._h-200)/2),'size':(320,200),'title':'测试窗口','bgcolor':(220,220,220,255),'font':'zhb','fontcolor':(255,255,255,255),
        'child':[{'class':'button','label':'OK','pos':(200,160),'size':(72,32),'onclick':onclose}]})
