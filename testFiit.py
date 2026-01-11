import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math 

# ========== 解决中文字体乱码核心配置 ==========
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认中文字体：黑体（SimHei）
plt.rcParams['axes.unicode_minus'] = False    # 关闭负号的默认渲染，避免负号显示为方框

# 设置绘图风格，保证图像清晰
plt.rcParams['figure.figsize'] = (16, 12)
plt.rcParams['font.size'] = 10

def generate_tilted_bowl_data(num_points=500):
    """
    生成沿着y轴倾斜的碗形曲面数据
    :param num_points: 数据点数量
    :return: 碗形数据点 (n, 3)，格式为 [x, y, z]
    """
    # # 1. 生成基础旋转抛物面数据（碗形）
    # theta = np.random.uniform(0, 2*np.pi, num_points)  # 方位角
    # r = np.random.uniform(0, 2, num_points)            # 半径
    # x = r * np.cos(theta)
    # z = r * np.sin(theta)
    # # 旋转抛物面：y = x² + z²（基础碗形，开口沿y轴正方向）
    # y_base = x**2 + z**2
    
    # # 2. 实现y轴倾斜：对x-z平面进行轻微旋转，让碗形沿y轴倾斜
    # tilt_angle = np.pi / 6  # 倾斜30度（沿z轴旋转，使y轴产生倾斜）
    # x_tilted = x * np.cos(tilt_angle) - y_base * np.sin(tilt_angle)
    # y_tilted = x * np.sin(tilt_angle) + y_base * np.cos(tilt_angle)
    
    # # 3. 添加少量噪声，模拟真实数据
    # noise = np.random.normal(0, 0.05, (num_points, 3))
    # bowl_data = np.column_stack((x_tilted, y_tilted, z)) + noise

    bowl_data = []
    for i in range(10):
        for j in range(15):
            cx = 10/2
            cy = 15/2
            dis = math.sqrt( (i - cx)**2 + (j - cy)**2 )
            bowl_data.append([i, j, i + j + dis])
    bowl_data = np.array(bowl_data)
    
    return bowl_data

# # 生成初始数据
# bowl_data = generate_tilted_bowl_data()
# x_init, y_init, z_init = bowl_data[:, 0], bowl_data[:, 1], bowl_data[:, 2]

import numpy as np

import numpy as np

def fit_plane_and_get_normal(points):
    """
    使用np.linalg.lstsq（最小二乘法）对3D点云进行平面拟合，求解平面方程和法向量
    :param points: 3D点云数据 (n, 3)，n为点的数量
    :return: 平面参数 (A, B, C, D)、单位法向量 (nx, ny, nz)、重心坐标 (cx, cy, cz)
    """
    # 步骤1：校验输入数据维度（保证数据合法性）
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("输入点云数据必须是(n, 3)维度的二维数组，每行对应一个3D点的xyz坐标")
    
    n = points.shape[0]
    if n < 3:
        raise ValueError("点云数据至少需要3个点才能拟合平面")
    
    # 步骤2：提取x、y、z坐标，计算数据重心（用于后续结果验证，不影响最小二乘求解）
    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]
    centroid = np.mean(points, axis=0)
    cx, cy, cz = centroid
    
    # 步骤3：构造最小二乘的设计矩阵X和目标向量y（核心步骤）
    # 设计矩阵X：(n, 3)，每行格式为 [x_i, y_i, 1]，对应线性模型 z = a0*x + a1*y + a2
    X_design = np.column_stack((x, y, np.ones(n)))
    # 目标向量y：(n,)，对应所有点的z坐标
    y_target = z
    
    # 步骤4：使用np.linalg.lstsq求解最小二乘问题
    # rcond=None：使用默认的条件数阈值，保证求解稳定性
    result = np.linalg.lstsq(X_design, y_target, rcond=None)
    params = result[0]  # 提取求解结果：[a0, a1, a2]
    a0, a1, a2 = params
    
    # 步骤5：从线性模型参数还原平面一般方程的[A, B, C, D]
    # 线性模型：z = a0*x + a1*y + a2 → 变形为：a0*x + a1*y - 1*z + a2 = 0
    A = a0
    B = a1
    C = -1.0
    D = a2
    
    # 步骤6：构造法向量并单位化（确保后续四元数旋转的准确性）
    normal = np.array([A, B, C])
    normal_norm = np.linalg.norm(normal)
    if normal_norm < 1e-8:  # 防止除以零（点云过于集中时）
        raise ValueError("点云数据过于集中，无法拟合有效平面")
    # unit_normal = normal / normal_norm
    unit_normal = np.array([A, B, C])
    
    # 步骤7：返回结果（保持与原函数一致的返回格式，兼容后续代码）
    plane_params = (A, B, C, D)
    return plane_params, unit_normal, centroid

# # 执行平面拟合
# plane_params, unit_normal, centroid = fit_plane_and_get_normal(bowl_data)
# A, B, C, D = plane_params
# print(f"拟合平面方程：{A:.6f}x + {B:.6f}y + {C:.6f}z + {D:.6f} = 0")
# print(f"平面单位法向量：{unit_normal}")
# print(f"数据重心坐标：{centroid}")

def quaternion_rotation(points, axis, angle_deg):
    """
    使用四元数法将3D点云绕指定轴旋转指定角度
    :param points: 待旋转3D点云 (n, 3)
    :param axis: 旋转轴（单位向量）(3,)
    :param angle_deg: 旋转角度（角度制，转为弧度制计算）
    :return: 旋转后的点云 (n, 3)
    """
    # 步骤1：参数预处理
    angle_rad = np.radians(angle_deg)  # 角度转弧度
    axis = axis / np.linalg.norm(axis)  # 确保旋转轴为单位向量
    
    # 步骤2：构造旋转四元数 q = (w, x, y, z)
    w = np.cos(angle_rad / 2)
    x, y, z = axis * np.sin(angle_rad / 2)
    q = np.array([w, x, y, z])  # 旋转四元数
    
    # 步骤3：构造四元数的共轭（单位四元数，共轭即为逆）
    q_conj = np.array([w, -x, -y, -z])  # q̄ = (w, -x, -y, -z)
    
    # 步骤4：遍历每个点，执行四元数旋转
    rotated_points = []
    for point in points:
        # 将3D点转为纯虚四元数 p = (0, x, y, z)
        p = np.array([0, point[0], point[1], point[2]])
        
        # 步骤5：四元数乘法运算：p' = q * p * q̄
        # 定义四元数乘法函数
        def quat_mult(a, b):
            a_w, a_x, a_y, a_z = a
            b_w, b_x, b_y, b_z = b
            w = a_w*b_w - a_x*b_x - a_y*b_y - a_z*b_z
            x = a_w*b_x + a_x*b_w + a_y*b_z - a_z*b_y
            y = a_w*b_y - a_x*b_z + a_y*b_w + a_z*b_x
            z = a_w*b_z + a_x*b_y - a_y*b_x + a_z*b_w
            return np.array([w, x, y, z])
        
        # 计算 q*p
        q_p = quat_mult(q, p)
        # 计算 (q*p)*q̄
        q_p_qconj = quat_mult(q_p, q_conj)
        
        # 步骤6：提取旋转后的点坐标（纯虚四元数的虚部）
        rotated_point = q_p_qconj[1:]  # 舍去实部，保留x,y,z
        rotated_points.append(rotated_point)
    
    return np.array(rotated_points)

def quaternion_rotation2(points, axis, angle_deg):
    angle_deg = angle_deg * np.pi / 180
    c = np.cos(angle_deg)
    s = np.sin(angle_deg)

    rotated_points = []
    vx = axis[0]
    vy = axis[1]
    vz = axis[2]
    for point in points:
        old_x = point[0]
        old_y = point[1]
        old_z = point[2]
        new_x = (vx*vx*(1 - c) + c) * old_x + (vx*vy*(1 - c) - vz*s) * old_y + (vx*vz*(1 - c) + vy*s) * old_z
        new_y = (vy*vx*(1 - c) + vz*s) * old_x + (vy*vy*(1 - c) + c) * old_y + (vy*vz*(1 - c) - vx*s) * old_z
        new_z = (vx*vz*(1 - c) - vy*s) * old_x + (vy*vz*(1 - c) + vx*s) * old_y + (vz*vz*(1 - c) + c) * old_z
    rotated_points.append[new_x, new_y, new_z]



# 定义旋转角度列表（90、180、270度）
# rotation_angles = [90, 180, 270]
# rotated_data_dict = {}

# 执行旋转：以平面法向量为旋转轴，分别旋转不同角度
# for angle in rotation_angles:
#     rotated_data = quaternion_rotation(bowl_data, unit_normal, angle)
#     rotated_data_dict[angle] = rotated_data
#     print(f"已完成 {angle} 度旋转，数据形状：{rotated_data.shape}")

def plot_all_results(init_data, rotated_data_dict, plane_params, normal, centroid):
    """
    绘制所有结果：初始数据、拟合平面、各角度旋转后数据
    """
    # 提取初始数据
    x_init, y_init, z_init = init_data[:, 0], init_data[:, 1], init_data[:, 2]
    A, B, C, D = plane_params
    
    # 创建子图（2行3列：初始数据+拟合平面、90度、180度、270度、法向量示意、平面网格）
    fig = plt.figure()
    
    # 子图1：初始碗形数据 + 拟合平面
    ax1 = fig.add_subplot(2, 3, 1, projection='3d')
    ax1.scatter(x_init, y_init, z_init, c='blue', s=1, alpha=0.5, label='初始碗形数据')
    ax1.plot_surface(x_init.reshape(10,15), y_init.reshape(10,15), z_init.reshape(10,15), color='blue', alpha=0.3, label='初始碗形数据')
    
    # 绘制拟合平面（生成平面网格）
    x_plane = np.linspace(np.min(x_init), np.max(x_init), 20)
    z_plane = np.linspace(np.min(z_init), np.max(z_init), 20)
    x_plane, z_plane = np.meshgrid(x_plane, z_plane)
    y_plane = (-A * x_plane - C * z_plane - D) / B  # 从平面方程解出y
    ax1.plot_surface(x_plane, y_plane, z_plane, color='red', alpha=0.3, label='拟合平面')
    
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    ax1.set_title('初始碗形数据 + 拟合平面')
    ax1.legend()
    
    # 子图2-4：90、180、270度旋转后数据
    for idx, angle in enumerate(rotation_angles, 2):
        rotated_data = rotated_data_dict[angle]
        x_rot, y_rot, z_rot = rotated_data[:, 0], rotated_data[:, 1], rotated_data[:, 2]
        ax = fig.add_subplot(2, 3, idx, projection='3d')
        ax.scatter(x_rot, y_rot, z_rot, c='green', s=1, alpha=0.5, label=f'{angle}度旋转后数据')
        ax.plot_surface(x_rot.reshape(10,15), y_rot.reshape(10,15), z_rot.reshape(10,15), color='green', alpha=0.5, label=f'{angle}度旋转后数据')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f'{angle}度旋转后曲面结果')
        ax.legend()
    
    # 子图5：法向量示意（重心为起点，法向量为方向）
    ax5 = fig.add_subplot(2, 3, 5, projection='3d')
    ax5.scatter(x_init, y_init, z_init, c='blue', s=1, alpha=0.3)
    ax5.plot_surface(x_init.reshape(10,15), y_init.reshape(10,15), z_init.reshape(10,15),color='blue',  alpha=0.3)
    # 绘制法向量（放大5倍便于观察）
    nx, ny, nz = normal
    cx, cy, cz = centroid
    ax5.quiver(cx, cy, cz, nx*5, ny*5, nz*5, color='red', linewidth=2, label='平面法向量')
    ax5.set_xlabel('X')
    ax5.set_ylabel('Y')
    ax5.set_zlabel('Z')
    ax5.set_title('平面法向量示意')
    ax5.legend()
    
    # 子图6：旋转轴（法向量）+ 旋转后数据叠加
    ax6 = fig.add_subplot(2, 3, 6, projection='3d')
    for angle, rotated_data in rotated_data_dict.items():
        x_rot, y_rot, z_rot = rotated_data[:, 0], rotated_data[:, 1], rotated_data[:, 2]
        ax6.scatter(x_rot, y_rot, z_rot, s=1, alpha=0.4, label=f'{angle}度')
        ax6.plot_surface(x_rot.reshape(10,15), y_rot.reshape(10,15), z_rot.reshape(10,15), alpha=0.4, label=f'{angle}度')
    # 绘制旋转轴（法向量）
    ax6.quiver(cx, cy, cz, nx*5, ny*5, nz*5, color='black', linewidth=3, label='旋转轴（法向量）')
    ax6.set_xlabel('X')
    ax6.set_ylabel('Y')
    ax6.set_zlabel('Z')
    ax6.set_title('各角度旋转结果叠加 + 旋转轴')
    ax6.legend()
    
    plt.tight_layout()
    plt.show()

# 执行可视化
# plot_all_results(bowl_data, rotated_data_dict, plane_params, unit_normal, centroid)

if __name__ == "__main__":
    # 1. 生成数据
    bowl_data = generate_tilted_bowl_data()
    print(bowl_data.shape)
    
    # 2. 平面拟合与法向量求解
    plane_params, unit_normal, centroid = fit_plane_and_get_normal(bowl_data)
    A, B, C, D = plane_params
    print("="*50)
    print(f"拟合平面方程：{A:.6f}x + {B:.6f}y + {C:.6f}z + {D:.6f} = 0")
    print(f"平面单位法向量：{unit_normal}")
    print(f"数据重心坐标：{centroid}")
    print("="*50)
    
    # 3. 四元数旋转
    rotation_angles = [90, 180, 270]
    rotated_data_dict = {}
    for angle in rotation_angles:
        rotated_data = quaternion_rotation(bowl_data, unit_normal, angle)
        rotated_data_dict[angle] = rotated_data
        print(f"已完成 {angle} 度旋转，数据形状：{rotated_data.shape}")
    
    # 4. 可视化所有结果
    plot_all_results(bowl_data, rotated_data_dict, plane_params, unit_normal, centroid)