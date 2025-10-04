# Примерная абстракция управления M Edu.
# Замените низкоуровневые вызовы на реальные функции вашего SDK/ПО.

from dataclasses import dataclass
import time
import math

@dataclass
class JointLimits:
    j1_min, j1_max = math.radians(-168), math.radians(168)
    j2_min, j2_max = math.radians(-88), math.radians(2)    # см. таблицу углов
    j3_min, j3_max = math.radians(55),  math.radians(144)
    j4_min, j4_max = math.radians(-88), math.radians(88)

class MEdu:
    def __init__(self):
        # Здесь инициализация связи: Ethernet/UART/SDK
        # self.dev = medu_sdk.connect("192.168.1.50")  # пример
        pass

    # --- Безопасность и сервис ---
    def home(self):
        """Поиск нулей по концевикам для J1..J4."""
        # self.dev.home_all()
        print("Homing J1..J4..."); time.sleep(2)

    def estop(self):
        """Аварийная остановка (снятие питания с приводов)."""
        # self.dev.estop()
        print("ESTOP!")

    # --- Кинематика/траектории ---
    def move_j(self, j1=None, j2=None, j3=None, j4=None, speed=0.5):
        """Перемещение в суставном пространстве (радианы)."""
        # Ограничим углы по допускам:
        jl = JointLimits()
        def clip(a, lo, hi): return max(lo, min(hi, a))
        if j1 is not None: j1 = clip(j1, jl.j1_min, jl.j1_max)
        if j2 is not None: j2 = clip(j2, jl.j2_min, jl.j2_max)
        if j3 is not None: j3 = clip(j3, jl.j3_min, jl.j3_max)
        if j4 is not None: j4 = clip(j4, jl.j4_min, jl.j4_max)
        # self.dev.joint_move(j1, j2, j3, j4, speed=speed)
        print(f"MoveJ: {j1, j2, j3, j4} @v={speed}")

    def move_l(self, x, y, z, yaw=0.0, speed=50):
        """Линейное перемещение (мм, рад). IK/планирование зависит от вашего SDK."""
        # self.dev.cartesian_move(x, y, z, yaw, speed=speed)
        print(f"MoveL: XYZ=({x:.1f},{y:.1f},{z:.1f}) yaw={yaw:.2f} @v={speed}mm/s")

    # --- Поворот инструмента (J4) ---
    def tool_rotate_deg(self, deg, speed=0.5):
        self.move_j(j4=math.radians(deg), speed=speed)

    # --- Механический хват (GP3) ---
    def gripper_close(self, pwm=0.8):
        """Сжатие когтей; pwm 0..1 — условный уровень."""
        # self.dev.gp3_pwm(channel="GRIP", value=pwm)
        print(f"Gripper CLOSE pwm={pwm}")

    def gripper_open(self, pwm=0.1):
        """Разжатие когтей."""
        # self.dev.gp3_pwm(channel="GRIP", value=pwm)
        print(f"Gripper OPEN pwm={pwm}")

    # --- Вакуумный хват (внешний блок: 12V OUT + TTL) ---
    def vacuum_on(self):
        """Включить насос (цифровой TTL) и подождать набор вакуума."""
        # self.dev.ttl_write("VACUUM_ENABLE", True)
        print("Vacuum ON"); time.sleep(0.3)

    def vacuum_off(self):
        """Выключить насос и сбросить давление."""
        # self.dev.ttl_write("VACUUM_ENABLE", False)
        print("Vacuum OFF")

    # --- Пишущий модуль (перо вниз/вверх = уровни Z) ---
    def pen_down(self, z_contact=-5.0):
        self.move_l(x=None, y=None, z=z_contact)  # В реале передайте текущие x,y из состояния

    def pen_up(self, z_safe=10.0):
        self.move_l(x=None, y=None, z=z_safe)

    # --- Лазер (через внешний блок и GP3/TTL) ---
    def laser_on(self, duty=0.3):
        """Включить лазер с ограничением мощности (через ШИМ/TTL). Работать только в очках!"""
        # self.dev.ttl_pwm("LASER", duty)
        print(f"LASER ON duty={duty}")

    def laser_off(self):
        # self.dev.ttl_pwm("LASER", 0.0)
        print("LASER OFF")
