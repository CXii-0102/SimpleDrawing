from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QPoint

class DrawingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.current_tool = "line" # 默认为直线
        self.shapes = []
        # 绘图
        self.current_shape = None
        self.start_point = None
        self.end_point = None
        self.temp_end_point = None
        # 图形属性
        self.current_color = QColor(Qt.black)
        self.current_line_width = 2
        self.current_fill_color = None
        print("DrawingWidget initialized")

    def paintEvent(self, event):
        # print("paintEvent 被调用!")
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        # 绘制所有已保存的图形
        for shape in self.shapes:
            self.draw_shape(painter, shape)

        # 绘制临时预览图形（如果正在绘图）
        if self.start_point and self.temp_end_point:
            temp_shape = {
                "tool": self.current_tool,
                "start": self.start_point,
                "end": self.temp_end_point,
                "color": self.current_color,
                "line_width": self.current_line_width,
                "fill_color": self.current_fill_color
            }
            # 用虚线画临时图形
            painter.setPen(Qt.DashLine)
            self.draw_shape(painter, temp_shape)

        painter.setPen(Qt.red)
        painter.drawRect(0, 0, self.width()-1, self.height()-1)
        painter.drawText(10, 30, f"当前工具：{self.current_tool}")

    def draw_shape(self, painter, shape):
        # 根据图形类型绘制图形
        pen = QPen(shape["color"], shape["line_width"])
        painter.setPen(pen)
        if shape.get("fill_color"):
            painter.setBrush(QBrush(shape["fill_color"]))
        else:
            painter.setBrush(Qt.NoBrush)

        if shape['tool'] == 'line':
            painter.drawLine(shape['start'], shape['end'])
        elif shape['tool'] == 'rect':
            painter.drawRect(shape['start'].x(), shape['start'].y(),
                             shape['end'].x() - shape['start'].x(),
                             shape['end'].y() - shape['start'].y())
        elif shape['tool'] == 'circle':
            painter.drawEllipse(shape['start'].x(), shape['start'].y(),
                                shape['end'].x() - shape['start'].x(),
                                shape['end'].y() - shape['start'].y())
        elif shape['tool'] == 'polygon':
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            print(f"开始绘图 at {self.start_point}")

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.start_point:
            self.end_point = event.pos()
            # 创建图形数据
            new_shape = {
                "tool": self.current_tool,
                "start": self.start_point,
                "end": self.end_point,
                "color": self.current_color,
                "line_width": self.current_line_width,
                "fill_color": self.current_fill_color
            }
            self.shapes.append(new_shape)
            self.start_point = None # 重置起点
            self.end_point = None
            self.temp_end_point = None
            self.update() # 触发重绘

    def mouseMoveEvent(self, event):
        # 鼠标移动时调用，用于实时预览
        if self.start_point:
            self.temp_end_point = event.pos() # 记录临时终点
            self.update() # 触发重绘

    def _point(self, x, y):
        """创建QPoint对象的辅助方法"""
        from PyQt5.QtCore import QPoint
        return QPoint(x, y)