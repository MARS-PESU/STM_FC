from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QTransform
from PyQt5.QtCore import Qt, QRect

class AttitudeIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.roll = 0
        self.pitch = 0

    def set_attitude(self, roll, pitch):
        self.roll = roll
        self.pitch = pitch
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2

        # Save original painter state
        painter.save()

        # Apply roll transformation
        transform = QTransform()
        transform.translate(center_x, center_y)
        transform.rotate(-self.roll)
        painter.setTransform(transform)

        # Sky
        painter.setBrush(QColor("#87ceeb"))
        painter.setPen(Qt.NoPen)
        horizon_height = self.pitch * 2
        painter.drawRect(QRect(-rect.width(), -rect.height() + int(horizon_height),
                               rect.width() * 2, rect.height() * 2))

        # Ground
        painter.setBrush(QColor("#d2b48c"))
        painter.drawRect(QRect(-rect.width(), int(horizon_height),
                               rect.width() * 2, rect.height()))

        # Horizon line
        pen = QPen(Qt.white, 2)
        painter.setPen(pen)
        painter.drawLine(-rect.width(), int(horizon_height),
                         rect.width(), int(horizon_height))

        painter.restore()

        # Draw outer frame
        pen = QPen(Qt.gray, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect.center(), min(center_x, center_y) - 5, min(center_x, center_y) - 5)

        # Draw fixed aircraft symbol
        painter.setPen(QPen(Qt.red, 2))
        painter.drawLine(center_x - 20, center_y, center_x + 20, center_y)
        painter.drawLine(center_x, center_y - 20, center_x, center_y + 20)
