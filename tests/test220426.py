import sys
import random
import pymunk
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, QTimer, Qt
from PySide6.QtGui import QVector3D


class PhysicsEngine:
    def __init__(self, width, height):
        self.space = pymunk.Space()
        # Дампинг 0.5 означает, что каждую секунду объект теряет часть скорости.
        # Это заставляет кубик плавно останавливаться (эффект трения о стол).
        self.space.damping = 0.6
        
        # Стенки (делаем их менее прыгучими)
        static_lines = [
            pymunk.Segment(self.space.static_body, (0, 0), (width, 0), 10),
            pymunk.Segment(self.space.static_body, (width, 0), (width, height), 10),
            pymunk.Segment(self.space.static_body, (width, height), (0, height), 10),
            pymunk.Segment(self.space.static_body, (0, height), (0, 0), 10)
        ]
        for line in static_lines:
            line.elasticity = 0.4  # Меньше прыгучести у бортов
            line.friction = 1.0
        self.space.add(*static_lines)
    
    def create_dice(self, x, y):
        mass = 2  # Сделаем кубик тяжелее
        moment = pymunk.moment_for_box(mass, (60, 60))
        body = pymunk.Body(mass, moment)
        body.position = x, y
        
        shape = pymunk.Poly.create_box(body, (60, 60))
        shape.elasticity = 0.3  # Кубик не должен прыгать как резиновый
        shape.friction = 0.8
        
        self.space.add(body, shape)
        return body
    
    # --- В MainWindow ---
    
    def throw_dice(self):
        if self.dice_body:
            # Очищаем старые формы перед новым броском
            for s in self.dice_body.shapes:
                self.physics.space.remove(s)
            self.physics.space.remove(self.dice_body)
        
        self.dice_body = self.physics.create_dice(512, 384)
        
        # Случайный начальный импульс (не слишком сильный)
        force = (random.uniform(-800, 800), random.uniform(-800, 800))
        self.dice_body.apply_impulse_at_local_point(force)
        self.dice_body.angular_velocity = random.uniform(-8, 8)
        
        # Плавное падение "от экрана"
        self.z_height = 400
        self.z_velocity = -10  # Мягкая начальная скорость вниз
    
    def update_physics(self):
        # Делаем несколько подшагов для плавности
        for _ in range(3):
            self.physics.space.step(1 / 180.0)
        
        if self.dice_body:
            root = self.overlay.rootObject()
            dice_qml = root.findChild(object, "fallingBody")
            
            if dice_qml:
                pos = self.dice_body.position
                
                # Имитация веса при прыжках по Z
                if self.z_height > 0:
                    self.z_velocity -= 0.5  # Ослабленная гравитация Z
                    self.z_height += self.z_velocity
                    
                    if self.z_height <= 0:
                        self.z_height = 0
                        # Коэффициент отскока: 0.4 (быстро гасит прыжки)
                        self.z_velocity = -self.z_velocity * 0.4
                        # При ударе о "стекло" немного гасим и горизонтальную скорость
                        self.dice_body.velocity *= 0.8
                        
                        # Постепенно замедляем вращение вручную, если оно слишком резкое
                self.dice_body.angular_velocity *= 0.98
                
                # Передача в QML
                dice_qml.setProperty("x", pos.x - 512)
                dice_qml.setProperty("y", -(pos.y - 384))
                dice_qml.setProperty("z", self.z_height)
                
                # Вращение теперь зависит от скорости движения для "катания"
                angle = self.dice_body.angle * 57.3
                # Добавляем наклон в сторону движения (эффект качения)
                tilt_x = self.dice_body.velocity.y * 0.05
                tilt_y = self.dice_body.velocity.x * 0.05
                dice_qml.setProperty("eulerRotation", QVector3D(angle + tilt_x, tilt_y, angle * 0.3))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(1024, 768)
        
        self.physics = PhysicsEngine(1024, 768)
        self.dice_body = None
        self.z_height = 0  # Имитация 3D высоты
        self.z_velocity = 0
        
        # UI
        self.central = QWidget()
        self.setCentralWidget(self.central)
        layout = QVBoxLayout(self.central)
        
        self.btn = QPushButton("БРОСИТЬ КУБИК")
        self.btn.clicked.connect(self.throw_dice)
        layout.addWidget(self.btn)
        
        self.overlay = QQuickWidget()
        self.overlay.setSource("test.qml")
        print(self.overlay.errors())
        self.overlay.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.overlay.setAttribute(Qt.WA_AlwaysStackOnTop)
        self.overlay.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay.setClearColor(Qt.transparent)
        layout.addWidget(self.overlay)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_physics)
        self.timer.start(16)
    
    def throw_dice(self):
        if self.dice_body:
            self.physics.space.remove(self.dice_body)
        
        # Спавним в центре
        self.dice_body = self.physics.create_dice(512, 384)
        
        # Импульс в 2D плоскости
        force = (random.uniform(-500, 500), random.uniform(-500, 500))
        self.dice_body.apply_impulse_at_local_point(force)
        self.dice_body.angular_velocity = random.uniform(-10, 10)
        
        # Имитация броска "в экран" (подбрасываем по Z)
        self.z_height = 500  # Высота над столом
        self.z_velocity = -15  # Скорость падения
    
    def update_physics(self):
        for _ in range(3):
            self.physics.space.step(1 / 180.0)
        
        if self.dice_body:
            root = self.overlay.rootObject()
            # Ищем наш загруженный MyCude
            dice_qml = root.findChild(object, "fallingBody")
            
            if dice_qml:
                pos = self.dice_body.position
                
                # 1. Обработка высоты (Z)
                if self.z_height > 0:
                    self.z_velocity -= 0.5
                    self.z_height += self.z_velocity
                    if self.z_height <= 0:
                        self.z_height = 0
                        self.z_velocity = -self.z_velocity * 0.4
                        
                        # 2. Плавное вращение
                # Используем угловую скорость из Pymunk для вращения по всем осям
                av = self.dice_body.angular_velocity * 57.3  # в градусы
                
                # Получаем текущие углы, чтобы плавно их наращивать
                current_rot = dice_qml.property("eulerRotation")
                
                # Если кубик еще движется, продолжаем вращение
                if self.dice_body.velocity.length > 10 or self.z_height > 0:
                    new_x = current_rot.x() + av * 0.5
                    new_y = current_rot.y() + av * 0.8
                    new_z = current_rot.z() + av
                else:
                    # Если почти остановился — плавно доводим до ближайшей грани (опционально)
                    new_x, new_y, new_z = current_rot.x(), current_rot.y(), current_rot.z()
                
                # Установка свойств
                dice_qml.setProperty("x", pos.x - 512)
                dice_qml.setProperty("y", -(pos.y - 384))
                dice_qml.setProperty("z", self.z_height)
                dice_qml.setProperty("eulerRotation", QVector3D(new_x, new_y, new_z))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())