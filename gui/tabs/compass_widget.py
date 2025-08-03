from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient, QBrush
from PyQt5.QtCore import Qt, QPointF
import math

class CompassWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.heading = 0  # Degrees
        self.setMinimumSize(160, 160)

    def set_heading(self, heading):
        self.heading = heading % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2 - 12

        # --- Gradient Glossy Background ---
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0, QColor(50, 50, 50))
        gradient.setColorAt(1, QColor(20, 20, 20))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawEllipse(center, radius, radius)

        # --- Outer Ring ---
        painter.setPen(QPen(QColor(180, 180, 180), 2))
        painter.drawEllipse(center, radius, radius)

        # --- Tick Marks ---
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x1 = center.x() + (radius - 12) * math.cos(rad)
            y1 = center.y() + (radius - 12) * math.sin(rad)
            x2 = center.x() + radius * math.cos(rad)
            y2 = center.y() + radius * math.sin(rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # --- Cardinal Directions ---
        directions = ['N', 'E', 'S', 'W']
        for i, d in enumerate(directions):
            angle = i * 90
            rad = math.radians(angle)
            tx = center.x() + (radius - 26) * math.cos(rad)
            ty = center.y() + (radius - 26) * math.sin(rad)
            painter.setFont(QFont('Segoe UI', 10, QFont.Bold))
            painter.setPen(QColor(255, 255, 255) if d != 'N' else QColor(255, 100, 100))
            painter.drawText(QPointF(tx - 6, ty + 6), d)

        # --- Compass Needle with Glow ---
        rad = math.radians(-self.heading + 90)
        x = center.x() + (radius - 20) * math.cos(rad)
        y = center.y() - (radius - 20) * math.sin(rad)
        painter.setPen(QPen(QColor(255, 60, 60), 3))
        painter.drawLine(center, QPointF(x, y))

        # --- Center Hub ---
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(Qt.darkGray, 1))
        painter.drawEllipse(center, 5, 5)

        # --- Heading Text ---
        painter.setPen(Qt.white)
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        painter.drawText(rect.adjusted(0, 0, 0, -8), Qt.AlignBottom | Qt.AlignHCenter, f"Heading: {int(self.heading)}°")
