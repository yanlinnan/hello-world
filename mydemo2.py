# 根据main2.py的示例加注释并尝试添加自己需要的窗口
# 删除动画，尝试朴素实现（因为对动画完全不理解）
# 实现不了，无法展开,只实现了在窗口内置折叠窗口的功能
from PyQt5 import QtCore, QtGui, QtWidgets

class CollapsibleBox(QtWidgets.QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)

        # 创建Qtoolbutton用于实现折叠
        self.toggle_button = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        # 无边框
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        # 设置有图标和文字
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        # 图标箭头朝向右侧
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        # 绑定槽函数
        self.toggle_button.pressed.connect(self.on_pressed)
        # 并行动画容器类，除了可以播放动画外还可以动态调整多个控件的尺寸和位置
        self.toggle_animation = QtCore.QParallelAnimationGroup(self)
        # 创建滚动给区域容器，最小和最大高度设置为0，即不显示区域
        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )

        # 设置控件的尺寸调整策略，水平策略Expanding会尽可能水平拉伸以占据父容器的可用空间，垂直策略Fixed将控件的垂直高度固定为建议尺寸，不拉伸
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        # 不绘制滚动区域的边框
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        # 创建垂直布局，加入toolbutton和滚动区域
        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        # 添加动画
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight") # 调整当前窗口最小高度的动画
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight") # 调整当前窗口最大高度的动画
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight") # 调整滚动区域最大高度的动画
        )

    @QtCore.pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        # 按下时向下，没按下时向右
        self.toggle_button.setArrowType(
            QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        )
        # 按下时动画向前播放（显示），没按下时向后播放（隐藏）
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        # 播放动画
        self.toggle_animation.start()
        # if not checked:
        #     self.minimumHeight = self.collapsed_height + self.content_height
        #     self.maximumHeight = self.collapsed_height + self.content_height
        #     self.content_area.maximumHeight = self.content_height
        #     # 可以设置正确的值，但是并没有显示窗口，为什么不显示？？？？
        #     print(f'{self.minimumHeight=}')
        #     print(f'{self.maximumHeight=}')
        #     print(f'{self.content_area.maximumHeight=}')
        #     # QtWidgets.QApplication.processEvents()
        # else:
        #     self.minimumHeight = self.collapsed_height
        #     self.maximumHeight = self.collapsed_height
        #     self.content_area.maximumHeight = 0
        #     # QtWidgets.QApplication.processEvents()

    # 设置中心布局，外面创建好带窗口的布局后，添加进来
    def setContentLayout(self, layout):
        # 删除原本滚动区域容器的布局并设置为传入的布局
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)

        # 获取高度，使用当前窗口的高度减去滚动区域的最大高度，得到的是toolbutton的高度，和传入布局高度相加就是窗口展开时的高度
        # sizeHint() 得到控件建议的默认大小
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        # 获取传入的布局的高度
        content_height = layout.sizeHint().height()

        # self.collapsed_height = collapsed_height
        # self.content_height = content_height
        # print(f'{collapsed_height=}')
        # print(f'{content_height=}')
        for i in range(self.toggle_animation.animationCount()-1):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(100)                                  # 动画时间
            animation.setStartValue(collapsed_height)                   # 动画开始值
            animation.setEndValue(collapsed_height + content_height)    # 动画结束值，即从toolbutton到窗口完全展开的位置

        # 最后一个动画额外设置，从0到传入布局的结束位置
        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(100)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

class MyWidget(QtWidgets.QMainWindow):
    def __init__(self, parent = None,):
        super().__init__(parent)
        self.setCentralWidget(QtWidgets.QWidget())
        dock = QtWidgets.QDockWidget("停靠窗口")
        scroll = QtWidgets.QScrollArea()
        dock.setWidget(scroll)
        content = QtWidgets.QWidget()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        valy = QtWidgets.QVBoxLayout(content)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)

        self.CreateCameraWidget()
        self.CreateStageWidget()

        # 创建box，可以直接传递窗口的布局，不需要先创建布局，将窗口加入布局，再将布局传递
        camerabox = CollapsibleBox("相机属性")
        valy.addWidget(camerabox)
        # val1 = QtWidgets.QVBoxLayout()
        # val1.addWidget(self.CameraWidget)
        # camerabox.setContentLayout(val1)
        camerabox.setContentLayout(self.CameraLayout)

        stagebox = CollapsibleBox("位移台属性")
        valy.addWidget(stagebox)
        # val2 = QtWidgets.QVBoxLayout()
        # val2.addWidget(self.StageWidget)
        # stagebox.setContentLayout(val2)
        stagebox.setContentLayout(self.StageLayout)


        valy.addStretch()


    # 可以绑定槽函数
    def CreateCameraWidget(self):
        # w = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()#(w)
        label1 = QtWidgets.QLabel("曝光时间")
        edit1 = QtWidgets.QLineEdit("100")
        button1 = QtWidgets.QPushButton("设置")
        label2 = QtWidgets.QLabel("增益")
        edit2 = QtWidgets.QLineEdit("20")
        button2 = QtWidgets.QPushButton("设置")
        layout.addWidget(label1,0,0,1,1)
        layout.addWidget(edit1,0,1,1,1)
        layout.addWidget(button1,1,0,1,2)
        layout.addWidget(label2,2,0,1,1)
        layout.addWidget(edit2,2,1,1,1)
        layout.addWidget(button2,3,0,1,2)
        #self.CameraWidget = w
        self.CameraLayout = layout
    
    # 可以绑定槽函数
    def CreateStageWidget(self):
        # w = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()#(w)
        label1 = QtWidgets.QLabel("X位置")
        edit1 = QtWidgets.QLineEdit("100")
        button1 = QtWidgets.QPushButton("移动")
        label2 = QtWidgets.QLabel("Y位置")
        edit2 = QtWidgets.QLineEdit("100")
        button2 = QtWidgets.QPushButton("移动")
        layout.addWidget(label1,0,0,1,1)
        layout.addWidget(edit1,0,1,1,1)
        layout.addWidget(button1,1,0,1,2)
        layout.addWidget(label2,2,0,1,1)
        layout.addWidget(edit2,2,1,1,1)
        layout.addWidget(button2,3,0,1,2)
        #self.StageWidget = w
        self.StageLayout = layout
    

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = MyWidget()
    w.resize(640, 480)
    w.show()
    sys.exit(app.exec_())