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
        
        return QPoint(0, 0)