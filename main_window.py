from PyQt5.QtWidgets import (QMainWindow, QToolBar, QPushButton, 
                             QLabel, QSpinBox, QColorDialog, 
                             QFileDialog, QMessageBox)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import json
from drawing_widget import DrawingWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Drawing App")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: lightgray;")
        # 创建菜单栏
        self.create_menu()
        # 创建工具栏
        self.create_toolbar()

        # 创建画布实例
        self.drawing_widget = DrawingWidget()
        self.setCentralWidget(self.drawing_widget)

    def create_toolbar(self):
        toolbar = QToolBar("绘图工具")
        self.addToolBar(toolbar)
        tools = ["直线", "矩形", "圆形", "多边形"]
        for tname in tools:
            btn = QPushButton(tname)
            # 连接点击信号到处理函数
            btn.clicked.connect(lambda checked, tool=tname: self.set_current_tool(tool))
            toolbar.addWidget(btn)

        toolbar.addSeparator()
        # 添加颜色选择按钮
        color_btn = QPushButton("颜色")
        color_btn.clicked.connect(self.select_color)
        toolbar.addWidget(color_btn)
        # 添加线宽选择按钮
        toolbar.addWidget(QLabel("线宽:"))
        self.width_spin = QSpinBox()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10)  # 线宽范围1-10
        self.width_spin.setValue(2)
        self.width_spin.valueChanged.connect(self.set_line_width)
        toolbar.addWidget(self.width_spin)

    def set_current_tool(self, tname):
        tool_map = {
            "直线": "line",
            "矩形": "rect",
            "圆形": "circle",
            "多边形": "polygon"
        }
        tool_id = tool_map.get(tname, "line")
        print(f"当前选择的工具：{tname}")

        # 更新画布的当前工具
        self.drawing_widget.current_tool = tool_id
        self.drawing_widget.update()  # 触发重绘

    def select_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.drawing_widget.current_color = color
            print(f"选择的颜色：{color.name()}")

    def set_line_width(self, width):
        self.drawing_widget.current_line_width = width
        print(f"设置线宽为：{width}")

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        # 保存动作
        save_action = file_menu.addAction("保存")
        save_action.triggered.connect(self.save_drawing)
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