import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QSlider, QLabel, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *

style_sheet = """
QMainWindow { background-color: #121212; }
QLabel { color: #E0E0E0; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; }
QFrame#ControlPanel { background-color: #1E1E1E; border-top: 2px solid #00ADB5; border-radius: 15px; }
QSlider::handle:horizontal { background: #00ADB5; width: 16px; height: 16px; border-radius: 8px; margin: -5px 0; }
QSlider::groove:horizontal { background: #393E46; height: 6px; border-radius: 3px; }
QSlider::handle:horizontal:hover { background: #00FFF5; }
"""

class Visualizer3D(QGLWidget):
    def __init__(self, parent=None):
        super(Visualizer3D, self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.rotX = 25.0
        self.rotY = 45.0
        self.zoom = -20.0
        self.lastPos = QPoint()
        
        # Параметри циліндра
        self.m, self.n = 2, 4
        self.R, self.L = 3.0, 10.0
        self.A1, self.A2, self.A3 = 0.1, 0.05, 0.5
        self.anim_speed = 1.0
        
        # Час для анімації
        self.time = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16) # ~60 FPS

    def update_animation(self):
        """Оновлення часу для створення ефекту вібрації"""
        self.time += 0.05 * self.anim_speed
        self.update() 

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST) 
        glClearColor(0.05, 0.05, 0.05, 1.0) # Темно-сірий фон

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h, 0.1, 100.0)

    def get_vertex_and_color(self, i, j, rows, cols):
        """Обчислює 3D координати точки та її колір (напруження)"""
        x = (i / rows) * self.L
        theta = (j / cols) * 2 * math.pi
        s = self.R * theta
        
        # Формули з методички
        arg_x = (math.pi * self.m * x) / self.L
        arg_s = (math.pi * self.n * s) / self.R
        
        # Фактор часу створює стоячу хвилю
        t_factor = math.sin(self.time)
        
        u1 = self.A1 * math.cos(arg_x) * math.cos(arg_s) * t_factor
        u2 = self.A2 * math.sin(arg_x) * math.sin(arg_s) * t_factor
        w  = self.A3 * math.sin(arg_x) * math.cos(arg_s) * t_factor
        
        # Фінальні координати
        X = (x - self.L/2) + u1
        Y = (self.R + w) * math.cos(theta) - u2 * math.sin(theta)
        Z = (self.R + w) * math.sin(theta) + u2 * math.cos(theta)
        
        # --- КОЛЬОРОВА КАРТА (Heatmap) ---
        # Обчислюємо відносне зміщення (від 0 до 1)
        # Додаємо 0.001, щоб уникнути ділення на нуль
        intensity = abs(w) / (self.A3 + 0.001) 
        intensity = max(0.0, min(1.0, intensity))
        
        # Градієнт: Синій (мінімум) -> Зелений -> Червоний (максимум)
        r = intensity
        g = 1.0 - abs(intensity - 0.5) * 2.0
        b = 1.0 - intensity
        
        return (X, Y, Z), (r, g, b)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Позиціонування камери
        glTranslate(0, 0, self.zoom)
        glRotate(self.rotX, 1, 0, 0)
        glRotate(self.rotY, 0, 1, 0)

        # Малюємо осі (X - червона, Y - зелена, Z - синя)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(6, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 6, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 6)
        glEnd()

        # --- МАЛЮВАННЯ ЦИЛІНДРА ---
        rows, cols = 30, 50 # Роздільна здатність сітки
        
        # Малюємо суцільну поверхню з градієнтом
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        for i in range(rows):
            glBegin(GL_QUAD_STRIP)
            for j in range(cols + 1):
                # Вершина поточного ряду
                v1, c1 = self.get_vertex_and_color(i, j, rows, cols)
                glColor3f(*c1); glVertex3f(*v1)
                
                # Вершина наступного ряду (щоб замкнути квадрат)
                v2, c2 = self.get_vertex_and_color(i + 1, j, rows, cols)
                glColor3f(*c2); glVertex3f(*v2)
            glEnd()

        # Додаємо чорну сітку поверх для кращого сприйняття форми (Wireframe)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glColor3f(0.0, 0.0, 0.0) # Чорні лінії
        # Використовуємо невеликий зсув, щоб лінії не зливалися з поверхнею
        glEnable(GL_POLYGON_OFFSET_LINE)
        glPolygonOffset(-1.0, -1.0)
        for i in range(rows):
            glBegin(GL_QUAD_STRIP)
            for j in range(cols + 1):
                v1, _ = self.get_vertex_and_color(i, j, rows, cols)
                glVertex3f(*v1)
                v2, _ = self.get_vertex_and_color(i + 1, j, rows, cols)
                glVertex3f(*v2)
            glEnd()
        glDisable(GL_POLYGON_OFFSET_LINE)

    # --- УПРАВЛІННЯ КАМЕРОЮ ---
    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()
        if event.buttons() & Qt.LeftButton:
            self.rotX += dy * 0.5
            self.rotY += dx * 0.5
        self.lastPos = event.pos()
        self.update()

    def wheelEvent(self, event):
        self.zoom += event.angleDelta().y() / 120
        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Моделювання форм коливань циліндра")
        self.resize(1100, 850)
        self.setStyleSheet(style_sheet)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.viz = Visualizer3D()
        layout.addWidget(self.viz, stretch=4)

        # --- ПАНЕЛЬ УПРАВЛІННЯ ---
        panel = QFrame(); panel.setObjectName("ControlPanel")
        grid = QGridLayout(panel)
        grid.setSpacing(15)
        
        # Додаємо елементи управління
        self.add_control(grid, "Півхвилі по довжині (m):", 1, 10, 2, 0, 0, 'm')
        self.add_control(grid, "Хвилі по колу (n):", 0, 10, 4, 0, 1, 'n')
        self.add_control(grid, "Радіус оболонки (R):", 10, 100, 30, 0, 2, 'R', div=10)
        
        self.add_control(grid, "Амплітуда A1 (Вісь X):", 0, 50, 5, 1, 0, 'A1', div=10)
        self.add_control(grid, "Амплітуда A2 (Коло):", 0, 50, 5, 1, 1, 'A2', div=10)
        self.add_control(grid, "Амплітуда A3 (Радіус):", 0, 50, 10, 1, 2, 'A3', div=10)
        
        self.add_control(grid, "Швидкість анімації:", 0, 50, 10, 2, 1, 'anim_speed', div=10)

        layout.addWidget(panel, stretch=1)

    def add_control(self, grid, label_text, min_v, max_v, def_v, r, c, param_name, div=1):
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        
        lbl = QLabel(f"{label_text} {def_v/div}")
        sld = QSlider(Qt.Horizontal)
        sld.setMinimum(min_v); sld.setMaximum(max_v); sld.setValue(def_v)
        
        def update_val(v):
            val = v / div
            lbl.setText(f"{label_text} {val}")
            setattr(self.viz, param_name, val)
            
        sld.valueChanged.connect(update_val)
        lay.addWidget(lbl); lay.addWidget(sld)
        grid.addWidget(container, r, c)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())