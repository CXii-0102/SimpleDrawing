from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPolygon
from PyQt5.QtCore import Qt, QPoint
from shape_utils import ShapeUtils

class DrawingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.current_tool = "line"  # 默认为直线
        self.shapes = []

        self.selected_shape_index = -1  # 当前选中的图形索引
        # 拖动状态
        self.is_dragging = False
        self.drag_start_point = None
        self.drag_offset = QPoint(0, 0)
        self.original_shape_data = None  # 保存拖动前的图形数据
        
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

        # 视图缩放
        self.scale_factor = 1.0  # 画布缩放因子
        self.min_scale = 0.2
        self.max_scale = 5.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        # 应用缩放
        painter.scale(self.scale_factor, self.scale_factor)
        
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
        painter.drawRect(0, 0, int((self.width()-1)/self.scale_factor), int((self.height()-1)/self.scale_factor))
        
        status_text = f"当前工具：{self.current_tool}"
        if self.current_tool == "polygon" and self.is_drawing_polygon:
            status_text += f" (已添加{len(self.polygon_points)}个顶点，双击完成)"
        painter.drawText(10, 30, status_text + f" | 缩放: {self.scale_factor:.2f}x")

    def draw_shape(self, painter, shape):
        # 保存 painter 的当前状态
        painter.save()
        
        try:
            # 如果是选中的图形，用不同的颜色或样式
            try:
                is_selected = (self.shapes.index(shape) == self.selected_shape_index)
            except ValueError:
                # 临时预览图形不在 self.shapes 中
                is_selected = False
            
            if is_selected:
                # 选中状态：红色边框，稍粗的线
                pen = QPen(Qt.red, shape["line_width"] + 2)
            else:
                pen = QPen(shape["color"], shape["line_width"])
                
            painter.setPen(pen)
            
            if shape.get("fill_color"):
                # 选中的图形可以半透明填充
                if is_selected:
                    fill_color = QColor(shape["fill_color"])
                    fill_color.setAlpha(128)  # 半透明
                    painter.setBrush(QBrush(fill_color))
                else:
                    painter.setBrush(QBrush(shape["fill_color"]))
            else:
                painter.setBrush(Qt.NoBrush)

            # 原有的绘制代码保持不变...
            if shape['tool'] == 'line':
                painter.drawLine(shape['start'], shape['end'])
            elif shape['tool'] == 'rect':
                rect = ShapeUtils.get_rect_points(shape['start'], shape['end'])
                painter.drawRect(rect)
            elif shape['tool'] == 'circle':
                rect = ShapeUtils.get_rect_points(shape['start'], shape['end'])
                painter.drawEllipse(rect)
            elif shape['tool'] == 'polygon' and len(shape['points']) >= 3:
                polygon = QPolygon(shape['points'])
                painter.drawPolygon(polygon)
                
        finally:
            # 恢复 painter 的原始状态
            painter.restore()

    def draw_polygon_preview(self, painter):
        """绘制多边形预览 - 简化版，不处理填充"""
        if len(self.polygon_points) == 0:
            return
        
        # 保存原始状态
        original_pen = painter.pen()
        original_brush = painter.brush()
        
        # 只绘制边和顶点，不处理填充
        pen = QPen(self.current_color, self.current_line_width)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)  # 确保无填充
        
        # 绘制已确定的边
        if len(self.polygon_points) > 1:
            for i in range(len(self.polygon_points) - 1):
                painter.drawLine(self.polygon_points[i], self.polygon_points[i + 1])
        
        # 绘制顶点小圆点
        solid_pen = QPen(self.current_color, 1)
        solid_pen.setStyle(Qt.SolidLine)
        painter.setPen(solid_pen)
        painter.setBrush(QBrush(self.current_color))
        
        for point in self.polygon_points:
            painter.drawEllipse(point, 3, 3)
        
        # 恢复原始状态
        painter.setPen(original_pen)
        painter.setBrush(original_brush)

    def draw_temp_shape(self, painter):
        """绘制其他工具的临时预览"""
        # 保存状态
        painter.save()
        
        try:
            temp_shape = {
                "tool": self.current_tool,
                "start": self.start_point,
                "end": self.temp_end_point,
                "color": self.current_color,
                "line_width": self.current_line_width,
                "fill_color": self.current_fill_color
            }
            painter.setPen(QPen(self.current_color, self.current_line_width, Qt.DashLine))
            self.draw_shape(painter, temp_shape)
            
        finally:
            # 恢复状态
            painter.restore()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.current_tool == "select":
                if self.select_shape_at_point(self._to_scene_point(event.pos())):
                    # 如果选中了图形，开始拖动准备
                    self.start_dragging(self._to_scene_point(event.pos()))
            elif self.current_tool == "polygon":
                self.handle_polygon_click(self._to_scene_point(event.pos()))
            else:
                self.handle_other_tools_click(self._to_scene_point(event.pos()))

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
        """鼠标释放"""
        if event.button() == Qt.LeftButton:
            if self.current_tool == "select" and self.is_dragging:
                # 结束拖动
                self.end_dragging()
            elif self.current_tool != "polygon" and self.start_point:
                # 其他工具的原有逻辑
                self.end_point = self._to_scene_point(event.pos())
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
        """鼠标移动 - 处理拖动和预览"""
        if self.current_tool == "select" and self.is_dragging:
            # 拖动模式：实时更新图形位置
            self.drag_shape_to(self._to_scene_point(event.pos()))
        elif self.current_tool == "polygon" and self.is_drawing_polygon:
            self.temp_end_point = self._to_scene_point(event.pos())
            self.update()
        elif self.start_point:
            self.temp_end_point = self._to_scene_point(event.pos())
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

    def _to_scene_point(self, device_pos):
        """将窗口坐标转换为场景坐标（考虑缩放）"""
        if self.scale_factor == 0:
            return device_pos
        return QPoint(int(device_pos.x() / self.scale_factor), int(device_pos.y() / self.scale_factor))

    def _get_rect(self, start, end):
        """根据起点终点计算矩形区域，返回QRect对象"""
        from PyQt5.QtCore import QRect
        x = min(start.x(), end.x())
        y = min(start.y(), end.y())
        width = abs(end.x() - start.x())
        height = abs(end.y() - start.y())
        return QRect(x, y, width, height)
    
    def select_shape_at_point(self, point):
        """选择指定点位置的图形"""
        # 先取消当前选择
        self.selected_shape_index = -1
        
        # 从后往前检查（后绘制的图形在上层）
        for i in range(len(self.shapes) - 1, -1, -1):
            shape = self.shapes[i]
            if ShapeUtils.is_point_in_shape(point, shape):
                self.selected_shape_index = i
                print(f"选中图形: {shape['tool']} (索引: {i})")
                self.update()
                return True
        
        print("未选中任何图形")
        self.update()
        return False
    
    def start_dragging(self, pos):
        """开始拖动准备"""
        if self.selected_shape_index != -1:
            self.is_dragging = True
            self.drag_start_point = pos
            self.original_shape_data = self.get_shape_copy(self.selected_shape_index)
            
            # 计算鼠标点击点与图形位置的偏移
            shape = self.shapes[self.selected_shape_index]
            shape_center = self.get_shape_center(shape)
            self.drag_offset = pos - shape_center
            
            print(f"开始拖动图形: {shape['tool']}")

    def drag_shape_to(self, pos):
        """将选中的图形拖动到指定位置"""
        if self.selected_shape_index == -1 or not self.original_shape_data:
            return
        
        # 计算新的中心位置
        new_center = pos - self.drag_offset
        self.update_shape_position(self.selected_shape_index, new_center)
        self.update()

    def update_shape_position(self, shape_index, new_center):
        """更新图形位置到新的中心点"""
        shape = self.shapes[shape_index]
        old_center = self.get_shape_center(self.original_shape_data)
        delta = new_center - old_center
        
        if shape['tool'] == 'line':
            shape['start'] = self.original_shape_data['start'] + delta
            shape['end'] = self.original_shape_data['end'] + delta
        elif shape['tool'] in ['rect', 'circle']:
            shape['start'] = self.original_shape_data['start'] + delta
            shape['end'] = self.original_shape_data['end'] + delta
        elif shape['tool'] == 'polygon':
            # 移动多边形的所有顶点
            shape['points'] = [
                point + delta for point in self.original_shape_data['points']
            ]

    

    def get_shape_copy(self, shape_index):
        """获取图形的深拷贝"""
        import copy
        shape = self.shapes[shape_index]
        
        if shape['tool'] == 'polygon':
            # 多边形需要特殊处理点列表
            return {
                'tool': shape['tool'],
                'points': [QPoint(p.x(), p.y()) for p in shape['points']],
                'color': shape['color'],
                'line_width': shape['line_width'],
                'fill_color': shape['fill_color']
            }
        else:
            return {
                'tool': shape['tool'],
                'start': QPoint(shape['start'].x(), shape['start'].y()),
                'end': QPoint(shape['end'].x(), shape['end'].y()),
                'color': shape['color'],
                'line_width': shape['line_width'],
                'fill_color': shape['fill_color']
            }

    def end_dragging(self):
        """结束拖动"""
        self.is_dragging = False
        self.drag_start_point = None
        self.drag_offset = QPoint(0, 0)
        self.original_shape_data = None
        print("拖动结束")
    
    def get_shape_center(self, shape):
        """获取图形的中心点"""
        return ShapeUtils.get_shape_center(shape)
    
    def cancel_polygon(self):
        """取消正在进行的多边形绘制"""
        self.is_drawing_polygon = False
        self.polygon_points = []
        self.temp_end_point = None
        self.update()

    def set_tool(self, tool_id):
        """设置当前工具"""
        # 如果切换到其他工具，取消选择状态
        if tool_id != "select":
            self.selected_shape_index = -1
            if self.is_dragging:
                self.end_dragging()

        # 如果切换到其他工具，取消正在进行的多边形绘制
        if tool_id != "polygon" and self.is_drawing_polygon:
            self.cancel_polygon()

        self.current_tool = tool_id
        self.update()

    # ===== 缩放相关 =====
    def wheelEvent(self, event):
        """滚轮缩放（以窗口左上角为原点进行缩放）"""
        delta = event.angleDelta().y()
        if delta == 0:
            return
        scale_step = 1.1 if delta > 0 else 1/1.1
        new_scale = max(self.min_scale, min(self.max_scale, self.scale_factor * scale_step))
        if abs(new_scale - self.scale_factor) > 1e-6:
            self.scale_factor = new_scale
            self.update()

    def zoom_in(self):
        self.scale_factor = min(self.max_scale, self.scale_factor * 1.1)
        self.update()

    def zoom_out(self):
        self.scale_factor = max(self.min_scale, self.scale_factor / 1.1)
        self.update()

    def zoom_reset(self):
        self.scale_factor = 1.0
        self.update()

    # ===== 导出图片 =====
    def export_image(self, file_path: str) -> bool:
        """将当前画布导出为图片文件（按当前视图效果导出）。
        支持常见格式：JPG、PNG等，依据文件后缀自动识别格式。
        """
        try:
            pixmap = self.grab()  # 截取当前部件内容（含缩放、预览、边框、状态文本）
            suffix = file_path.split('.')[-1].upper() if '.' in file_path else 'PNG'
            ok = pixmap.save(file_path, suffix)
            return bool(ok)
        except Exception:
            return False