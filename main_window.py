from PyQt5.QtWidgets import (QMainWindow, QToolBar, QPushButton, 
                             QLabel, QSpinBox, QColorDialog, 
                             QFileDialog, QMessageBox, QInputDialog)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import json
from drawing_widget import DrawingWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Drawing App")
        self.setGeometry(100, 100, 1200, 800)
        # 简单全局样式，美化窗口与工具栏（测试用）
        self.setStyleSheet("""
        QMainWindow { background-color: #f5f7fa; }
        QToolBar { background: #ffffff; spacing:6px; padding:6px; border: 1px solid #e1e4e8; }
        /* 浅蓝色主题：更柔和，便于测试 */
        QPushButton { background: #64B5F6; color: white; padding:6px 10px; border-radius:6px; }
        QPushButton:hover { background: #42A5F5; }
        QPushButton:pressed { background: #1E88E5; }
        QSpinBox { padding:4px; }
        """)
        # 创建菜单栏
        self.create_menu()
        # 创建画布实例（需先创建，再创建工具栏以绑定缩放按钮）
        self.drawing_widget = DrawingWidget()
        self.setCentralWidget(self.drawing_widget)

        # 创建工具栏
        self.create_toolbar()

    def create_toolbar(self):
        toolbar = QToolBar("绘图工具")
        self.addToolBar(toolbar)
        
        # 基本工具
        basic_tools = ["选择","直线", "矩形", "圆形", "多边形"]
        for tname in basic_tools:
            btn = QPushButton(tname)
            btn.clicked.connect(lambda checked, tool=tname: self.set_current_tool(tool))
            btn.setToolTip(tname)
            btn.setFixedHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            toolbar.addWidget(btn)

        toolbar.addSeparator()
        
        # 曲线工具
        curve_tools = ["Bézier曲线", "B样条曲线"]
        for tname in curve_tools:
            btn = QPushButton(tname)
            btn.clicked.connect(lambda checked, tool=tname: self.set_current_tool(tool))
            btn.setToolTip(tname)
            btn.setFixedHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            toolbar.addWidget(btn)
        
        toolbar.addSeparator()
        
        # 曲面工具
        surface_btn = QPushButton("Bézier曲面")
        surface_btn.clicked.connect(lambda: self.set_current_tool("Bézier曲面"))
        surface_btn.setToolTip("创建Bézier曲面")
        surface_btn.setFixedHeight(30)
        surface_btn.setCursor(Qt.PointingHandCursor)
        toolbar.addWidget(surface_btn)
        
        # 曲面显示模式切换
        wireframe_btn = QPushButton("网格线")
        wireframe_btn.clicked.connect(lambda: self.set_surface_display_mode('wireframe'))
        wireframe_btn.setFixedHeight(30)
        toolbar.addWidget(wireframe_btn)
        
        filled_btn = QPushButton("填充")
        filled_btn.clicked.connect(lambda: self.set_surface_display_mode('filled'))
        filled_btn.setFixedHeight(30)
        toolbar.addWidget(filled_btn)
        
        toolbar.addSeparator()
        
        # 变换工具
        transform_tools = [("平移", "translate"), ("旋转", "rotate"), ("缩放", "scale")]
        for tname, ttype in transform_tools:
            btn = QPushButton(tname)
            btn.clicked.connect(lambda checked, t=ttype: self.apply_transform(t))
            btn.setFixedHeight(30)
            toolbar.addWidget(btn)
        
        toolbar.addSeparator()
        
        # 缩放控制
        zoom_in_btn = QPushButton("放大")
        zoom_in_btn.clicked.connect(self.drawing_widget.zoom_in)
        toolbar.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("缩小")
        zoom_out_btn.clicked.connect(self.drawing_widget.zoom_out)
        toolbar.addWidget(zoom_out_btn)

        toolbar.addSeparator()
        
        # 颜色和线宽
        color_btn = QPushButton("边框颜色")
        color_btn.clicked.connect(self.select_color)
        color_btn.setFixedHeight(30)
        toolbar.addWidget(color_btn)
        
        fill_color_btn = QPushButton("填充颜色")
        fill_color_btn.clicked.connect(self.select_fill_color)
        fill_color_btn.setFixedHeight(30)
        toolbar.addWidget(fill_color_btn)
        
        toolbar.addWidget(QLabel("线宽:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10)
        self.width_spin.setValue(2)
        self.width_spin.valueChanged.connect(self.set_line_width)
        self.width_spin.setFixedWidth(60)
        toolbar.addWidget(self.width_spin)

        self.statusBar().showMessage("就绪")

    def set_current_tool(self, tname):
        tool_map = {
            "选择": "select",
            "直线": "line", 
            "矩形": "rect",
            "圆形": "circle",
            "多边形": "polygon",
            "Bézier曲线": "bezier_curve",
            "B样条曲线": "bspline_curve",
            "Bézier曲面": "bezier_surface"
        }
        tool_id = tool_map.get(tname, "select")

        # 设置曲线类型
        if tool_id == "bezier_curve":
            self.drawing_widget.curve_type = 'bezier'
        elif tool_id == "bspline_curve":
            self.drawing_widget.curve_type = 'bspline'

        self.drawing_widget.set_tool(tool_id)
        self.statusBar().showMessage(f"当前工具: {tname}")
    
    def set_surface_display_mode(self, mode):
        """设置曲面显示模式"""
        self.drawing_widget.surface_display_mode = mode
        if self.drawing_widget.selected_shape_index >= 0:
            shape = self.drawing_widget.shapes[self.drawing_widget.selected_shape_index]
            if shape['tool'] == 'bezier_surface':
                shape['display_mode'] = mode
                self.drawing_widget.update()
        mode_name = "网格线" if mode == "wireframe" else "填充"
        self.statusBar().showMessage(f"曲面显示: {mode_name}")
    
    def apply_transform(self, transform_type):
        """应用变换到选中的图形"""
        from PyQt5.QtWidgets import QInputDialog
        
        if self.drawing_widget.selected_shape_index < 0:
            QMessageBox.warning(self, "提示", "请先选择一个图形")
            return
        
        if transform_type == 'translate':
            dx, ok1 = QInputDialog.getInt(self, "平移", "X方向偏移量:", 20, -1000, 1000)
            if not ok1:
                return
            dy, ok2 = QInputDialog.getInt(self, "平移", "Y方向偏移量:", 20, -1000, 1000)
            if not ok2:
                return
            self.drawing_widget.apply_transform_to_selected('translate', dx=dx, dy=dy)
        elif transform_type == 'rotate':
            angle, ok = QInputDialog.getDouble(self, "旋转", "旋转角度(度):", 15, -360, 360, 1)
            if not ok:
                return
            self.drawing_widget.apply_transform_to_selected('rotate', angle=angle)
        elif transform_type == 'scale':
            sx, ok1 = QInputDialog.getDouble(self, "缩放", "X方向缩放比例:", 1.2, 0.1, 10.0, 2)
            if not ok1:
                return
            sy, ok2 = QInputDialog.getDouble(self, "缩放", "Y方向缩放比例:", 1.2, 0.1, 10.0, 2)
            if not ok2:
                return
            self.drawing_widget.apply_transform_to_selected('scale', sx=sx, sy=sy)
        
        transform_name = {"translate": "平移", "rotate": "旋转", "scale": "缩放"}
        self.statusBar().showMessage(f"已应用{transform_name[transform_type]}")

    def select_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.drawing_widget.current_color = color
            self.statusBar().showMessage(f"边框颜色: {color.name()}")

    def set_line_width(self, width):
        self.drawing_widget.current_line_width = width
        self.statusBar().showMessage(f"线宽: {width}")

    def select_fill_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.drawing_widget.current_fill_color = color
            self.statusBar().showMessage(f"填充颜色: {color.name()}")

    def set_no_fill(self):
        self.drawing_widget.current_fill_color = None


    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        # 保存动作
        save_action = file_menu.addAction("保存")
        save_action.triggered.connect(self.save_drawing)
        # 导出图片
        export_action = file_menu.addAction("导出图片")
        export_action.triggered.connect(self.export_image)
        # 打开动作
        open_action = file_menu.addAction("打开")
        open_action.triggered.connect(self.open_drawing)

        file_menu.addSeparator()

        # 退出动作
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)

    def save_drawing(self):
        file_path = QFileDialog.getSaveFileName(self, "保存绘图", "", "JSON Files (*.json);;All Files (*)")[0]
        if file_path:
            try:
                save_data = {
                    "shapes": []
                }
                # 转换图形数据为可序列化的格式
                for shape in self.drawing_widget.shapes:
                    if shape["tool"] == "polygon":
                        serializable_shape = {
                            "tool": shape["tool"],
                            "points": [{"x": p.x(), "y": p.y()} for p in shape["points"]],
                            "color": shape["color"].name(),
                            "line_width": shape["line_width"],
                            "fill_color": shape["fill_color"].name() if shape["fill_color"] else None
                        }
                        save_data["shapes"].append(serializable_shape)
                    else:
                        serializable_shape = {
                            "tool": shape["tool"],
                            "start_x": shape["start"].x(),
                            "start_y": shape["start"].y(),
                            "end_x": shape["end"].x(),
                            "end_y": shape["end"].y(),
                            "color": shape["color"].name(),
                            "line_width": shape["line_width"],
                            "fill_color": shape["fill_color"].name() if shape["fill_color"] else None
                        }
                        save_data["shapes"].append(serializable_shape)
                # 保存为 JSON 文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "保存成功", "绘图已成功保存！")

            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存绘图时出错: {e}")

    def open_drawing(self):
        """从文件打开绘图"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开绘图", "", "JSON Files (*.json);;All Files (*)"
        )
    
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    save_data = json.load(f)
                
                # 清空当前画布
                self.drawing_widget.shapes = []
                
                # 重新创建图形对象
                for shape_data in save_data["shapes"]:
                    if shape_data.get("tool") == "polygon":
                        shape = {
                            "tool": "polygon",
                            "points": [
                                self.drawing_widget._point(pt["x"], pt["y"]) for pt in shape_data.get("points", [])
                            ],
                            "color": QColor(shape_data["color"]),
                            "line_width": shape_data["line_width"],
                            "fill_color": QColor(shape_data["fill_color"]) if shape_data["fill_color"] else None
                        }
                        self.drawing_widget.shapes.append(shape)
                    else:
                        shape = {
                            "tool": shape_data["tool"],
                            "start": self.drawing_widget._point(shape_data["start_x"], shape_data["start_y"]),
                            "end": self.drawing_widget._point(shape_data["end_x"], shape_data["end_y"]),
                            "color": QColor(shape_data["color"]),
                            "line_width": shape_data["line_width"],
                            "fill_color": QColor(shape_data["fill_color"]) if shape_data["fill_color"] else None
                        }
                        self.drawing_widget.shapes.append(shape)
                
                # 更新画布
                self.drawing_widget.update()
                QMessageBox.information(self, "成功", "绘图已加载！")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败：{str(e)}")

    def export_image(self):
        """导出当前画布为图片文件（JPG/PNG等）"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出图片",
            "",
            "Image Files (*.jpg *.jpeg *.png *.bmp);;All Files (*)"
        )
        if not file_path:
            return
        ok = self.drawing_widget.export_image(file_path)
        if ok:
            QMessageBox.information(self, "成功", "图片导出成功！")
        else:
            QMessageBox.critical(self, "失败", "图片导出失败。")