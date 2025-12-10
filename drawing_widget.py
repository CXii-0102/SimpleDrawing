from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPolygon, QPixmap, QImage
from PyQt5.QtCore import Qt, QPoint
from shape_utils import ShapeUtils
from curve_algorithms import CurveAlgorithms
from surface_algorithms import SurfaceAlgorithms

class DrawingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1000, 700)
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
        
        # 曲线曲面专用状态
        self.curve_control_points = []  # 曲线控制点
        self.is_drawing_curve = False
        self.curve_type = 'bezier'  # 'bezier' 或 'bspline'
        self.curve_algorithm = 'bernstein'  # 'bernstein' 或 'de_casteljau'
        
        # 曲面控制网格
        self.surface_control_grid = []  # 二维控制点数组
        self.is_drawing_surface = False
        self.surface_type = 'bezier'  # 'bezier' 或 'triangular'
        self.surface_display_mode = 'wireframe'  # 'wireframe' 或 'filled'
        
        # 控制点拖拽
        self.dragging_control_point = None  # {'shape_index': int, 'point_index': int}
        self.control_point_radius = 5

        print("DrawingWidget initialized")

        # 视图缩放
        self.scale_factor = 1.0  # 画布缩放因子
        self.min_scale = 0.2
        self.max_scale = 5.0
        
        # 变换操作
        self.transform_mode = None

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
        elif self.current_tool in ['bezier_curve', 'bspline_curve'] and self.is_drawing_curve:
            self.draw_curve_preview(painter)
        elif self.start_point and self.temp_end_point:
            self.draw_temp_shape(painter)

        # 3. 绘制边框和状态
        painter.setPen(Qt.red)
        painter.drawRect(0, 0, int((self.width()-1)/self.scale_factor), int((self.height()-1)/self.scale_factor))
        
        status_text = f"当前工具：{self.current_tool}"
        if self.current_tool == "polygon" and self.is_drawing_polygon:
            status_text += f" (已添加{len(self.polygon_points)}个顶点，双击完成)"
        elif self.current_tool in ["bezier_curve", "bspline_curve"] and self.is_drawing_curve:
            status_text += f" (已添加{len(self.curve_control_points)}个控制点，双击完成)"
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
            elif shape['tool'] in ['bezier_curve', 'bspline_curve']:
                self.draw_curve(painter, shape, is_selected)
            elif shape['tool'] in ['bezier_surface']:
                self.draw_surface(painter, shape, is_selected)
                
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
    
    def draw_curve_preview(self, painter):
        """绘制曲线预览"""
        if len(self.curve_control_points) == 0:
            return
        
        # 保存原始状态
        painter.save()
        
        # 绘制控制多边形（虚线）
        pen = QPen(QColor(150, 150, 150), 1, Qt.DashLine)
        painter.setPen(pen)
        for i in range(len(self.curve_control_points) - 1):
            painter.drawLine(self.curve_control_points[i], self.curve_control_points[i + 1])
        
        # 如果有足够的控制点，绘制曲线预览
        if len(self.curve_control_points) >= 2:
            pen = QPen(self.current_color, self.current_line_width, Qt.DashLine)
            painter.setPen(pen)
            
            if self.curve_type == 'bezier':
                curve_points = CurveAlgorithms.bezier_curve_bernstein(self.curve_control_points, 50)
            else:  # bspline
                if len(self.curve_control_points) >= 4:
                    curve_points = CurveAlgorithms.b_spline_curve(self.curve_control_points, 3, 50)
                else:
                    curve_points = []
            
            for i in range(len(curve_points) - 1):
                painter.drawLine(curve_points[i], curve_points[i + 1])
        
        # 绘制控制点
        painter.setBrush(QBrush(QColor(0, 128, 255)))
        for cp in self.curve_control_points:
            painter.drawEllipse(cp, self.control_point_radius, self.control_point_radius)
        
        painter.restore()

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
            scene_pos = self._to_scene_point(event.pos())
            
            if self.current_tool == "select":
                # 先尝试选择控制点
                if self.selected_shape_index >= 0 and self.start_control_point_drag(scene_pos):
                    # 成功开始拖拽控制点
                    pass
                elif self.select_shape_at_point(scene_pos):
                    # 如果选中了图形，开始拖动准备
                    self.start_dragging(scene_pos)
            elif self.current_tool in ["bezier_curve", "bspline_curve"]:
                self.handle_curve_click(scene_pos)
            elif self.current_tool == "polygon":
                self.handle_polygon_click(scene_pos)
            else:
                self.handle_other_tools_click(scene_pos)

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
            if self.dragging_control_point:
                # 结束控制点拖拽
                self.end_control_point_drag()
            elif self.current_tool == "select" and self.is_dragging:
                # 结束图形拖动
                self.end_dragging()
            elif self.current_tool not in ["polygon", "bezier_curve", "bspline_curve"] and self.start_point:
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
        scene_pos = self._to_scene_point(event.pos())
        
        if self.dragging_control_point:
            # 拖拽控制点
            self.drag_control_point_to(scene_pos)
        elif self.current_tool == "select" and self.is_dragging:
            # 拖动模式：实时更新图形位置
            self.drag_shape_to(scene_pos)
        elif self.current_tool in ["bezier_curve", "bspline_curve"] and self.is_drawing_curve:
            self.temp_end_point = scene_pos
            self.update()
        elif self.current_tool == "polygon" and self.is_drawing_polygon:
            self.temp_end_point = scene_pos
            self.update()
        elif self.start_point:
            self.temp_end_point = scene_pos
            self.update()

    def mouseDoubleClickEvent(self, event):
        """双击完成多边形或曲线"""
        if event.button() == Qt.LeftButton:
            if self.current_tool == "polygon" and self.is_drawing_polygon:
                self.complete_polygon()
            elif self.current_tool in ["bezier_curve", "bspline_curve"] and self.is_drawing_curve:
                self.complete_curve()
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
        elif shape['tool'] in ['bezier_curve', 'bspline_curve']:
            # 曲线需要复制控制点
            return {
                'tool': shape['tool'],
                'control_points': [QPoint(p.x(), p.y()) for p in shape.get('control_points', [])],
                'color': shape['color'],
                'line_width': shape['line_width'],
                'fill_color': shape.get('fill_color'),
                'algorithm': shape.get('algorithm', 'bernstein'),
                'degree': shape.get('degree', 3),
                'show_control_points': shape.get('show_control_points', True)
            }
        elif shape['tool'] == 'bezier_surface':
            # 曲面需要复制控制网格
            control_grid_copy = []
            for row in shape.get('control_grid', []):
                control_grid_copy.append([QPoint(p.x(), p.y()) for p in row])
            return {
                'tool': shape['tool'],
                'control_grid': control_grid_copy,
                'color': shape['color'],
                'line_width': shape['line_width'],
                'fill_color': shape.get('fill_color'),
                'display_mode': shape.get('display_mode', 'wireframe'),
                'show_control_grid': shape.get('show_control_grid', True)
            }
        else:
            # 基本图形（line, rect, circle）
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
        
        # 如果切换到其他工具，取消正在进行的曲线绘制
        if tool_id not in ["bezier_curve", "bspline_curve"] and self.is_drawing_curve:
            self.reset_curve_state()

        self.current_tool = tool_id
        
        # 如果是曲面工具，直接创建曲面
        if tool_id == "bezier_surface":
            self.handle_surface_setup()
            # 切换回选择工具以便编辑
            self.current_tool = "select"
        
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
    
    # ===== 曲线绘制相关 =====
    def draw_curve(self, painter, shape, is_selected=False):
        """绘制参数曲线"""
        control_points = shape.get('control_points', [])
        if len(control_points) < 2:
            return
        
        # 计算曲线点
        curve_points = []
        if shape['tool'] == 'bezier_curve':
            algorithm = shape.get('algorithm', 'bernstein')
            if algorithm == 'de_casteljau':
                curve_points = CurveAlgorithms.bezier_curve_de_casteljau(control_points, 100)
            else:
                curve_points = CurveAlgorithms.bezier_curve_bernstein(control_points, 100)
        elif shape['tool'] == 'bspline_curve':
            degree = shape.get('degree', 3)
            # B样条曲线需要至少 degree+1 个控制点
            if len(control_points) >= degree + 1:
                curve_points = CurveAlgorithms.b_spline_curve(control_points, degree, 100)
            else:
                curve_points = []
        
        # 绘制曲线
        if len(curve_points) > 1:
            for i in range(len(curve_points) - 1):
                painter.drawLine(curve_points[i], curve_points[i + 1])
        
        # 绘制控制点和控制多边形
        if is_selected or shape.get('show_control_points', False):
            # 绘制控制多边形（虚线）
            old_pen = painter.pen()
            pen = QPen(QColor(150, 150, 150), 1, Qt.DashLine)
            painter.setPen(pen)
            for i in range(len(control_points) - 1):
                painter.drawLine(control_points[i], control_points[i + 1])
            painter.setPen(old_pen)
            
            # 绘制控制点
            for i, cp in enumerate(control_points):
                if is_selected and self.dragging_control_point and \
                   self.dragging_control_point.get('shape_index') == self.selected_shape_index and \
                   self.dragging_control_point.get('info', {}).get('point_index') == i:
                    painter.setBrush(QBrush(QColor(255, 0, 0)))
                else:
                    painter.setBrush(QBrush(QColor(0, 128, 255)))
                painter.drawEllipse(cp, self.control_point_radius, self.control_point_radius)
    
    def draw_surface(self, painter, shape, is_selected=False):
        """绘制参数曲面"""
        control_grid = shape.get('control_grid', [])
        if not control_grid or not control_grid[0]:
            return
        
        display_mode = shape.get('display_mode', 'wireframe')
        
        if shape['tool'] == 'bezier_surface':
            # 计算曲面
            surface_data = SurfaceAlgorithms.bezier_surface(control_grid, 20, 20)
            
            if display_mode == 'wireframe':
                # 绘制网格线
                old_pen = painter.pen()
                pen = QPen(shape['color'], shape['line_width'])
                painter.setPen(pen)
                
                # u方向的线
                for line in surface_data['u_lines']:
                    for i in range(len(line) - 1):
                        painter.drawLine(line[i], line[i + 1])
                
                # v方向的线
                for line in surface_data['v_lines']:
                    for i in range(len(line) - 1):
                        painter.drawLine(line[i], line[i + 1])
                
                painter.setPen(old_pen)
            
            elif display_mode == 'filled':
                # 填充模式
                points_grid = surface_data['points']
                fill_color1 = shape.get('fill_color', QColor(200, 200, 255))
                fill_color2 = QColor(255, 200, 200)
                
                # 绘制每个小四边形
                for i in range(len(points_grid) - 1):
                    for j in range(len(points_grid[0]) - 1):
                        p0 = points_grid[i][j]
                        p1 = points_grid[i + 1][j]
                        p2 = points_grid[i + 1][j + 1]
                        p3 = points_grid[i][j + 1]
                        
                        # 计算渐变颜色
                        t = i / (len(points_grid) - 1)
                        color = SurfaceAlgorithms.interpolate_color(fill_color1, fill_color2, t)
                        
                        painter.setBrush(QBrush(color))
                        painter.setPen(QPen(color, 1))
                        
                        # 绘制四边形（拆分成两个三角形）
                        polygon = QPolygon([p0, p1, p2, p3])
                        painter.drawPolygon(polygon)
        
        # 绘制控制网格
        if is_selected or shape.get('show_control_grid', False):
            old_pen = painter.pen()
            pen = QPen(QColor(100, 100, 100), 1, Qt.DotLine)
            painter.setPen(pen)
            
            # 绘制控制网格线
            for row in control_grid:
                for i in range(len(row) - 1):
                    painter.drawLine(row[i], row[i + 1])
            
            for j in range(len(control_grid[0])):
                for i in range(len(control_grid) - 1):
                    painter.drawLine(control_grid[i][j], control_grid[i + 1][j])
            
            # 绘制控制点
            for i, row in enumerate(control_grid):
                for j, cp in enumerate(row):
                    painter.setBrush(QBrush(QColor(255, 128, 0)))
                    painter.drawEllipse(cp, self.control_point_radius, self.control_point_radius)
            
            painter.setPen(old_pen)
    
    def handle_curve_click(self, pos):
        """处理曲线工具的点击"""
        if not self.is_drawing_curve:
            # 开始绘制新曲线
            self.is_drawing_curve = True
            self.curve_control_points = [pos]
            print(f"开始绘制曲线，添加控制点: {pos}")
        else:
            # 添加新控制点
            self.curve_control_points.append(pos)
            print(f"添加曲线控制点: {pos}, 总数: {len(self.curve_control_points)}")
        self.update()
    
    def complete_curve(self):
        """完成曲线绘制"""
        if self.is_drawing_curve and len(self.curve_control_points) >= 2:
            tool_name = f"{self.curve_type}_curve"
            curve_shape = {
                "tool": tool_name,
                "control_points": self.curve_control_points.copy(),
                "color": self.current_color,
                "line_width": self.current_line_width,
                "algorithm": self.curve_algorithm,
                "degree": 3,  # B样条次数
                "show_control_points": True
            }
            self.shapes.append(curve_shape)
            self.reset_curve_state()
            print(f"{tool_name}绘制完成")
        else:
            print("曲线至少需要2个控制点")
    
    def reset_curve_state(self):
        """重置曲线绘图状态"""
        self.is_drawing_curve = False
        self.curve_control_points = []
        self.update()
    
    def handle_surface_setup(self):
        """设置曲面控制网格"""
        # 创建一个4x4的控制网格（双三次Bézier曲面）
        rows = 4
        cols = 4
        spacing_x = 80
        spacing_y = 80
        start_x = 100
        start_y = 100
        
        self.surface_control_grid = []
        for i in range(rows):
            row = []
            for j in range(cols):
                x = start_x + j * spacing_x
                y = start_y + i * spacing_y
                row.append(QPoint(x, y))
            self.surface_control_grid.append(row)
        
        # 创建曲面形状
        surface_shape = {
            "tool": "bezier_surface",
            "control_grid": [row[:] for row in self.surface_control_grid],  # 深拷贝
            "color": self.current_color,
            "line_width": self.current_line_width,
            "fill_color": self.current_fill_color,
            "display_mode": self.surface_display_mode,
            "show_control_grid": True
        }
        self.shapes.append(surface_shape)
        print("Bézier曲面已创建")
        self.update()
    
    def find_control_point_at(self, pos, tolerance=8):
        """查找指定位置的控制点"""
        if self.selected_shape_index < 0 or self.selected_shape_index >= len(self.shapes):
            return None
        
        shape = self.shapes[self.selected_shape_index]
        
        # 检查曲线控制点
        if shape['tool'] in ['bezier_curve', 'bspline_curve']:
            control_points = shape.get('control_points', [])
            for i, cp in enumerate(control_points):
                dx = pos.x() - cp.x()
                dy = pos.y() - cp.y()
                if dx * dx + dy * dy <= tolerance * tolerance:
                    return {'type': 'curve', 'point_index': i}
        
        # 检查曲面控制点
        elif shape['tool'] == 'bezier_surface':
            control_grid = shape.get('control_grid', [])
            for i, row in enumerate(control_grid):
                for j, cp in enumerate(row):
                    dx = pos.x() - cp.x()
                    dy = pos.y() - cp.y()
                    if dx * dx + dy * dy <= tolerance * tolerance:
                        return {'type': 'surface', 'row': i, 'col': j}
        
        return None
    
    def start_control_point_drag(self, pos):
        """开始拖拽控制点"""
        cp_info = self.find_control_point_at(pos)
        if cp_info:
            self.dragging_control_point = {
                'shape_index': self.selected_shape_index,
                'info': cp_info
            }
            print(f"开始拖拽控制点: {cp_info}")
            return True
        return False
    
    def drag_control_point_to(self, pos):
        """将控制点拖拽到指定位置"""
        if not self.dragging_control_point:
            return
        
        shape_index = self.dragging_control_point['shape_index']
        cp_info = self.dragging_control_point['info']
        
        if shape_index < 0 or shape_index >= len(self.shapes):
            return
        
        shape = self.shapes[shape_index]
        
        if cp_info['type'] == 'curve':
            point_index = cp_info['point_index']
            if 'control_points' in shape and point_index < len(shape['control_points']):
                shape['control_points'][point_index] = pos
        
        elif cp_info['type'] == 'surface':
            row = cp_info['row']
            col = cp_info['col']
            if 'control_grid' in shape and row < len(shape['control_grid']) and col < len(shape['control_grid'][row]):
                shape['control_grid'][row][col] = pos
        
        self.update()
    
    def end_control_point_drag(self):
        """结束控制点拖拽"""
        if self.dragging_control_point:
            print("结束控制点拖拽")
            self.dragging_control_point = None
            self.update()
    
    # ===== 变换操作 =====
    def apply_transform_to_selected(self, transform_type, **params):
        """对选中的图形应用变换"""
        if self.selected_shape_index < 0 or self.selected_shape_index >= len(self.shapes):
            return
        
        shape = self.shapes[self.selected_shape_index]
        
        if transform_type == 'translate':
            dx = params.get('dx', 0)
            dy = params.get('dy', 0)
            self.translate_shape(shape, dx, dy)
        
        elif transform_type == 'rotate':
            angle = params.get('angle', 0)
            center = params.get('center', self.get_shape_center(shape))
            self.rotate_shape(shape, angle, center)
        
        elif transform_type == 'scale':
            sx = params.get('sx', 1.0)
            sy = params.get('sy', 1.0)
            center = params.get('center', self.get_shape_center(shape))
            self.scale_shape(shape, sx, sy, center)
        
        self.update()
    
    def translate_shape(self, shape, dx, dy):
        """平移图形"""
        delta = QPoint(dx, dy)
        
        if shape['tool'] in ['line', 'rect', 'circle']:
            shape['start'] = shape['start'] + delta
            shape['end'] = shape['end'] + delta
        
        elif shape['tool'] == 'polygon':
            shape['points'] = [p + delta for p in shape['points']]
        
        elif shape['tool'] in ['bezier_curve', 'bspline_curve']:
            shape['control_points'] = [p + delta for p in shape['control_points']]
        
        elif shape['tool'] == 'bezier_surface':
            new_grid = []
            for row in shape['control_grid']:
                new_grid.append([p + delta for p in row])
            shape['control_grid'] = new_grid
    
    def rotate_shape(self, shape, angle_deg, center):
        """旋转图形"""
        import math
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        def rotate_point(p, center, cos_a, sin_a):
            x = p.x() - center.x()
            y = p.y() - center.y()
            new_x = x * cos_a - y * sin_a
            new_y = x * sin_a + y * cos_a
            return QPoint(int(new_x + center.x()), int(new_y + center.y()))
        
        if shape['tool'] in ['line', 'rect', 'circle']:
            shape['start'] = rotate_point(shape['start'], center, cos_a, sin_a)
            shape['end'] = rotate_point(shape['end'], center, cos_a, sin_a)
        
        elif shape['tool'] == 'polygon':
            shape['points'] = [rotate_point(p, center, cos_a, sin_a) for p in shape['points']]
        
        elif shape['tool'] in ['bezier_curve', 'bspline_curve']:
            shape['control_points'] = [rotate_point(p, center, cos_a, sin_a) for p in shape['control_points']]
        
        elif shape['tool'] == 'bezier_surface':
            new_grid = []
            for row in shape['control_grid']:
                new_grid.append([rotate_point(p, center, cos_a, sin_a) for p in row])
            shape['control_grid'] = new_grid
    
    def scale_shape(self, shape, sx, sy, center):
        """缩放图形"""
        def scale_point(p, center, sx, sy):
            x = center.x() + (p.x() - center.x()) * sx
            y = center.y() + (p.y() - center.y()) * sy
            return QPoint(int(x), int(y))
        
        if shape['tool'] in ['line', 'rect', 'circle']:
            shape['start'] = scale_point(shape['start'], center, sx, sy)
            shape['end'] = scale_point(shape['end'], center, sx, sy)
        
        elif shape['tool'] == 'polygon':
            shape['points'] = [scale_point(p, center, sx, sy) for p in shape['points']]
        
        elif shape['tool'] in ['bezier_curve', 'bspline_curve']:
            shape['control_points'] = [scale_point(p, center, sx, sy) for p in shape['control_points']]
        
        elif shape['tool'] == 'bezier_surface':
            new_grid = []
            for row in shape['control_grid']:
                new_grid.append([scale_point(p, center, sx, sy) for p in row])
            shape['control_grid'] = new_grid