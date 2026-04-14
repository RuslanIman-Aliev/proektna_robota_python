import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QSlider, QLabel, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *

style_sheet = """
QMainWindow { background-color: #121212; }
QLabel { color: #E0E0E0; font-family: 'Segoe UI'; font-size: 13px; }
QFrame#ControlPanel { background-color: #1E1E1E; border-top: 1px solid #333; border-radius: 15px; }
QSlider::handle:horizontal { background: #00ADB5; width: 16px; height: 16px; border-radius: 8px; margin: -5px 0; }
QSlider::groove:horizontal { background: #393E46; height: 6px; border-radius: 3px; }
"""

class Visualizer3D(QGLWidget):
    def __init__(self, parent=None):
        super(Visualizer3D, self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.rotX = 25
        self.rotY = 45
        self.zoom = -15.0
        self.lastPos = QPoint()
        
        self.m, self.n = 2, 4
        self.R, self.L = 3.0, 10.0
        self.A1, self.A2, self.A3 = 0.1, 0.05, 0.5

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.07, 0.07, 0.07, 1.0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h, 0.1, 100.0)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glTranslate(0, 0, self.zoom)
        glRotate(self.rotX, 1, 0, 0)
        glRotate(self.rotY, 0, 1, 0)

        self.draw_axes()
        self.draw_cylinder()

    def draw_axes(self):
        """Отрисовка осей координат"""
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(5, 0, 0) # X
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 5, 0) # Y
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 5) # Z
        glEnd()

    def draw_cylinder(self):
        """Отрисовка деформированного цилиндра по формулам"""
        rows, cols = 40, 60 
        glColor4f(0.0, 0.67, 0.7, 0.6) 
        
        for i in range(rows):
            glBegin(GL_LINE_STRIP)
            for j in range(cols + 1):
                x = (i / rows) * self.L
                theta = (j / cols) * 2 * math.pi
                s = self.R * theta
                
                arg_x = (math.pi * self.m * x) / self.L
                arg_s = (math.pi * self.n * s) / self.R
                
                u1 = self.A1 * math.cos(arg_x) * math.cos(arg_s)
                u2 = self.A2 * math.sin(arg_x) * math.sin(arg_s)
                w  = self.A3 * math.sin(arg_x) * math.cos(arg_s)
                
                X_final = (x - self.L/2) + u1
                Y_final = (self.R + w) * math.cos(theta) - u2 * math.sin(theta)
                Z_final = (self.R + w) * math.sin(theta) + u2 * math.cos(theta)
                
                glVertex3f(X_final, Y_final, Z_final)
            glEnd()

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
        self.resize(1000, 800)
        self.setStyleSheet(style_sheet)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.viz = Visualizer3D()
        layout.addWidget(self.viz, stretch=5)

        panel = QFrame(); panel.setObjectName("ControlPanel")
        grid = QGridLayout(panel)
        
        self.add_control(grid, "Півхвилі по довжині (m):", 1, 10, 2, 0, 0, 'm')
        self.add_control(grid, "Хвилі по колу (n):", 0, 10, 4, 0, 1, 'n')
        self.add_control(grid, "Радіус оболонки (R):", 1, 10, 3, 0, 2, 'R')
        self.add_control(grid, "Амплітуда A1 (x10):", 0, 20, 1, 1, 0, 'A1', div=10)
        self.add_control(grid, "Амплітуда A2 (x10):", 0, 20, 1, 1, 1, 'A2', div=10)
        self.add_control(grid, "Амплітуда A3 (x10):", 0, 20, 5, 1, 2, 'A3', div=10)

        layout.addWidget(panel, stretch=1)

    def add_control(self, grid, label_text, min_v, max_v, def_v, r, c, param_name, div=1):
        container = QWidget()
        lay = QVBoxLayout(container)
        lbl = QLabel(f"{label_text} {def_v/div}")
        sld = QSlider(Qt.Horizontal)
        sld.setMinimum(min_v); sld.setMaximum(max_v); sld.setValue(def_v)
        
        def update_val(v):
            val = v / div
            lbl.setText(f"{label_text} {val}")
            setattr(self.viz, param_name, val)
            self.viz.update()
            
        sld.valueChanged.connect(update_val)
        lay.addWidget(lbl); lay.addWidget(sld)
        grid.addWidget(container, r, c)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow(); window.show()
    sys.exit(app.exec_())