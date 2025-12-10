"""
参数曲面算法模块
实现经典参数曲面算法：Bézier曲面、三边Bézier曲面
不使用外部库，完全手动实现
"""
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor
import math


class SurfaceAlgorithms:
    """参数曲面算法类"""
    
    @staticmethod
    def factorial(n):
        """计算阶乘"""
        if n <= 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result
    
    @staticmethod
    def binomial_coefficient(n, i):
        """计算二项式系数 C(n, i)"""
        if i < 0 or i > n:
            return 0
        return SurfaceAlgorithms.factorial(n) // (SurfaceAlgorithms.factorial(i) * SurfaceAlgorithms.factorial(n - i))
    
    @staticmethod
    def bernstein_basis(i, n, t):
        """
        计算Bernstein基函数
        B_{i,n}(t) = C(n,i) * t^i * (1-t)^(n-i)
        """
        return SurfaceAlgorithms.binomial_coefficient(n, i) * (t ** i) * ((1 - t) ** (n - i))
    
    @staticmethod
    def bezier_surface(control_grid, u_samples=20, v_samples=20):
        """
        计算双三次Bézier曲面（张量积形式）
        :param control_grid: 控制点网格，二维列表 [[QPoint, ...], [...], ...]
                            control_grid[i][j] 表示第i行第j列的控制点
        :param u_samples: u方向采样数
        :param v_samples: v方向采样数
        :return: 字典 {
            'points': 曲面点网格（二维列表）,
            'u_lines': u方向的线（用于网格显示）,
            'v_lines': v方向的线（用于网格显示）
        }
        """
        if not control_grid or not control_grid[0]:
            return {'points': [], 'u_lines': [], 'v_lines': []}
        
        m = len(control_grid)      # u方向控制点数
        n = len(control_grid[0])   # v方向控制点数
        
        # 生成曲面点
        surface_points = []
        for i in range(u_samples + 1):
            u = i / u_samples
            row_points = []
            for j in range(v_samples + 1):
                v = j / v_samples
                
                # 计算曲面上的点 S(u,v)
                x = 0.0
                y = 0.0
                z = 0.0  # 用y坐标作为高度，z作为深度（用于3D效果）
                
                for ui in range(m):
                    for vi in range(n):
                        # 张量积：B_ui,m-1(u) * B_vi,n-1(v)
                        basis = (SurfaceAlgorithms.bernstein_basis(ui, m - 1, u) * 
                                SurfaceAlgorithms.bernstein_basis(vi, n - 1, v))
                        
                        ctrl_pt = control_grid[ui][vi]
                        x += ctrl_pt.x() * basis
                        y += ctrl_pt.y() * basis
                        # 简单的高度计算（可以从控制点额外属性获取，这里简化处理）
                        # z += 0  # 2D投影，z暂时为0
                
                row_points.append(QPoint(int(x), int(y)))
            surface_points.append(row_points)
        
        # 生成网格线
        u_lines = []  # 固定u，改变v的线
        v_lines = []  # 固定v，改变u的线
        
        # u方向的线（每一行）
        for row in surface_points:
            u_lines.append(row)
        
        # v方向的线（每一列）
        for j in range(len(surface_points[0])):
            line = []
            for i in range(len(surface_points)):
                line.append(surface_points[i][j])
            v_lines.append(line)
        
        return {
            'points': surface_points,
            'u_lines': u_lines,
            'v_lines': v_lines
        }
    
    @staticmethod
    def triangular_bernstein_basis(i, j, k, n, u, v, w):
        """
        计算三角域上的Bernstein基函数
        B_{i,j,k}^n(u,v,w) = (n! / (i!j!k!)) * u^i * v^j * w^k
        其中 i+j+k=n, u+v+w=1
        """
        if i + j + k != n:
            return 0.0
        
        # 计算多项式系数
        numerator = SurfaceAlgorithms.factorial(n)
        denominator = (SurfaceAlgorithms.factorial(i) * 
                      SurfaceAlgorithms.factorial(j) * 
                      SurfaceAlgorithms.factorial(k))
        
        coefficient = numerator / denominator
        
        # 计算基函数值
        return coefficient * (u ** i) * (v ** j) * (w ** k)
    
    @staticmethod
    def barycentric_to_cartesian(u, v, w, p0, p1, p2):
        """
        将重心坐标转换为笛卡尔坐标
        :param u, v, w: 重心坐标（u+v+w=1）
        :param p0, p1, p2: 三角形的三个顶点
        :return: QPoint
        """
        x = u * p0.x() + v * p1.x() + w * p2.x()
        y = u * p0.y() + v * p1.y() + w * p2.y()
        return QPoint(int(x), int(y))
    
    @staticmethod
    def triangular_bezier_surface(control_points, degree, samples=20, domain_triangle=None):
        """
        计算三边Bézier曲面
        :param control_points: 控制点字典 {(i,j,k): QPoint, ...}
                              其中 i+j+k=degree
        :param degree: 曲面次数
        :param samples: 采样数量
        :param domain_triangle: 参数域三角形的三个顶点 [p0, p1, p2]
                               如果为None，则使用单位三角形
        :return: 字典 {
            'points': 曲面点列表,
            'triangles': 三角形网格（用于填充）
        }
        """
        if domain_triangle is None:
            # 默认使用一个等边三角形
            domain_triangle = [
                QPoint(200, 400),
                QPoint(400, 100),
                QPoint(600, 400)
            ]
        
        surface_points = []
        triangles = []
        
        # 在重心坐标系中采样
        step = 1.0 / samples
        
        for ui in range(samples + 1):
            u = ui * step
            for vi in range(samples + 1 - ui):
                v = vi * step
                w = 1.0 - u - v
                
                if w < -1e-10:  # 超出三角形范围
                    continue
                
                # 计算曲面上的点
                x = 0.0
                y = 0.0
                
                # 遍历所有控制点
                for (i, j, k), ctrl_pt in control_points.items():
                    if i + j + k != degree:
                        continue
                    
                    basis = SurfaceAlgorithms.triangular_bernstein_basis(i, j, k, degree, u, v, w)
                    x += ctrl_pt.x() * basis
                    y += ctrl_pt.y() * basis
                
                surface_points.append({
                    'point': QPoint(int(x), int(y)),
                    'uv': (u, v, w),
                    'domain_point': SurfaceAlgorithms.barycentric_to_cartesian(u, v, w, *domain_triangle)
                })
        
        # 生成三角形网格（用于填充）
        # 这里简化处理，仅生成点
        
        return {
            'points': surface_points,
            'triangles': triangles
        }
    
    @staticmethod
    def interpolate_color(color1, color2, t):
        """
        在两个颜色之间插值
        :param color1: 起始颜色 QColor
        :param color2: 结束颜色 QColor
        :param t: 插值参数 [0, 1]
        :return: QColor
        """
        if color1 is None or color2 is None:
            return QColor(128, 128, 128)
        
        r = int(color1.red() * (1 - t) + color2.red() * t)
        g = int(color1.green() * (1 - t) + color2.green() * t)
        b = int(color1.blue() * (1 - t) + color2.blue() * t)
        
        return QColor(r, g, b)
    
    @staticmethod
    def scan_line_fill_triangle(p0, p1, p2, color1, color2, color3):
        """
        使用扫描线算法填充三角形，并实现颜色渐变
        :param p0, p1, p2: 三角形的三个顶点 QPoint
        :param color1, color2, color3: 三个顶点的颜色
        :return: 像素列表 [(QPoint, QColor), ...]
        """
        # 按y坐标排序顶点
        vertices = sorted([(p0, color1), (p1, color2), (p2, color3)], key=lambda v: v[0].y())
        (v0, c0), (v1, c1), (v2, c2) = vertices
        
        pixels = []
        
        # 扫描线填充
        y_min = v0.y()
        y_max = v2.y()
        
        if y_max == y_min:
            return pixels
        
        for y in range(y_min, y_max + 1):
            # 计算与扫描线相交的x坐标
            x_intersects = []
            
            # 检查三条边
            edges = [(v0, v1, c0, c1), (v1, v2, c1, c2), (v2, v0, c2, c0)]
            
            for va, vb, ca, cb in edges:
                if va.y() == vb.y():
                    continue
                
                if min(va.y(), vb.y()) <= y <= max(va.y(), vb.y()):
                    # 计算交点
                    t = (y - va.y()) / (vb.y() - va.y()) if vb.y() != va.y() else 0
                    x = int(va.x() + t * (vb.x() - va.x()))
                    
                    # 计算颜色
                    color = SurfaceAlgorithms.interpolate_color(ca, cb, t)
                    x_intersects.append((x, color))
            
            # 填充扫描线
            if len(x_intersects) >= 2:
                x_intersects.sort(key=lambda item: item[0])
                x_start, color_start = x_intersects[0]
                x_end, color_end = x_intersects[-1]
                
                for x in range(x_start, x_end + 1):
                    if x_end != x_start:
                        t = (x - x_start) / (x_end - x_start)
                        color = SurfaceAlgorithms.interpolate_color(color_start, color_end, t)
                    else:
                        color = color_start
                    
                    pixels.append((QPoint(x, y), color))
        
        return pixels
