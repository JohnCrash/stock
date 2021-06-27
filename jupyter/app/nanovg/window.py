import ctypes
from ctypes import c_int
from OpenGL import GL
import sdl2
from sdl2 import video,events
from sdl2.timer import SDL_GetTicks
from . import vg
from .canvas import Canvas2d
"""
定义一个基本的VG窗口类
初始化字体
"""
class frame:
    def __init__(self,title,w,h):
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            raise RuntimeError('SDL_Init')

        self._window = sdl2.SDL_CreateWindow(title.encode('utf-8'),
                                    sdl2.SDL_WINDOWPOS_UNDEFINED,
                                    sdl2.SDL_WINDOWPOS_UNDEFINED, w, h,
                                    sdl2.SDL_WINDOW_OPENGL|sdl2.SDL_WINDOW_RESIZABLE)
        if not self._window:
            raise RuntimeError('SDL_CreateWindow')
        self._context = sdl2.SDL_GL_CreateContext(self._window)
        sdl2.SDL_GL_MakeCurrent(self._window,self._context)
        if vg.glewInit()!=vg.GLEW_OK:
            raise RuntimeError('glewInit')
        self._canvas = Canvas2d()
        self._render  = None
        self._running = True
        self._fps = 0
        self._interval = -1
        sdl2.SDL_GL_SetSwapInterval(0)
        self.loadDemoData()

    def quit(self):
        self._running = False

    def keyDown(self,event):
        pass
    def keyUp(self,event):
        pass
    def handleEvent(self,event):
        return False
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
                        self.keyDown(event.key)
                    elif event.type == sdl2.SDL_KEYUP:
                        self.keyUp(event.key)
            t = SDL_GetTicks()/1000.
            dt = t-prevt
            prevt = t
            if self._interval>0 and acc>self._interval:
                acc = 0
                self.update(dt)
            acc+=dt
            sdl2.SDL_Delay(10)
        sdl2.SDL_GL_DeleteContext(self._context)
        sdl2.SDL_DestroyWindow(self._window)
        sdl2.SDL_Quit()
        
    def setInterval(self,r):
        self._fps = r
        if r>0:
            self._interval = 1./r
        else:
            self._interval = -1

    def render(self,dt,w,h):
        pass

    def update(self,dt):
        w,h = c_int(),c_int()
        video.SDL_GetWindowSize(self._window, ctypes.byref(w), ctypes.byref(h))
        fbWidth,fbHeight = w.value,h.value
        GL.glViewport(0, 0, fbWidth, fbHeight)
        if False:
            GL.glClearColor(0, 0, 0, 0)
        else:
            GL.glClearColor(1,1, 1, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT | GL.GL_STENCIL_BUFFER_BIT)
        
        
        self.render(dt,fbWidth,fbHeight)
        
        sdl2.SDL_GL_SwapWindow(self._window)

    def loadDemoData(self):
        data = {}
        data['images'] = []
        path = 'D:/source/SDL/build/win32'
        for i in range(12):
            file = "%s/example/images/image%d.jpg"%(path,i+1)
            data['images'].append(self._canvas.createImage(file, 0))
            if data['images'][-1]==0:
                print("Could not load %s."%file)
                return -1
        
        data['fontIcons'] = self._canvas.createFont("icons", "%s/example/entypo.ttf"%path)
        if data['fontIcons'] == -1:
            print("Could not add font icons.\n")
            return -1

        data['fontNormal'] = self._canvas.createFont("sans", "%s/example/Roboto-Regular.ttf"%path)
        if data['fontNormal'] == -1:
            print("Could not add font italic.\n")
            return -1

        data['fontBold'] = self._canvas.createFont("sans-bold", "%s/example/Roboto-Bold.ttf"%path)
        if data['fontBold'] == -1:
            print("Could not add font bold.\n")
            return -1

        data['fontEmoji'] = self._canvas.createFont("emoji", "%s/example/NotoEmoji-Regular.ttf"%path)
        if data['fontEmoji'] == -1:
            print("Could not add font emoji.\n")
            return -1

        zh = self._canvas.createFont("zh", "c:/windows/fonts/simsun.ttc")
        if zh == -1:
            print("Could not add font zh.\n")
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
