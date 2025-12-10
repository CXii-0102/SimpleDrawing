"""
参数曲线算法模块
实现经典参数曲线算法：Bézier曲线、B样条曲线
不使用外部库，完全手动实现
"""
from PyQt5.QtCore import QPoint
import math


class CurveAlgorithms:
    """参数曲线算法类"""
    
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
        return CurveAlgorithms.factorial(n) // (CurveAlgorithms.factorial(i) * CurveAlgorithms.factorial(n - i))
    
    @staticmethod
    def bernstein_basis(i, n, t):
        """
        计算Bernstein基函数
        B_{i,n}(t) = C(n,i) * t^i * (1-t)^(n-i)
        """
        return CurveAlgorithms.binomial_coefficient(n, i) * (t ** i) * ((1 - t) ** (n - i))
    
    @staticmethod
    def bezier_curve_bernstein(control_points, num_samples=100):
        """
        使用Bernstein基函数计算Bézier曲线
        :param control_points: 控制点列表 [QPoint, QPoint, ...]
        :param num_samples: 采样点数量
        :return: 曲线上的点列表
        """
        if len(control_points) < 2:
            return []
        
        n = len(control_points) - 1  # 曲线次数
        curve_points = []
        
        for i in range(num_samples + 1):
            t = i / num_samples
            x = 0.0
            y = 0.0
            
            # 计算曲线上的点
            for j in range(n + 1):
                basis = CurveAlgorithms.bernstein_basis(j, n, t)
                x += control_points[j].x() * basis
                y += control_points[j].y() * basis
            
            curve_points.append(QPoint(int(x), int(y)))
        
        return curve_points
    
    @staticmethod
    def de_casteljau(control_points, t):
        """
        使用de Casteljau递推算法计算Bézier曲线上的点
        :param control_points: 控制点列表
        :param t: 参数值 [0, 1]
        :return: 曲线上的点
        """
        if not control_points:
            return None
        
        # 创建工作数组（避免修改原始控制点）
        points = [[p.x(), p.y()] for p in control_points]
        n = len(points)
        
        # de Casteljau递推
        for r in range(1, n):
            for i in range(n - r):
                points[i][0] = (1 - t) * points[i][0] + t * points[i + 1][0]
                points[i][1] = (1 - t) * points[i][1] + t * points[i + 1][1]
        
        return QPoint(int(points[0][0]), int(points[0][1]))
    
    @staticmethod
    def bezier_curve_de_casteljau(control_points, num_samples=100):
        """
        使用de Casteljau算法计算Bézier曲线
        :param control_points: 控制点列表
        :param num_samples: 采样点数量
        :return: 曲线上的点列表
        """
        if len(control_points) < 2:
            return []
        
        curve_points = []
        for i in range(num_samples + 1):
            t = i / num_samples
            point = CurveAlgorithms.de_casteljau(control_points, t)
            if point:
                curve_points.append(point)
        
        return curve_points
    
    @staticmethod
    def b_spline_basis(i, k, t, knots):
        """
        计算B样条基函数（Cox-de Boor递推公式）
        :param i: 基函数索引
        :param k: 基函数次数
        :param t: 参数值
        :param knots: 节点向量
        :return: 基函数值
        """
        # 边界检查
        if i < 0 or i + k + 1 >= len(knots):
            return 0.0
            
        if k == 0:
            # 零次基函数
            if i >= len(knots) - 1:
                return 0.0
            if knots[i] <= t < knots[i + 1]:
                return 1.0
            # 特殊处理最后一个区间（t等于最大节点值）
            if abs(t - knots[i + 1]) < 1e-10 and t >= knots[-1] - 1e-10:
                return 1.0
            return 0.0
        
        # 递推计算
        # 第一项
        denominator1 = knots[i + k] - knots[i]
        if abs(denominator1) < 1e-10:
            term1 = 0.0
        else:
            term1 = (t - knots[i]) / denominator1 * CurveAlgorithms.b_spline_basis(i, k - 1, t, knots)
        
        # 第二项
        denominator2 = knots[i + k + 1] - knots[i + 1]
        if abs(denominator2) < 1e-10:
            term2 = 0.0
        else:
            term2 = (knots[i + k + 1] - t) / denominator2 * CurveAlgorithms.b_spline_basis(i + 1, k - 1, t, knots)
        
        return term1 + term2
    
    @staticmethod
    def generate_uniform_knots(n, k):
        """
        生成均匀B样条节点向量
        :param n: 控制点数量
        :param k: B样条次数
        :return: 节点向量
        """
        # 节点向量长度 = n + k + 1
        m = n + k + 1
        knots = []
        for i in range(m):
            knots.append(float(i))
        return knots
    
    @staticmethod
    def generate_clamped_knots(n, k):
        """
        生成夹紧(clamped) B样条节点向量
        前k+1个节点为0，后k+1个节点为1，中间均匀分布
        :param n: 控制点数量
        :param k: B样条次数
        :return: 节点向量
        """
        m = n + k + 1
        knots = []
        
        # 前k+1个节点为0
        for i in range(k + 1):
            knots.append(0.0)
        
        # 中间节点均匀分布
        num_internal = m - 2 * (k + 1)
        for i in range(1, num_internal + 1):
            knots.append(i / (num_internal + 1))
        
        # 后k+1个节点为1
        for i in range(k + 1):
            knots.append(1.0)
        
        return knots
    
    @staticmethod
    def b_spline_curve(control_points, degree=3, num_samples=100, knot_type='clamped'):
        """
        计算B样条曲线
        :param control_points: 控制点列表
        :param degree: B样条次数（2=二次，3=三次）
        :param num_samples: 采样点数量
        :param knot_type: 节点类型 'uniform' 或 'clamped'
        :return: 曲线上的点列表
        """
        n = len(control_points)
        if n < degree + 1:
            return []
        
        # 生成节点向量
        if knot_type == 'uniform':
            knots = CurveAlgorithms.generate_uniform_knots(n, degree)
        else:  # clamped
            knots = CurveAlgorithms.generate_clamped_knots(n, degree)
        
        # 确定参数范围
        t_min = knots[degree]
        t_max = knots[n]
        
        # 安全检查
        if t_min >= t_max:
            return []
        
        curve_points = []
        for i in range(num_samples + 1):
            # 计算参数值
            if i == num_samples:
                t = t_max - 1e-10  # 避免精确等于t_max时的边界问题
            else:
                t = t_min + (t_max - t_min) * i / num_samples
            
            # 确保t在有效范围内
            t = max(t_min, min(t, t_max - 1e-10))
            
            # 计算曲线上的点
            x = 0.0
            y = 0.0
            for j in range(n):
                basis = CurveAlgorithms.b_spline_basis(j, degree, t, knots)
                x += control_points[j].x() * basis
                y += control_points[j].y() * basis
            
            # 检查计算结果是否有效
            if abs(x) < 1e8 and abs(y) < 1e8:  # 防止异常大的值
                curve_points.append(QPoint(int(x), int(y)))
        
        return curve_points
    
    @staticmethod
    def quadratic_bezier(p0, p1, p2, num_samples=50):
        """
        二次Bézier曲线（3个控制点）
        :param p0, p1, p2: 控制点
        :param num_samples: 采样点数量
        :return: 曲线上的点列表
        """
        return CurveAlgorithms.bezier_curve_bernstein([p0, p1, p2], num_samples)
    
    @staticmethod
    def cubic_bezier(p0, p1, p2, p3, num_samples=50):
        """
        三次Bézier曲线（4个控制点）
        :param p0, p1, p2, p3: 控制点
        :param num_samples: 采样点数量
        :return: 曲线上的点列表
        """
        return CurveAlgorithms.bezier_curve_bernstein([p0, p1, p2, p3], num_samples)
