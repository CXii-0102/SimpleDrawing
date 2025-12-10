from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QPolygon

class ShapeUtils:
    """图形工具类，包含各种图形相关的计算方法"""
    
    @staticmethod
    def get_rect_points(start, end):
        """获取QRect对象"""
        x = min(start.x(), end.x())
        y = min(start.y(), end.y())
        width = abs(end.x() - start.x())
        height = abs(end.y() - start.y())
        return QRect(x, y, width, height)
    
    @staticmethod
    def is_point_near_line(point, start, end, tolerance=5):
        """判断点是否靠近直线"""
        line_length = ((end.x() - start.x())**2 + (end.y() - start.y())**2)**0.5
        if line_length == 0:
            return False
        
        # 使用向量叉积计算距离
        distance = abs((end.x() - start.x()) * (start.y() - point.y()) - 
                       (start.x() - point.x()) * (end.y() - start.y())) / line_length
        
        return distance <= tolerance
    
    @staticmethod
    def is_point_in_ellipse(point, rect):
        """判断点是否在椭圆内"""
        if rect.width() == 0 or rect.height() == 0:
            return False
        
        center_x = rect.center().x()
        center_y = rect.center().y()
        a = rect.width() / 2
        b = rect.height() / 2
        
        if a == 0 or b == 0:
            return False
            
        normalized_x = (point.x() - center_x) / a
        normalized_y = (point.y() - center_y) / b
        
        return (normalized_x**2 + normalized_y**2) <= 1
    
    @staticmethod
    def is_point_in_shape(point, shape):
        """判断点是否在图形内"""
        if shape['tool'] == 'line':
            return ShapeUtils.is_point_near_line(point, shape['start'], shape['end'])
        elif shape['tool'] == 'rect':
            rect = ShapeUtils.get_rect_points(shape['start'], shape['end'])
            return rect.contains(point)
        elif shape['tool'] == 'circle':
            rect = ShapeUtils.get_rect_points(shape['start'], shape['end'])
            return ShapeUtils.is_point_in_ellipse(point, rect)
        elif shape['tool'] == 'polygon':
            polygon = QPolygon(shape['points'])
            return polygon.containsPoint(point, Qt.OddEvenFill)
        elif shape['tool'] in ['bezier_curve', 'bspline_curve']:
            # 检查是否靠近曲线的控制点区域
            control_points = shape.get('control_points', [])
            if not control_points:
                return False
            # 检查点是否在控制点附近（用于选择）
            for cp in control_points:
                dx = point.x() - cp.x()
                dy = point.y() - cp.y()
                if dx * dx + dy * dy <= 100:  # 10像素范围
                    return True
            return False
        elif shape['tool'] == 'bezier_surface':
            # 检查是否在曲面的控制网格区域
            control_grid = shape.get('control_grid', [])
            if not control_grid or not control_grid[0]:
                return False
            # 检查点是否在控制网格的边界内
            bounds = ShapeUtils.get_shape_bounds(shape)
            return bounds.contains(point)
        
        return False
    
    @staticmethod
    def get_shape_bounds(shape):
        """获取图形的边界矩形"""
        if shape['tool'] == 'line':
            x = min(shape['start'].x(), shape['end'].x())
            y = min(shape['start'].y(), shape['end'].y())
            width = abs(shape['end'].x() - shape['start'].x())
            height = abs(shape['end'].y() - shape['start'].y())
            return QRect(x, y, width, height)
        elif shape['tool'] in ['rect', 'circle']:
            return ShapeUtils.get_rect_points(shape['start'], shape['end'])
        elif shape['tool'] == 'polygon':
            return QPolygon(shape['points']).boundingRect()
        elif shape['tool'] in ['bezier_curve', 'bspline_curve']:
            # 曲线的边界：所有控制点的边界
            control_points = shape.get('control_points', [])
            if not control_points:
                return QRect()
            min_x = min(p.x() for p in control_points)
            min_y = min(p.y() for p in control_points)
            max_x = max(p.x() for p in control_points)
            max_y = max(p.y() for p in control_points)
            return QRect(min_x, min_y, max_x - min_x, max_y - min_y)
        elif shape['tool'] == 'bezier_surface':
            # 曲面的边界：所有控制点的边界
            control_grid = shape.get('control_grid', [])
            if not control_grid or not control_grid[0]:
                return QRect()
            all_points = []
            for row in control_grid:
                all_points.extend(row)
            min_x = min(p.x() for p in all_points)
            min_y = min(p.y() for p in all_points)
            max_x = max(p.x() for p in all_points)
            max_y = max(p.y() for p in all_points)
            return QRect(min_x, min_y, max_x - min_x, max_y - min_y)
        
        return QRect()
    
    @staticmethod
    def get_shape_center(shape):
        """获取图形的中心点"""
        if shape['tool'] == 'line':
            return QPoint(
                (shape['start'].x() + shape['end'].x()) // 2,
                (shape['start'].y() + shape['end'].y()) // 2
            )
        elif shape['tool'] in ['rect', 'circle']:
            return QPoint(
                (shape['start'].x() + shape['end'].x()) // 2,
                (shape['start'].y() + shape['end'].y()) // 2
            )
        elif shape['tool'] == 'polygon':
            if not shape['points']:
                return QPoint(0, 0)
            avg_x = sum(point.x() for point in shape['points']) // len(shape['points'])
            avg_y = sum(point.y() for point in shape['points']) // len(shape['points'])
            return QPoint(avg_x, avg_y)
        elif shape['tool'] in ['bezier_curve', 'bspline_curve']:
            # 曲线中心：所有控制点的中心
            control_points = shape.get('control_points', [])
            if not control_points:
                return QPoint(0, 0)
            avg_x = sum(p.x() for p in control_points) // len(control_points)
            avg_y = sum(p.y() for p in control_points) // len(control_points)
            return QPoint(avg_x, avg_y)
        elif shape['tool'] == 'bezier_surface':
            # 曲面中心：所有控制点的中心
            control_grid = shape.get('control_grid', [])
            if not control_grid or not control_grid[0]:
                return QPoint(0, 0)
            all_points = []
            for row in control_grid:
                all_points.extend(row)
            avg_x = sum(p.x() for p in all_points) // len(all_points)
            avg_y = sum(p.y() for p in all_points) // len(all_points)
            return QPoint(avg_x, avg_y)
        
        return QPoint(0, 0)