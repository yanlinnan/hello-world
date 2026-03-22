"""
VTK 3D 模型创建工具
使用 PySide6 和 VTK 构建的交互式 3D 建模应用

功能:
    - 添加立方体和圆柱体
    - 重叠几何体自动半透明显示
    - 可调节全局透明度
    - 布尔挖空运算（移除重叠部分）
    - 3D 交互（旋转、平移、缩放）
"""

import sys
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QRadioButton, QSlider, QLabel, QGroupBox, QMessageBox,
    QButtonGroup, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPalette

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk import (
    vtkCubeSource, vtkCylinderSource, vtkActor, vtkPolyDataMapper,
    vtkProperty, vtkRenderer, vtkRenderWindow, vtkAxesActor,
    vtkOrientationMarkerWidget, vtkBooleanOperationPolyDataFilter,
    vtkTriangleFilter, vtkCleanPolyData, vtkMassProperties
)


class GeometryObject:
    """
    几何体对象类
    
    存储单个几何体的所有相关信息，包括 VTK 中的 actor、mapper、source 等。
    
    属性:
        name: 几何体的名称，用于标识
        actor: VTK 演员对象，负责在场景中渲染几何体
        mapper: VTK 映射器，将几何数据传递给 actor
        source: VTK 几何数据源，生成几何体的形状数据
        geometry_type: 几何体类型，'cube' 或 'cylinder'
        original_color: 原始颜色，用于重置时恢复
    """
    
    def __init__(self, name, actor, mapper, source, geometry_type):
        self.name = name                      # 对象名称
        self.actor = actor                    # VTK演员，控制几何体的渲染属性
        self.mapper = mapper                   # VTK映射器，将几何数据传输到GPU
        self.source = source                  # VTK数据源，存储几何体的顶点数据
        self.geometry_type = geometry_type    # 几何体类型：'cube' 或 'cylinder'
        self.original_color = actor.GetProperty().GetColor()  # 保存初始颜色


class ModelManager:
    """
    模型管理器类
    
    负责管理场景中所有的几何体对象，提供添加、删除、重叠检测和布尔运算等功能。
    
    属性:
        renderer: VTK 渲染器，用于管理场景中的所有 actor
        objects: 存储所有几何体对象的列表
        counter: 计数器，记录已创建的立方体和圆柱体数量
    """
    
    def __init__(self, renderer):
        self.renderer = renderer        # VTK渲染器，管理场景中的所有几何体
        self.objects = []               # 存储所有几何体对象的列表
        self.counter = {'cube': 0, 'cylinder': 0}  # 用于生成唯一命名的计数器
    
    def add_cube(self, center=(0, 0, 0)):
        """
        添加立方体到场景中
        
        创建一个 1x1x1 的立方体，设置其位置为指定中心点。
        立方体颜色为粉红色 (RGB: 0.91, 0.12, 0.39)
        
        参数:
            center: 立方体中心点的坐标元组 (x, y, z)
        
        返回:
            GeometryObject: 创建的几何体对象
        """
        self.counter['cube'] += 1                                    # 立方体计数加1
        name = f"Cube_{self.counter['cube']}"                        # 生成唯一名称
        
        # ========== 创建立方体数据源 ==========
        # vtkCubeSource 是生成立方体网格数据的类
        source = vtkCubeSource()
        source.SetCenter(*center)           # 设置立方体中心点坐标
        source.SetXLength(1.0)             # 设置X方向边长为1
        source.SetYLength(1.0)             # 设置Y方向边长为1
        source.SetZLength(1.0)             # 设置Z方向边长为1
        source.Update()                     # 执行数据生成，更新输出数据
        
        # ========== 创建映射器 ==========
        # vtkPolyDataMapper 将几何数据（多边形网格）映射到图形硬件
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())  # 连接数据源的输出端口
        
        # ========== 创建渲染演员 ==========
        # vtkActor 代表场景中的一个可渲染对象
        actor = vtkActor()
        actor.SetMapper(mapper)                              # 将映射器关联到演员
        actor.GetProperty().SetColor(0.91, 0.12, 0.39)    # 设置漫反射颜色（粉红色）
        actor.SetPosition(*center)                           # 设置世界坐标系中的位置
        
        # ========== 添加到渲染器 ==========
        self.renderer.AddActor(actor)      # 将演员添加到渲染器，渲染器会负责绘制它
        
        # ========== 创建几何体对象并存储 ==========
        obj = GeometryObject(name, actor, mapper, source, 'cube')
        self.objects.append(obj)           # 添加到对象列表中管理
        return obj
    
    def add_cylinder(self, center=(0, 0, 0)):
        """
        添加圆柱体到场景中
        
        创建一个半径 0.5、高度 1 的圆柱体，设置其位置为指定中心点。
        圆柱体颜色为紫色 (RGB: 0.61, 0.15, 0.69)
        
        参数:
            center: 圆柱体中心点的坐标元组 (x, y, z)
        
        返回:
            GeometryObject: 创建的几何体对象
        """
        self.counter['cylinder'] += 1                              # 圆柱体计数加1
        name = f"Cylinder_{self.counter['cylinder']}"              # 生成唯一名称
        
        # ========== 创建圆柱体数据源 ==========
        # vtkCylinderSource 生成圆柱形网格数据
        source = vtkCylinderSource()
        source.SetCenter(center[0], center[1] + 0.5, center[2])   # 设置中心点（Y轴偏移0.5使底部对齐）
        source.SetRadius(0.5)             # 设置圆柱体半径为0.5
        source.SetHeight(1.0)             # 设置圆柱体高度为1
        source.SetResolution(32)           # 设置圆周分段数（精度），32段足够平滑
        source.Update()                     # 执行数据生成
        
        # ========== 创建映射器 ==========
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        
        # ========== 创建渲染演员 ==========
        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.61, 0.15, 0.69)    # 设置漫反射颜色（紫色）
        actor.SetPosition(0, 0, 0)                        # 注意：圆柱体位置由source控制
        actor.SetOrigin(center[0], center[1] + 0.5, center[2])  # 设置旋转中心
        
        # ========== 添加到渲染器 ==========
        self.renderer.AddActor(actor)
        
        # ========== 创建几何体对象并存储 ==========
        obj = GeometryObject(name, actor, mapper, source, 'cylinder')
        self.objects.append(obj)
        return obj
    
    def check_overlap(self, obj1, obj2):
        """
        检查两个几何体是否重叠
        
        通过比较两个几何体的包围盒（Bounding Box）来判断是否存在重叠区域。
        包围盒是一个完全包含几何体的轴对齐矩形盒子。
        
        参数:
            obj1: 第一个几何体对象
            obj2: 第二个几何体对象
        
        返回:
            bool: 如果两个几何体重叠返回 True，否则返回 False
        """
        bounds1 = obj1.actor.GetBounds()  # 获取第一个几何体的包围盒
        bounds2 = obj2.actor.GetBounds()  # 获取第二个几何体的包围盒
        # bounds 返回 [xmin, xmax, ymin, ymax, zmin, zmax]
        
        # 检测两个包围盒是否在X、Y、Z三个轴上都不相交
        # 如果在某个轴上不相交，则两个几何体不重叠
        # 使用德摩根定律判断不相交：左边 > 右边界 或 右边 < 左边界
        overlap = not (bounds1[0] > bounds2[1] or  # X轴：obj1左 > obj2右
                       bounds1[1] < bounds2[0] or  # X轴：obj1右 < obj2左
                       bounds1[2] > bounds2[3] or  # Y轴：obj1下 > obj2上
                       bounds1[3] < bounds2[2] or  # Y轴：obj1上 < obj2下
                       bounds1[4] > bounds2[5] or  # Z轴：obj1前 > obj2后
                       bounds1[5] < bounds2[4])    # Z轴：obj1后 < obj2前
        return overlap
    
    def set_transparency(self, transparency):
        """
        设置所有几何体的透明度
        
        透明度的值会被转换为不透明度（opacity = 1 - transparency）后应用到所有几何体。
        
        参数:
            transparency: 透明度值，范围 0.0 到 1.0
        """
        opacity = 1.0 - transparency       # 转换为不透明度（0=完全透明，1=完全不透明）
        for obj in self.objects:           # 遍历所有几何体
            obj.actor.GetProperty().SetOpacity(opacity)  # 设置不透明度
    
    def carve_overlaps(self):
        """
        对所有重叠的几何体执行挖空操作
        
        遍历场景中所有的几何体对，检测重叠区域并执行布尔差集运算。
        运算完成后将所有几何体恢复为完全不透明。
        
        返回:
            bool: 如果操作成功返回 True，否则返回 False
        """
        # 至少需要两个几何体才能进行布尔运算
        if len(self.objects) < 2:
            return False
        
        modified = True                    # 标记是否有几何体被修改
        iterations = 0                     # 迭代计数器
        # 最多需要 n*(n-1)/2 次迭代（每对几何体最多处理一次）
        max_iterations = len(self.objects) * (len(self.objects) - 1) // 2
        
        # 使用迭代方式处理多次重叠的情况
        # 当有新几何体被创建时，可能产生新的重叠对，需要重新检查
        while modified and iterations < max_iterations:
            modified = False               # 假设本次迭代不做任何修改
            iterations += 1
            i = 0
            while i < len(self.objects):
                j = i + 1                  # 从 i 之后开始配对，避免重复检查
                while j < len(self.objects):
                    obj1 = self.objects[i]
                    obj2 = self.objects[j]
                    
                    # 检查这对几何体是否重叠
                    if self.check_overlap(obj1, obj2):
                        # 执行两个几何体的挖空操作
                        if self._carve_two_objects(obj1, obj2):
                            # 如果成功，列表长度会减小
                            if len(self.objects) <= 2:
                                return True  # 只剩2个或更少时直接返回
                            modified = True  # 标记需要重新检查
                            i = -1           # 重置索引，从头开始重新遍历
                            break
                    j += 1
                i += 1
        
        # 挖空完成后，将所有几何体恢复为完全不透明
        for obj in self.objects:
            obj.actor.GetProperty().SetOpacity(1.0)
        
        return True
    
    def _carve_two_objects(self, obj1, obj2):
        """
        对两个几何体执行布尔差集运算
        
        使用 VTK 的布尔运算过滤器，从 obj1 中减去 obj2 的重叠部分。
        运算后 obj1 被挖空，obj2 被移除。
        
        参数:
            obj1: 被挖空的几何体（重叠部分会被移除）
            obj2: 挖空用的几何体（运算后会被删除）
        
        返回:
            bool: 如果运算成功返回 True，否则返回 False
        """
        try:
            # ========== 获取两个几何体的多边形数据 ==========
            poly1 = self._get_polydata(obj1)
            poly2 = self._get_polydata(obj2)
            
            # 检查数据是否有效
            if poly1.GetNumberOfPoints() == 0 or poly2.GetNumberOfPoints() == 0:
                return False
            
            # ========== 执行布尔差集运算 ==========
            # vtkBooleanOperationPolyDataFilter 执行多边形网格的布尔运算
            bool_filter = vtkBooleanOperationPolyDataFilter()
            bool_filter.SetOperationToDifference()  # 设置为差集运算（A - B）
            bool_filter.SetInputData(0, poly1)       # 设置第一个输入（被减的几何体）
            bool_filter.SetInputData(1, poly2)       # 设置第二个输入（减去的几何体）
            bool_filter.Update()                     # 执行布尔运算
            
            # 检查运算结果是否为空
            if bool_filter.GetOutput().GetNumberOfPoints() == 0:
                return False
            
            # ========== 三角网格化 ==========
            # 布尔运算的输出可能不是标准三角形网格，需要转换
            tri = vtkTriangleFilter()
            tri.SetInputConnection(bool_filter.GetOutputPort())  # 接收布尔运算结果
            tri.Update()                     # 执行三角化
            
            # ========== 清理重复顶点 ==========
            # 三角化可能产生重复的顶点和单元，需要清理
            clean = vtkCleanPolyData()
            clean.SetInputConnection(tri.GetOutputPort())  # 接收三角化后的数据
            clean.Update()                     # 执行清理（合并距离很近的顶点）
            
            # 再次检查结果是否为空
            if clean.GetOutput().GetNumberOfPoints() == 0:
                return False
            
            # ========== 更新几何体 ==========
            new_mapper = vtkPolyDataMapper()
            new_mapper.SetInputConnection(clean.GetOutputPort())
            
            # 更新 obj1 的映射器和数据源
            obj1.actor.SetMapper(new_mapper)  # 关联新的映射器
            obj1.mapper = new_mapper           # 更新对象引用
            obj1.source = clean.GetOutput()    # 保存新的几何数据
            
            # ========== 移除 obj2 ==========
            self.renderer.RemoveActor(obj2.actor)  # 从渲染器移除
            self.objects.remove(obj2)               # 从列表移除
            
            return True
        except Exception as e:
            print(f"Boolean operation error: {e}")
            return False
    
    def _get_polydata(self, obj):
        """
        获取几何体的多边形数据
        
        将几何体数据转换为可进行布尔运算的 vtkPolyData 格式。
        布尔运算需要输入多边形数据（点+单元的集合）。
        
        参数:
            obj: 几何体对象
        
        返回:
            vtkPolyData: 转换后的多边形数据
        """
        # 检查对象是否有 GetOutputPort 方法（有则说明是数据源）
        if hasattr(obj.source, 'GetOutputPort'):
            output = obj.source.GetOutput()
            # 如果输出已经是 vtkPolyData 类型，进行三角化处理
            if output.IsA('vtkPolyData'):
                tri = vtkTriangleFilter()
                tri.SetInputConnection(obj.source.GetOutputPort())
                tri.Update()
                return tri.GetOutput()
            return output
        # 如果已经是多边形数据，直接返回
        return obj.source
    
    def clear_all(self):
        """
        清空场景中的所有几何体
        
        移除所有几何体并重置计数器。
        """
        # 遍历所有几何体，从渲染器中移除
        for obj in self.objects:
            self.renderer.RemoveActor(obj.actor)
        
        self.objects.clear()               # 清空对象列表
        self.counter = {'cube': 0, 'cylinder': 0}  # 重置计数器
    
    def get_object_count(self):
        """
        获取当前几何体数量
        
        返回:
            int: 场景中几何体的数量
        """
        return len(self.objects)
    
    def has_overlapping_pairs(self):
        """
        检查是否存在重叠的几何体对
        
        遍历所有几何体对，检查是否有任何一对存在重叠。
        
        返回:
            bool: 如果存在重叠对返回 True，否则返回 False
        """
        # 双重循环检查所有几何体对
        for i in range(len(self.objects)):
            for j in range(i + 1, len(self.objects)):  # j 从 i+1 开始，避免重复
                if self.check_overlap(self.objects[i], self.objects[j]):
                    return True
        return False


class VTKWidget(QWidget):
    """
    VTK 3D 视图控件
    
    集成 VTK 渲染窗口的 Qt 控件，提供 3D 场景的显示和交互功能。
    
    继承自 QWidget，可以像普通 Qt 控件一样添加到布局中。
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_vtk()
    
    def _init_vtk(self):
        """
        初始化 VTK 渲染环境和交互器
        
        设置渲染器、渲染窗口、交互器、坐标轴等组件。
        """
        # ========== 创建渲染器 ==========
        # vtkRenderer 负责管理场景中的所有对象，控制光照、相机等
        self.renderer = vtkRenderer()
        self.renderer.SetBackground(0.17, 0.17, 0.17)  # 设置背景色为深灰色
        
        # ========== 创建 VTK-Qt 集成窗口 ==========
        # QVTKRenderWindowInteractor 是 VTK 与 Qt 的桥梁
        # 允许在 Qt 控件中嵌入 VTK 渲染窗口
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        
        # 获取 VTK 渲染窗口
        self.render_window = self.vtk_widget.GetRenderWindow()
        self.render_window.SetWindowName("VTK 3D Modeler")  # 设置窗口标题
        self.render_window.SetSize(800, 600)                # 设置默认大小
        self.render_window.AddRenderer(self.renderer)       # 将渲染器关联到窗口
        
        # ========== 设置交互风格 ==========
        # vtkInteractorStyleTrackballCamera 允许用鼠标操作相机（旋转、缩放、平移）
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.vtk_widget.SetInteractorStyle(style)
        
        # ========== 创建模型管理器 ==========
        # ModelManager 负责管理场景中的几何体对象
        self.model_manager = ModelManager(self.renderer)
        
        # ========== 创建坐标轴指示器 ==========
        # vtkAxesActor 在原点显示 XYZ 坐标轴，帮助用户理解方向
        self.axes = vtkAxesActor()
        self.axes.SetTotalLength(2, 2, 2)       # 设置轴的长度为2个单位
        self.axes.SetShaftTypeToCylinder()      # 使用圆柱体作为轴杆
        self.axes.SetXAxisLabelText("X")        # X轴标签
        self.axes.SetYAxisLabelText("Y")        # Y轴标签
        self.axes.SetZAxisLabelText("Z")        # Z轴标签
        self.axes.SetCylinderRadius(0.02)       # 设置轴的半径
        
        # ========== 创建坐标轴小部件 ==========
        # vtkOrientationMarkerWidget 在视口角落显示坐标轴
        self.orientation_widget = vtkOrientationMarkerWidget()
        self.orientation_widget.SetOrientationMarker(self.axes)  # 关联坐标轴
        self.orientation_widget.SetInteractor(self.vtk_widget)   # 关联交互器
        self.orientation_widget.SetViewport(0.0, 0.0, 0.2, 0.2) # 设置显示区域（左下角20%）
        self.orientation_widget.SetEnabled(1)    # 启用小部件
        self.orientation_widget.On()            # 显示小部件
        
        # ========== 设置布局 ==========
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)   # 移除布局边距
        layout.addWidget(self.vtk_widget)        # 将 VTK 控件添加到布局
        
        # ========== 初始化交互 ==========
        self.vtk_widget.Initialize()             # 初始化交互器
        self.vtk_widget.Start()                 # 启动交互循环
        self.render_window.Render()             # 触发首次渲染
    
    def add_cube(self):
        """
        添加立方体到场景
        
        计算偏移位置添加立方体，并检测与现有几何体的重叠。
        如果有重叠，相关几何体会自动设置为半透明。
        
        返回:
            GeometryObject: 创建的立方体对象
        """
        # 计算偏移位置：每个新几何体偏移0.3单位，增加重叠的可能性
        offset = self.model_manager.get_object_count() * 0.3
        new_obj = self.model_manager.add_cube(center=(offset, 0, offset))
        
        # ========== 检测重叠并设置半透明 ==========
        for obj in self.model_manager.objects:
            # 排除自身，并检测是否与新立方体重叠
            if obj != new_obj and self.model_manager.check_overlap(obj, new_obj):
                new_obj.actor.GetProperty().SetOpacity(0.5)  # 新几何体50%透明
                obj.actor.GetProperty().SetOpacity(0.5)      # 被重叠的也50%透明
        
        self.render_window.Render()             # 刷新渲染
        return new_obj
    
    def add_cylinder(self):
        """
        添加圆柱体到场景
        
        计算偏移位置添加圆柱体，并检测与现有几何体的重叠。
        如果有重叠，相关几何体会自动设置为半透明。
        
        返回:
            GeometryObject: 创建的圆柱体对象
        """
        offset = self.model_manager.get_object_count() * 0.3
        new_obj = self.model_manager.add_cylinder(center=(offset, 0, offset))
        
        # 检测重叠并设置半透明
        for obj in self.model_manager.objects:
            if obj != new_obj and self.model_manager.check_overlap(obj, new_obj):
                new_obj.actor.GetProperty().SetOpacity(0.5)
                obj.actor.GetProperty().SetOpacity(0.5)
        
        self.render_window.Render()
        return new_obj
    
    def set_transparency(self, value):
        """
        设置所有几何体的透明度
        
        参数:
            value: 透明度百分比 (0-100)
        """
        # 将百分比转换为小数（0.0 到 1.0）
        self.model_manager.set_transparency(value / 100.0)
        self.render_window.Render()
    
    def carve_overlaps(self):
        """
        执行挖空操作
        
        对场景中所有重叠的几何体执行布尔差集运算。
        
        返回:
            bool: 操作是否成功
        """
        if self.model_manager.carve_overlaps():
            self.render_window.Render()
            return True
        return False
    
    def clear_all(self):
        """
        清空所有几何体
        """
        self.model_manager.clear_all()
        self.render_window.Render()
    
    def can_carve(self):
        """
        检查是否可以执行挖空操作
        
        返回:
            bool: 如果至少有两个几何体返回 True
        """
        return self.model_manager.get_object_count() >= 2


class MainWindow(QMainWindow):
    """
    主窗口类
    
    应用程序的主窗口，包含 3D 视图区域和右侧控制面板。
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VTK 3D Modeler")
        self.setMinimumSize(1000, 700)           # 设置最小窗口大小
        
        # ========== 创建中央控件 ==========
        central_widget = QWidget()
        self.setCentralWidget(central_widget)     # 设置中央控件
        
        # ========== 创建主布局 ==========
        # 水平布局：左侧3D视图 + 右侧控制面板
        main_layout = QHBoxLayout(central_widget)
        
        # 创建并添加 VTK 3D 视图控件（占据主要空间，stretch factor=1）
        self.vtk_widget = VTKWidget()
        main_layout.addWidget(self.vtk_widget, 1)
        
        # 创建并添加控制面板
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
    
    def _create_control_panel(self):
        """
        创建右侧控制面板
        
        包含几何体选择、透明度调节、布尔运算和清空操作等控件。
        
        返回:
            QWidget: 创建的面板控件
        """
        panel = QWidget()
        panel.setFixedWidth(250)                  # 固定面板宽度为250像素
        
        # ========== 设置样式表（CSS） ==========
        panel.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;        /* 浅灰色背景 */
            }
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #CCCCCC;        /* 灰色边框 */
                border-radius: 6px;               /* 圆角 */
                margin-top: 12px;                 /* 标题与边框的间距 */
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            /* 主按钮样式（蓝色） */
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;         /* 悬停时颜色加深 */
            }
            QPushButton:pressed {
                background-color: #1565C0;        /* 按下时颜色更深 */
            }
            QPushButton:disabled {
                background-color: #BDBDBD;        /* 禁用状态灰色 */
            }
            /* 清空按钮样式（灰色） */
            QPushButton#clearBtn {
                background-color: #757575;
            }
            QPushButton#clearBtn:hover {
                background-color: #616161;
            }
            /* 滑块样式 */
            QSlider::groove:horizontal {
                border: 1px solid #CCCCCC;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #2196F3;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            /* 单选按钮样式 */
            QRadioButton {
                font-size: 12px;
                padding: 4px;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
            }
        """)
        
        # ========== 创建垂直布局 ==========
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)  # 设置内边距
        layout.setSpacing(8)                       # 设置组件间距
        
        # ========== 标题 ==========
        title = QLabel("几何体")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #212121;")
        layout.addWidget(title)
        
        # ========== 几何体选择组 ==========
        geometry_group = QGroupBox("选择几何体")
        geometry_layout = QVBoxLayout(geometry_group)
        
        # 立方体单选按钮（默认选中）
        self.cube_radio = QRadioButton("立方体")
        self.cube_radio.setChecked(True)
        geometry_layout.addWidget(self.cube_radio)
        
        # 圆柱体单选按钮
        self.cylinder_radio = QRadioButton("圆柱体")
        geometry_layout.addWidget(self.cylinder_radio)
        
        layout.addWidget(geometry_group)
        
        # ========== 添加按钮 ==========
        self.add_button = QPushButton("添加几何体")
        self.add_button.clicked.connect(self._on_add_geometry)  # 连接点击信号
        layout.addWidget(self.add_button)
        
        # ========== 透明度设置组 ==========
        transparency_group = QGroupBox("透明度设置")
        transparency_layout = QVBoxLayout(transparency_group)
        
        # 创建水平滑块
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setMinimum(0)      # 最小值0
        self.transparency_slider.setMaximum(100)     # 最大值100
        self.transparency_slider.setValue(0)        # 默认值0（不透明）
        self.transparency_slider.setTickPosition(QSlider.TicksBelow)  # 显示刻度线
        self.transparency_slider.setTickInterval(25)  # 每25显示一个刻度
        # 滑块值变化时触发回调
        self.transparency_slider.valueChanged.connect(self._on_transparency_changed)
        
        transparency_layout.addWidget(self.transparency_slider)
        
        # 透明度标签
        self.transparency_label = QLabel("透明度: 0%")
        self.transparency_label.setAlignment(Qt.AlignCenter)  # 居中对齐
        transparency_layout.addWidget(self.transparency_label)
        
        layout.addWidget(transparency_group)
        
        # ========== 布尔运算组 ==========
        boolean_group = QGroupBox("布尔运算")
        boolean_layout = QVBoxLayout(boolean_group)
        
        self.carve_button = QPushButton("挖空重叠部分")
        self.carve_button.clicked.connect(self._on_carve)  # 连接点击信号
        boolean_layout.addWidget(self.carve_button)
        
        layout.addWidget(boolean_group)
        
        layout.addStretch()  # 添加弹性空间，把上面的控件往上推
        
        # ========== 操作组 ==========
        operations_group = QGroupBox("操作")
        operations_layout = QVBoxLayout(operations_group)
        
        clear_button = QPushButton("清空场景")
        clear_button.setObjectName("clearBtn")       # 设置对象名，用于CSS选择器
        clear_button.clicked.connect(self._on_clear)  # 连接点击信号
        operations_layout.addWidget(clear_button)
        
        layout.addWidget(operations_group)
        
        return panel
    
    def _on_add_geometry(self):
        """
        添加几何体按钮的响应函数
        
        根据当前选择的类型（立方体或圆柱体）添加相应的几何体。
        """
        if self.cube_radio.isChecked():
            self.vtk_widget.add_cube()
        else:
            self.vtk_widget.add_cylinder()
    
    def _on_transparency_changed(self, value):
        """
        透明度滑块变化时的响应函数
        
        更新透明度标签并设置几何体的透明度。
        
        参数:
            value: 滑块的当前值 (0-100)
        """
        self.transparency_label.setText(f"透明度: {value}%")  # 更新标签文字
        self.vtk_widget.set_transparency(value)               # 调用VTK控件设置透明度
    
    def _on_carve(self):
        """
        挖空按钮的响应函数
        
        执行布尔挖空运算，移除重叠区域。
        """
        # 检查是否有足够的几何体
        if not self.vtk_widget.can_carve():
            QMessageBox.warning(self, "警告", "场景中需要至少两个几何体才能进行挖空操作。")
            return
        
        # 执行挖空操作
        if self.vtk_widget.carve_overlaps():
            QMessageBox.information(self, "成功", "挖空操作完成！")
        else:
            QMessageBox.warning(self, "操作失败", "无法完成布尔运算，请确保几何体有重叠区域。")
    
    def _on_clear(self):
        """
        清空按钮的响应函数
        
        清空所有几何体并重置透明度滑块。
        """
        # 弹出确认对话框
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有几何体吗？",
            QMessageBox.Yes | QMessageBox.No  # 提供是/否两个选项
        )
        if reply == QMessageBox.Yes:           # 用户点击"是"
            self.vtk_widget.clear_all()        # 清空场景
            self.transparency_slider.setValue(0)  # 重置透明度滑块


def main():
    """
    程序入口函数
    
    创建应用程序实例和主窗口，启动事件循环。
    """
    # ========== 创建 Qt 应用程序 ==========
    # QApplication 管理应用程序的所有资源和主事件循环
    app = QApplication(sys.argv)
    app.setApplicationName("VTK 3D Modeler")
    
    # ========== 创建和显示主窗口 ==========
    window = MainWindow()
    window.show()
    
    # ========== 启动事件循环 ==========
    # app.exec() 启动 Qt 的事件循环，程序在这里进入等待状态
    # sys.exit() 确保程序退出时返回正确的退出码
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
