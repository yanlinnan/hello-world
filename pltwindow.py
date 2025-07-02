# 绘制窗口测试，绘图时在子图上新建qt画布，使用qt实施绘图，绘图结束后再使用matplotlib绘图
import sys
import cv2
from PySide6.QtWidgets import QWidget, QApplication,QVBoxLayout,QFileDialog
from PySide6.QtGui import QAction,QPainter, QPen, QColor
from PySide6.QtCore import Qt, QPoint
from matplotlib.figure import Figure
from matplotlib import patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []  # 存储点击的点
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # 允许鼠标事件穿透
        self.startpoint = None
        self.endpoint = None
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing) # 抗锯齿
        pen = QPen(QColor(255, 0, 0), 3)  # 红色，5像素大小的点
        painter.setPen(pen)
        
        # for point in self.points:
        #     painter.drawPoint(point)
        if self.endpoint is not None:
            painter.drawLine(self.startpoint, self.endpoint)
    
    def add_point(self, point):
        self.points.append(point)
        self.update()

    def set_start_point(self, point):
        self.startpoint = point

    def set_end_point(self, point):
        self.endpoint = point
        self.update()

    def deleteALL(self):
        self.startpoint = None
        self.endpoint = None
        self.update()


class PltWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initui()
        self.initevent()

        self.startdraw = False
        self.startpoint = []
        self.endpoint = []

    def initui(self):
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas)
        self.open_action = QAction('open')
        self.toolbar.addAction(self.open_action)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.fig.clear()
        self.ax_exist = False

        # 创建覆盖层用于绘制图形
        self.overlay = OverlayWidget(self.canvas)
        self.overlay.setGeometry(self.canvas.rect())

    def initevent(self):
        self.fig.canvas.mpl_connect('button_press_event', self.on_left_press_clicked)
        self.fig.canvas.mpl_connect('button_release_event', self.on_left_release_clicked)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_move)
        self.open_action.triggered.connect(self.open)
        self.fig.canvas.mpl_connect('key_release_event',self.on_key_release_clicked)
        self.canvas.resizeEvent = self.on_canvas_resize

    def open(self):
        path, _ = QFileDialog.getOpenFileName()
        if path:
            print(path)
            image = cv2.imread(path,cv2.IMREAD_GRAYSCALE)
            self.axes = self.fig.add_subplot(1,1,1)
            self.axes.imshow(image)
            self.canvas.draw_idle()
            # self.overlay.setGeometry()

    def on_canvas_resize(self, event):
        self.overlay.setGeometry(self.canvas.rect())
        super(FigureCanvas, self.canvas).resizeEvent(event)

    def on_left_press_clicked(self,event):
        if event.inaxes != self.axes:
            return
        self.startdraw = True
        x_data = event.xdata
        y_data = event.ydata
        self.startpoint = [x_data, y_data]
        x_pixel,y_pixel = self.dataxy_to_pixelxy(x_data, y_data)
        self.overlay.set_start_point(QPoint(int(x_pixel), int(y_pixel)))

    def on_left_release_clicked(self, event):
        if event.inaxes != self.axes:
            return
        self.startdraw = False
        x_data = event.xdata
        y_data = event.ydata
        self.endpoint = [x_data, y_data]
        # rect = patches.Rectangle(self.startpoint, abs(self.endpoint[0]-self.startpoint[0]), abs(self.endpoint[1]-self.startpoint[1]))
        # self.axes.add_patch(rect)
        self.axes.plot([self.startpoint[0],x_data], [self.startpoint[1],y_data],linewidth=2,color='r')
        self.canvas.draw()
        self.overlay.deleteALL()


    def on_move(self, event):
        if self.startdraw == False:
            return        
        if event.inaxes != self.axes:
            return

        # 获取坐标
        x_data = event.xdata
        y_data = event.ydata
        x_pixel = event.x
        y_pixel = event.y
        print(f'({x_data=},{y_data}), ({x_pixel=},{y_pixel=})')

        x_pixel,y_pixel = self.dataxy_to_pixelxy(x_data, y_data)
        # self.overlay.add_point(QPoint(int(x_pixel), int(y_pixel)))
        self.overlay.set_end_point(QPoint(int(x_pixel), int(y_pixel)))

    def dataxy_to_pixelxy(self,x,y):
        # 将数据坐标转换为画布坐标 (0-1 范围内的相对坐标)
        bbox = self.axes.get_position()
        x_canvas = bbox.x0 + (x - self.axes.get_xlim()[0]) / (self.axes.get_xlim()[1] - self.axes.get_xlim()[0]) * bbox.width
        y_canvas = bbox.y0 + (y - self.axes.get_ylim()[0]) / (self.axes.get_ylim()[1] - self.axes.get_ylim()[0]) * bbox.height
        # 将画布坐标转换为像素坐标
        x_pixel = int(x_canvas * self.canvas.width())
        y_pixel = int((1 - y_canvas) * self.canvas.height())  # Qt的Y轴是从上到下的    
        return x_pixel,y_pixel    

    def on_key_release_clicked(self, event):
        1

if __name__ == '__main__':
    app = QApplication([])
    w = PltWindow()
    w.show()
    sys.exit(app.exec())