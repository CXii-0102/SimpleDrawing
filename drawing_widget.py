from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPolygon
from PyQt5.QtCore import Qt, QPoint

class DrawingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.current_tool = "line"  # 默认为直线
        self.shapes = []
        
        # 基本绘图状态
        self.start_point = None
        self.end_point = None
        self.temp_end_point = None
        
        # 图形属性
        self.current_color = QColor(Qt.black)
        self.current_line_width = 2
        self.current_fill_color = None
        
        # 多边形专用状态
        self.polygon_points = []
        self.is_drawing_polygon = False

        print("DrawingWidget initialized")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        
        # 1. 绘制所有已保存的图形
        for shape in self.shapes:
            self.draw_shape(painter, shape)

        # 2. 绘制临时预览
        if self.current_tool == 'polygon' and self.is_drawing_polygon:
            self.draw_polygon_preview(painter)
        elif self.start_point and self.temp_end_point:
            self.draw_temp_shape(painter)

        # 3. 绘制边框和状态
        painter.setPen(Qt.red)
        painter.drawRect(0, 0, self.width()-1, self.height()-1)
        
        status_text = f"当前工具：{self.current_tool}"
        if self.current_tool == "polygon" and self.is_drawing_polygon:
            status_text += f" (已添加{len(self.polygon_points)}个顶点，双击完成)"
        painter.drawText(10, 30, status_text)

    def draw_shape(self, painter, shape):
        pen = QPen(shape["color"], shape["line_width"])
        painter.setPen(pen)
        
        if shape.get("fill_color"):
            painter.setBrush(QBrush(shape["fill_color"]))
        else:
            painter.setBrush(Qt.NoBrush)

        if shape['tool'] == 'line':
            painter.drawLine(shape['start'], shape['end'])
        elif shape['tool'] == 'rect':
            rect = self._get_rect(shape['start'], shape['end'])
            painter.drawRect(rect)
        elif shape['tool'] == 'circle':
            rect = self._get_rect(shape['start'], shape['end'])
            painter.drawEllipse(rect)
        elif shape['tool'] == 'polygon' and len(shape['points']) >= 3:
            polygon = QPolygon(shape['points'])
            painter.drawPolygon(polygon)

    def draw_polygon_preview(self, painter):
        """绘制多边形预览"""
        if len(self.polygon_points) == 0:
            return
        
        # 设置虚线画笔用于边
        pen = QPen(self.current_color, self.current_line_width)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # 绘制已确定的边（顶点之间的连线）
        if len(self.polygon_points) > 1:
            for i in range(len(self.polygon_points) - 1):
                painter.drawLine(self.polygon_points[i], self.polygon_points[i + 1])

        # 绘制顶点小圆点
        solid_pen = QPen(self.current_color, 1)
        solid_pen.setStyle(Qt.SolidLine)
        painter.setPen(solid_pen)
        painter.setBrush(QBrush(self.current_color))
        
        for point in self.polygon_points:
            painter.drawEllipse(point, 2, 2)

        # 恢复无填充
        painter.setBrush(Qt.NoBrush)

    def draw_temp_shape(self, painter):
        """绘制其他工具的临时预览"""
        temp_shape = {
            "tool": self.current_tool,
            "start": self.start_point,
            "end": self.temp_end_point,
            "color": self.current_color,
            "line_width": self.current_line_width,
            "fill_color": self.current_fill_color
        }
        painter.setPen(Qt.DashLine)
        self.draw_shape(painter, temp_shape)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.current_tool == "polygon":
                self.handle_polygon_click(event.pos())
            else:
                self.handle_other_tools_click(event.pos())

    def handle_polygon_click(self, pos):
        """处理多边形的点击"""
        if not self.is_drawing_polygon:
            # 开始绘制新多边形
            self.is_drawing_polygon = True
            self.polygon_points = [pos]
            print("开始绘制多边形")
        else:
            # 添加新顶点
            self.polygon_points.append(pos)
            print(f"添加多边形顶点 at {pos}")
        self.update()

    def handle_other_tools_click(self, pos):
        """处理其他工具的点击"""
        self.start_point = pos
        print(f"开始绘图 at {pos}")

    def mouseReleaseEvent(self, event):
        """鼠标释放 - 只处理非多边形工具"""
        if (self.current_tool != "polygon" and 
            event.button() == Qt.LeftButton and 
            self.start_point):
            
            self.end_point = event.pos()
            new_shape = {
                "tool": self.current_tool,
                "start": self.start_point,
                "end": self.end_point,
                "color": self.current_color,
                "line_width": self.current_line_width,
                "fill_color": self.current_fill_color
            }
            self.shapes.append(new_shape)
            self.reset_drawing_state()
            self.update()

    def mouseMoveEvent(self, event):
        """鼠标移动 - 实时预览"""
        if self.current_tool == "polygon" and self.is_drawing_polygon:
            self.temp_end_point = event.pos()
            self.update()
        elif self.start_point:
            self.temp_end_point = event.pos()
            self.update()

    def mouseDoubleClickEvent(self, event):
        """双击完成多边形"""
        if (event.button() == Qt.LeftButton and 
            self.current_tool == "polygon" and 
            self.is_drawing_polygon):
            self.complete_polygon()
        else:
            super().mouseDoubleClickEvent(event)

    def complete_polygon(self):
        """完成多边形绘制"""
        if self.is_drawing_polygon and len(self.polygon_points) >= 3:
            polygon_shape = {
                "tool": "polygon",
                "points": self.polygon_points.copy(),
                "color": self.current_color,
                "line_width": self.current_line_width,
                "fill_color": self.current_fill_color
            }
            self.shapes.append(polygon_shape)
            self.reset_polygon_state()
            print("多边形绘制完成")
        else:
            print("多边形至少需要3个顶点才能完成")

    def reset_drawing_state(self):
        """重置基本绘图状态"""
        self.start_point = None
        self.end_point = None
        self.temp_end_point = None

    def reset_polygon_state(self):
        """重置多边形绘图状态"""
        self.is_drawing_polygon = False
        self.polygon_points = []
        self.temp_end_point = None
        self.update()

    def _point(self, x, y):
        """创建QPoint对象的辅助方法"""
        return QPoint(x, y)

    def _get_rect(self, start, end):
        """根据起点终点计算矩形区域"""
        return start.x(), start.y(), end.x()-start.x(), end.y()-start.y()