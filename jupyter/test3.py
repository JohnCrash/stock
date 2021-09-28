from app.nanovg import frame,vg,themos,ui
Themos = themos.ThemosBlack
class MyApp(frame.app):
    def __init__(self,title,w,h):
        super(MyApp,self).__init__(title,w,h)
        self.setWindowTitle('测试ui对象')
        self.createFrame(0,self.CAPTION_HEIGHT,self._w,self._h-self.CAPTION_HEIGHT,'graph')
        canvas,w,h = self.beginFrame('graph')
        canvas.beginPath()
        canvas.fillColor(vg.nvgRGB(64,64,64))
        canvas.rect(0,0,w,h)
        canvas.fill()
        self.endFrame()
        ui.test(self)
MyApp('图表',1600,800).run()