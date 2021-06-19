#!/usr/bin/python2.7
"""Quick hack of 'modern' OpenGL example using pysdl2 and pyopengl
Based on
pysdl2 OpenGL example
http://www.arcsynthesis.org/gltut/Basics/Tut02%20Vertex%20Attributes.html
http://schi.iteye.com/blog/1969710
"""
import sys
import ctypes
from OpenGL.error import GLError
import numpy

from OpenGL import GL, GLU
from OpenGL.GL import shaders
from OpenGL.arrays import vbo

import sdl2
from sdl2 import video
from numpy import array
from sdl2.timer import SDL_GetTicks
from app.nanovg import vg
from ctypes import CDLL, POINTER, Structure, Union,c_int,c_uint,c_void_p,c_float,c_char_p,c_ubyte,c_bool
shaderProgram = None
VAO = None
VBO = None

def initialize():
    global shaderProgram
    global VAO
    global VBO

    vertexShader = shaders.compileShader("""
#version 330
layout (location=0) in vec4 position;
layout (location=1) in vec4 colour;
smooth out vec4 theColour;
void main()
{
    gl_Position = position;
    theColour = colour;
}
""", GL.GL_VERTEX_SHADER)

    fragmentShader = shaders.compileShader("""
#version 330
smooth in vec4 theColour;
out vec4 outputColour;
void main()
{
    outputColour = theColour;
}
""", GL.GL_FRAGMENT_SHADER)

    shaderProgram = shaders.compileProgram(vertexShader, fragmentShader)

    vertexData = numpy.array([
	# Vertex Positions
        0.0, 0.5, 0.0, 1.0,
        0.5, -0.366, 0.0, 1.0,
        -0.5, -0.366, 0.0, 1.0,

	# Vertex Colours
        1.0, 0.0, 0.0, 1.0,
        0.0, 1.0, 0.0, 1.0,
        0.0, 0.0, 1.0, 1.0,
    ], dtype=numpy.float32)

    # Core OpenGL requires that at least one OpenGL vertex array be bound
    VAO = GL.glGenVertexArrays(1)
    GL.glBindVertexArray(VAO)

    # Need VBO for triangle vertices and colours
    VBO = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, VBO)
    GL.glBufferData(GL.GL_ARRAY_BUFFER, vertexData.nbytes, vertexData,
        GL.GL_STATIC_DRAW)

    # enable array and set up data
    GL.glEnableVertexAttribArray(0)
    GL.glEnableVertexAttribArray(1)
    GL.glVertexAttribPointer(0, 4, GL.GL_FLOAT, GL.GL_FALSE, 0,
        None)
    # the last parameter is a pointer
    GL.glVertexAttribPointer(1, 4, GL.GL_FLOAT, GL.GL_FALSE, 0,
        ctypes.c_void_p(48))

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glBindVertexArray(0)


def render():
    global shaderProgram
    global VAO
    GL.glClearColor(0, 0, 0, 1)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    # active shader program
    GL.glUseProgram(shaderProgram)

    try:
        GL.glBindVertexArray(VAO)

        # draw triangle
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
    finally:
        GL.glBindVertexArray(0)
        GL.glUseProgram(0)

def loadDemoData(_vg):
    data = {}
    data['images'] = []
    path = b'D:/source/SDL/build/win32'
    for i in range(12):
        file = b"%s/example/images/image%d.jpg"%(path,i+1)
        data['images'].append(vg.nvgCreateImage(_vg, file, 0))
        if data['images'][-1]==0:
            print("Could not load %s."%file)
            return -1
    
    data['fontIcons'] = vg.nvgCreateFont(_vg, b"icons", b"%s/example/entypo.ttf"%path)
    if data['fontIcons'] == -1:
        print("Could not add font icons.\n")
        return -1

    data['fontNormal'] = vg.nvgCreateFont(_vg, b"sans", b"%s/example/Roboto-Regular.ttf"%path)
    if data['fontNormal'] == -1:
        print("Could not add font italic.\n")
        return -1

    data['fontBold'] = vg.nvgCreateFont(_vg, b"sans-bold", b"%s/example/Roboto-Bold.ttf"%path)
    if data['fontBold'] == -1:
        print("Could not add font bold.\n")
        return -1

    data['fontEmoji'] = vg.nvgCreateFont(_vg, b"emoji", b"%s/example/NotoEmoji-Regular.ttf"%path)
    if data['fontEmoji'] == -1:
        print("Could not add font emoji.\n")
        return -1

    vg.nvgAddFallbackFontId(_vg, data['fontNormal'], data['fontEmoji'])
    vg.nvgAddFallbackFontId(_vg, data['fontBold'], data['fontEmoji'])
    return data

class vgGraph:
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
    def render(self,_vg,x,y):
        avg = self.getGraphAverage()
        w = 200
        h = 35
        vg.nvgBeginPath(_vg)
        vg.nvgRect(_vg, x,y, w,h)
        vg.nvgFillColor(_vg, vg.nvgRGBA(0,0,0,128))
        vg.nvgFill(_vg)
        vg.nvgBeginPath(_vg)
        vg.nvgMoveTo(_vg, x, y+h)

        for i in range(100):
            v = 1.0 / (0.00001 + self._values[(self._head+i) % 100])
            if v > 80.0:
                v = 80.0
            vx = x + (float(i)/(100-1)) * w
            vy = y + h - ((v / 80.0) * h)
            vg.nvgLineTo(_vg, vx, vy)
        
        vg.nvgLineTo(_vg, x+w, y+h)
        vg.nvgFillColor(_vg, vg.nvgRGBA(255,192,0,128))
        vg.nvgFill(_vg)

        vg.nvgFontFace(_vg, b"sans")

        vg.nvgFontSize(_vg, 15.0)
        vg.nvgTextAlign(_vg,vg.NVG_ALIGN_RIGHT|vg.NVG_ALIGN_TOP)
        vg.nvgFillColor(_vg, vg.nvgRGBA(240,240,240,255))
        s = b"%.2f FPS"%(1.0 / avg)
        vg.nvgText(_vg, x+w-3,y+3, s, None)
        vg.nvgFontSize(_vg, 13.)
        vg.nvgTextAlign(_vg,vg.NVG_ALIGN_RIGHT|vg.NVG_ALIGN_BASELINE)
        vg.nvgFillColor(_vg, vg.nvgRGBA(240,240,240,160))
        s = b"%.2f ms"%(avg * 1000.0)
        vg.nvgText(_vg, x+w-3,y+h-3, s, None)

def run():
    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
        print(sdl2.SDL_GetError())
        return -1

    window = sdl2.SDL_CreateWindow(b"OpenGL demo",
                                   sdl2.SDL_WINDOWPOS_UNDEFINED,
                                   sdl2.SDL_WINDOWPOS_UNDEFINED, 320, 200,
                                   sdl2.SDL_WINDOW_OPENGL|sdl2.SDL_WINDOW_RESIZABLE)
    if not window:
        print(sdl2.SDL_GetError())
        return -1

    # Force OpenGL 3.3 'core' context.
    # Must set *before* creating GL context!
    """
    video.SDL_GL_SetAttribute(video.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
    video.SDL_GL_SetAttribute(video.SDL_GL_CONTEXT_MINOR_VERSION, 3)
    video.SDL_GL_SetAttribute(video.SDL_GL_CONTEXT_PROFILE_MASK,
        video.SDL_GL_CONTEXT_PROFILE_CORE)
    """
    context = sdl2.SDL_GL_CreateContext(window)
    sdl2.SDL_GL_MakeCurrent(window,context)
    # Setup GL shaders, data, etc.
    initialize()
    if vg.glewInit()!=vg.GLEW_OK:
        print("glew初始化失败")
    _vg = vg.nvgCreateGLES(vg.NVG_ANTIALIAS | vg.NVG_STENCIL_STROKES)
    data = loadDemoData(_vg)
    g = vgGraph()
    prevt = 0
    event = sdl2.SDL_Event()
    running = True
    sdl2.SDL_GL_SetSwapInterval(-1) #控制最大刷新频率
    while running:
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == sdl2.SDL_QUIT:
                running = False

        #render()
        w,h = c_int(),c_int()
        video.SDL_GetWindowSize(window, ctypes.byref(w), ctypes.byref(h))
        t = SDL_GetTicks()/1000.
        dt = t-prevt
        prevt = t
        print(dt)
        
        g.update(dt)
        fbWidth,fbHeight = w.value,h.value
        GL.glViewport(0, 0, fbWidth, fbHeight)
        if False:
            GL.glClearColor(0, 0, 0, 0)
        else:
            GL.glClearColor(0.3, 0.3, 0.32, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT | GL.GL_STENCIL_BUFFER_BIT)
        
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glDisable(GL.GL_DEPTH_TEST)
        vg.nvgBeginFrame(_vg, fbWidth, fbHeight, fbWidth / fbHeight)
        g.render(_vg,5, 5)
        vg.nvgEndFrame(_vg)
        
        sdl2.SDL_GL_SwapWindow(window)
        
        #sdl2.SDL_Delay(10)

    vg.nvgDeleteGLES(_vg)
    sdl2.SDL_GL_DeleteContext(context)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()
    return 0

if __name__ == "__main__":
    sys.exit(run())