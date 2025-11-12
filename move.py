import sys
import time
import traceback

from sdk.manipulators.medu import MEdu
from sdk.commands.move_coordinates_command import (
    MoveCoordinatesParamsPosition as Pos,
    MoveCoordinatesParamsOrientation as Ori,
    PlannerType,
)

HOST = "172.16.2.190"
CLIENT_ID = "move-test"
LOGIN = "user"
PASSWORD = "pass"

# Настройки движения
STEP_MM = 30.0           # на сколько сдвигать за один шаг
V_SCALE = 0.20           # 0..1 масштаб скорости для LIN
A_SCALE = 0.20           # 0..1 масштаб ускорения для LIN
PAUSE = 0.3

def get_current_pose(m: MEdu) -> tuple[Pos, Ori]:
    """Читаем текущую позу TCP через info.get_coordinates()."""
    data = m.info.get_coordinates(timeout_seconds=5)  # вернёт dict
    # ожидаем структуру: {"position":{"x":..,"y":..,"z":..},"orientation":{"x":..,"y":..,"z":..,"w":..}}
    p = data["position"]; q = data["orientation"]
    return Pos(p["x"], p["y"], p["z"]), Ori(q["x"], q["y"], q["z"], q["w"])

def move_to(m: MEdu, pos: Pos, ori: Ori):
    """Линейное перемещение в абсолютные координаты, ориентацию сохраняем."""
    m.move_to_coordinates(
        position=pos,
        orientation=ori,
        velocity_scaling_factor=V_SCALE,
        acceleration_scaling_factor=A_SCALE,
        planner_type=PlannerType.LIN,   # линейно по прямой
        timeout_seconds=20,
        throw_error=True
    )

def move_rel(m: MEdu, dx=0.0, dy=0.0, dz=0.0):
    """Относительное смещение на dx/dy/dz (мм)."""
    pos, ori = get_current_pose(m)
    target = Pos(pos.x + dx, pos.y + dy, pos.z + dz)
    move_to(m, target, ori)

def main():
    m = MEdu(HOST, CLIENT_ID, LOGIN, PASSWORD)
    connected = got_control = False
    try:
        print("[*] Подключение...")
        m.connect(); connected = True
        print("[+] Подключено")

        print("[*] Получаем управление...")
        m.get_control(); got_control = True
        print("[+] Управление получено")

        # (опционально) питание инструмента, если стоит приводной захват
        try: m.nozzle_power(True)
        except Exception: pass

        # Блок перемещений: вперёд/назад (X), вправо/влево (Y), вверх/вниз (Z)
        print("[→] Вперёд +X")
        move_rel(m, dx=+STEP_MM); time.sleep(PAUSE)

        print("[←] Назад -X")
        move_rel(m, dx=-STEP_MM); time.sleep(PAUSE)

        print("[→] Вправо +Y")
        move_rel(m, dy=+STEP_MM); time.sleep(PAUSE)

        print("[←] Влево -Y")
        move_rel(m, dy=-STEP_MM); time.sleep(PAUSE)

        print("[↑] Вверх +Z")
        move_rel(m, dz=+STEP_MM); time.sleep(PAUSE)

        print("[↓] Вниз -Z")
        move_rel(m, dz=-STEP_MM); time.sleep(PAUSE)

        print("[✓] Движения по осям выполнены")

    except Exception as e:
        print("[!] Ошибка:", e)
        traceback.print_exc()
    finally:
        try:
            if got_control:
                try: m.nozzle_power(False)
                except Exception: pass
        finally:
            try:
                if got_control: m.release_control()
            except Exception: pass
            try:
                if connected: m.disconnect()
            except Exception: pass

if __name__ == "__main__":
    print("ВНИМАНИЕ: освободите рабочую зону. Продолжить? [y/N] ", end="", flush=True)
    if sys.stdin.readline().strip().lower() == "y":
        main()
    else:
        print("Отмена.")
