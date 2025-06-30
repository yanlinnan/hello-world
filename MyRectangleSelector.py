from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


class MyRectangleSelector:
    def __init__(self, ax, on_release_back):
        self.ax = ax
        self.on_release = on_release_back

        self.rect_list = []
        self.rect_xy_list = []
        self.rect_status_list = []
        self.recting = False
        self.draw_or_move = True # true表示绘制新矩形 false表示修改旧矩形
        self.rect_index = -1

        self.create_selector()

        self.ax.figure.canvas.mpl_connect('button_press_event', self.on_left_press_clicked)

    def create_selector(self):
        rect_selector = RectangleSelector(
            self.ax, self.on_select,
            useblit=True,                   # 是否使用blitting提高性能
            button=[1],                     # 1:左键，2:中键，3:右键
            minspanx=5, minspany=5,
            spancoords='pixels',            # 'pixels':以像素作为最小单位 ,'data':以坐标作为最小单位
            interactive=True,                # 选择后是否可以拖动调整矩形
            # 矩形样式
            props=dict(edgecolor='red',alpha=0,fill=False,linewidth=2),
        )
        self.rect_selector = rect_selector
        self.recting = True

    def enable_selector(self, enable):
        self.recting = enable
        self.rect_selector.set_active(enable)

    def on_select(self,eclick,erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        # print(x1,y1,x2,y2)
        rect = patches.Rectangle((min(x1,x2), min(y1,y2)), abs(x1-x2), abs(y1-y2),
                                 linewidth = 2,
                                 edgecolor = 'r',
                                 fill = False,
                                 alpha = 1,
                                 linestyle = '-')
        # if self.draw_or_move:
        print("绘制",x1,x2,y1,y2)
        self.ax.add_patch(rect)
        self.ax.figure.canvas.draw()
        self.rect_xy_list.append([x1,x2,y1,y2])
        self.rect_list.append(rect)
        self.set_false_status()
        self.rect_status_list.append(True)
        # else:
        #     i = self.rect_index
        #     self.rect_xy_list[i] = [x1,x2,y1,y2]
        #     print(f'移除第{i}个矩形')
        #     self.rect_list[i].remove()
        #     self.rect_list[i] = rect

    def set_false_status(self):
        for i in range(len(self.rect_status_list)):
            self.rect_status_list[i] = False

    def on_left_press_clicked(self,event):
        # pass
        if self.recting and event.inaxes and event.button == 1:
            x = event.xdata
            y = event.ydata
            for i in range(len(self.rect_xy_list)):
                if len(self.rect_xy_list[i]) > 0 and self.xy_in_rect(x,y,self.rect_xy_list[i]):
                    x1,x2,y1,y2 = self.rect_xy_list[i]
                    self.rect_selector.extents = [x1,x2,y1,y2]

                    # self.rect_list[i].remove() 选中不能删，不然就没了
                    # 选中之后如果拖动则会二次选中
                    print('删除',self.rect_xy_list[i])
                    self.rect_xy_list[i] = []
                    self.rect_list[i].remove()
                    self.rect_list[i] = None
                    self.ax.figure.canvas.draw()
                    return


    def xy_in_rect(self,x,y,rect):
        xmin,xmax,ymin,ymax = rect
        
        image_width = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
        fig = self.ax.figure
        # bbox = self.ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        # width1, height1 = bbox.width * fig.dpi, bbox.height * fig.dpi
        # print(width1,height1)
        # # 矩形线宽是2，所以小矩形的宽高应该是6，对应图像的像素数目是 6 * image_width / width1
        # o = 3 * image_width / width1
        # print('o',o) # 这个计算方法不对，算出来太小了

        bbox = self.ax.get_tightbbox(fig.canvas.get_renderer())
        width2 = bbox.width * fig.dpi / 72
        height2 = bbox.height * fig.dpi / 72
        print(width2,height2)

        # 方法三
        pos = self.ax.get_position()
        fig_size = fig.get_size_inches()
        width3 = pos.width * fig_size[0] * fig.dpi
        height3 = pos.height * fig_size[1] * fig.dpi
        print(width3,height3)

        # rectselector只判断9个点，如果在这个函数里判断整个边界会导致选中9个点之外的点时重新绘制矩形
        o = 3 # 允许偏移误差,应该根据图像缩放比例确定，否则会有比较大的误差
        xmid = (xmax + xmin) / 2
        ymid = (ymax + ymin) / 2
        for xx in [xmin,xmid,xmax]:
            for yy in [ymin,ymid,ymax]:
                if abs(x - xx) < o and abs(y - yy) < o:
                    # print('选中',x,y,[xmin,xmid,xmax],[ymin,ymid,ymax])
                    return True
        # print('非选中',x,y,[xmin,xmid,xmax],[ymin,ymid,ymax])
        return False


if __name__ == '__main__':
    figure = plt.figure()
    ax = figure.add_subplot(1,1,1)

    ax.imshow(np.random.rand(100,100))

    def on_back(start,end):
        print(start,end)
    selector = MyRectangleSelector(ax,on_back)

    plt.show()