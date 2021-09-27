from . import vg

class ThemosDefault:
    BGCOLOR = (0.95,0.95,0.95,1) #图表背景颜色

    MA60_COLOR = vg.nvgRGB(255,128,60) #ma60颜色
    PRICE_COLOR = vg.nvgRGB(70,130,200) #价格颜色
    MAIN_COLOR = vg.nvgRGB(255,0,255) #主力
    HUGE_COLOR = vg.nvgRGB(139,0,0)
    LARG_COLOR = vg.nvgRGB(255,0,0)
    MA5_COLOR = vg.nvgRGB(255,0,255)
    MA30_COLOR = vg.nvgRGB(0,0,255)
    MID_COLOR = vg.nvgRGB(255,215,0)
    TING_COLOR = vg.nvgRGB(135,206,250)
    RED_COLOR = vg.nvgRGB(220,0,0)   #涨
    GREEN_COLOR = vg.nvgRGB(0,120,0) #跌
    RED_KCOLOR = vg.nvgRGB(250,0,0)  
    GREEN_KCOLOR = vg.nvgRGB(0,244,244)      
    BG_COLOR = vg.nvgRGB(255,255,255) #背景
    CROSS_COLOR = vg.nvgRGBAf(0,0,0,0.5)
    YLABELWIDTH = 40   #y轴坐标轴空间
    XLABELHEIGHT = 30  #x轴坐标轴空间

    ORDER_BGCOLOR = vg.nvgRGB(220,220,220)
    ORDER_HEADCOLOR = vg.nvgRGB(64,96,196)
    ORDER_SELCOLOR = vg.nvgRGB(196,96,96)
    ORDER_TEXTBGCOLOR = vg.nvgRGBA(64,64,64,255)
    ORDER_TEXTCOLOR = vg.nvgRGB(255,255,255)  
    ORDER_TEXTCOLOR2 = vg.nvgRGB(255,255,0)
    ORDER_TEXTCOLOR3 = vg.nvgRGB(0,255,0)
    CAN_BUY_TEXTCOLOR = vg.nvgRGB(170,0,0)  #上轨和中轨向上
    CAN_BUY_TEXTCOLOR2 = vg.nvgRGB(70,0,140)  #都向上
    CAN_BUY_TEXTCOLOR3 = vg.nvgRGB(187,61,0)  #仅仅下轨向上
    WARN_BUY_COLOR = vg.nvgRGB(64,0,0)
    WARN_BUY_COLOR2 = vg.nvgRGB(128,0,0)
    WARN_NEWHIGH_COLOR = vg.nvgRGB(64,64,0)
    WARN_SELL_COLOR = vg.nvgRGB(0,64,0)
    WARN_SELL_COLOR2 = vg.nvgRGB(0,128,0)
    ORDER_WIDTH = 150       #排序栏宽度
    ORDER_ITEM_HEIGHT = 24  #排序栏按钮高度
    ORDER_FONTSIZE = 14

    AXISCOLOR = vg.nvgRGBf(0,0,0)
    GRIDCOLOR = vg.nvgRGBf(0.65,0.65,0.65)
    TEXTCOLOR = vg.nvgRGBf(0,0,0)

    SELBGCOLOR = vg.nvgRGBf(0,0.1,0.1)

class ThemosBlack:
    BGCOLOR = (0.0,0.0,0.0,1) #图表背景颜色

    MA60_COLOR = vg.nvgRGB(255,128,60) #ma60颜色
    PRICE_COLOR = vg.nvgRGB(70,130,200) #价格颜色
    MAIN_COLOR = vg.nvgRGB(255,0,255) #主力
    HUGE_COLOR = vg.nvgRGB(139,0,0)
    LARG_COLOR = vg.nvgRGB(255,128,0)
    MA5_COLOR = vg.nvgRGB(255,0,255)
    MA10_COLOR = vg.nvgRGB(240,248,136)
    MA20_COLOR = vg.nvgRGB(0,178,240)
    MA30_COLOR = vg.nvgRGB(0,128,255)
    MID_COLOR = vg.nvgRGB(255,215,0)
    TING_COLOR = vg.nvgRGB(135,206,250)
    RED_COLOR = vg.nvgRGB(250,0,0)  
    GREEN_COLOR = vg.nvgRGB(0,200,0) 
    RED_KCOLOR = vg.nvgRGB(250,0,0)  
    GREEN_KCOLOR = vg.nvgRGB(0,244,244)  
    BG_COLOR = vg.nvgRGB(0,0,0) #背景
    CROSS_COLOR = vg.nvgRGBAf(1,1,1,0.5)
    YLABELWIDTH = 42   #y轴坐标轴空间
    XLABELHEIGHT = 36  #x轴坐标轴空间

    ORDER_BGCOLOR = vg.nvgRGB(0,0,0)
    ORDER_HEADCOLOR = vg.nvgRGB(0,0,0)
    ORDER_SELCOLOR = vg.nvgRGB(32,96,168)
    ORDER_TEXTBGCOLOR = vg.nvgRGBA(0,0,0,255)
    ORDER_TEXTCOLOR = vg.nvgRGB(255,255,255) 
    ORDER_TEXTCOLOR2 = vg.nvgRGB(255,255,0) 
    ORDER_TEXTCOLOR3 = vg.nvgRGB(0,255,0)
    CAN_BUY_TEXTCOLOR = vg.nvgRGB(170,0,0)  #上轨和中轨向上
    CAN_BUY_TEXTCOLOR2 = vg.nvgRGB(70,0,140)  #都向上
    CAN_BUY_TEXTCOLOR3 = vg.nvgRGB(100,50,0)  #仅仅下轨向上

    WARN_BUY_COLOR = vg.nvgRGB(64,0,0)
    WARN_BUY_COLOR2 = vg.nvgRGB(128,0,0)
    WARN_NEWHIGH_COLOR = vg.nvgRGB(64,64,0)
    WARN_SELL_COLOR = vg.nvgRGB(0,64,0)
    WARN_SELL_COLOR2 = vg.nvgRGB(0,128,0)
    ORDER_WIDTH = 160       #排序栏宽度
    ORDER_ITEM_HEIGHT = 24  #排序栏按钮高度
    ORDER_FONTSIZE = 14

    AXISCOLOR = vg.nvgRGBf(0.9,0.9,0.9)
    GRIDCOLOR = vg.nvgRGBf(0.15,0.15,0.15)
    TEXTCOLOR = vg.nvgRGBf(1,1,1)

    SELBGCOLOR = vg.nvgRGBf(0,0,0.1)
