import time
from typing import Dict, Any

from sdk.commands.move_coordinates_command import (
    MoveCoordinatesParamsPosition,
    MoveCoordinatesParamsOrientation,
)
from sdk.manipulators.medu import MEdu

# ===================== ПОДКЛЮЧЕНИЕ =====================

HOST = "172.16.2.190"
CLIENT_ID = "test-client"
LOGIN = "user"
PASSWORD = "pass"

# Положение «открыть/закрыть» для механического захвата
GRIP_OPEN_ANGLE = 15
GRIP_CLOSE_ANGLE = 45
GRIP_ROTATION = 0

# Профиль движения
VEL = 0.2
ACC = 0.2

# === КООРДИНАТЫ (из твоего примера) ===
data: Dict[str, Dict[str, Dict[str, Any]]] = {
    "CELL_1": {
    "tool0": {
      "position": {
        "x": 0.3617882087218369,
        "y": 0.00508008432504984,
        "z": 0.17807452861550552
      },
      "orientation": {
        "x": 1.2604159540609968e-06,
        "y": -0.00010199221203390681,
        "z": 0.012356365568307135,
        "w": 0.9999236519984626
      }
    },
    "tool1": {
      "position": {
        "x": 0.36180431980029043,
        "y": 0.005080482575549211,
        "z": 0.09907453025933749
      },
      "orientation": {
        "x": 1.2604159540609968e-06,
        "y": -0.00010199221203390681,
        "z": 0.012356365568307135,
        "w": 0.9999236519984626
      }
    }
  },
  "CELL_2": {
    "tool0": {
      "position": {
        "x": 0.2732234245153105,
        "y": 0.005734009737968053,
        "z": 0.17795862212439406
      },
      "orientation": {
        "x": 1.7907925725030182e-06,
        "y": -0.00010198427832722,
        "z": 0.01755613637013075,
        "w": 0.9998458739584584
      }
    },
    "tool1": {
      "position": {
        "x": 0.2732395211854321,
        "y": 0.005735027827511212,
        "z": 0.09895862376822605
      },
      "orientation": {
        "x": 1.790876977654963e-06,
        "y": -0.0001019842768450731,
        "z": 0.017556963871627036,
        "w": 0.9998458594281473
      }
    }
  },
  "HOME": {
    "tool0": {
      "position": {"x": 0.3024302540056362, "y": 0.0054692584918479385, "z": 0.3168755616122176},
      "orientation": {"x": 1.573306280013831e-06, "y": -0.00010198786531394762, "z": 0.015423917819394457, "w": 0.9998810391017027}
    },
    "tool1": {
      "position": {"x": 0.3024463591635571, "y": 0.0054699329925811824, "z": 0.23787556325604953},
      "orientation": {"x": 1.5733361905779901e-06, "y": -0.0001019878648525307, "z": 0.015424211060221484, "w": 0.9998810345781991}
    }
  }
}

# ===================== НИЗКОУРОВНЕВЫЕ ДВИЖЕНИЯ =====================

def move(m: MEdu, x: float, y: float, z: float, ox: float, oy: float, oz: float, ow: float,
         velocity: float = VEL, acceleration: float = ACC) -> None:
    m.move_to_coordinates(
        MoveCoordinatesParamsPosition(x=x, y=y, z=z),
        MoveCoordinatesParamsOrientation(x=ox, y=oy, z=oz, w=ow),
        velocity_scaling_factor=velocity,
        acceleration_scaling_factor=acceleration
    )

def move_pose(m: MEdu, cell: str, tool: str = "tool0", v: float = VEL, a: float = ACC) -> None:
    p = data[cell][tool]["position"]
    o = data[cell][tool]["orientation"]
    move(m, p["x"], p["y"], p["z"], o["x"], o["y"], o["z"], o["w"], v, a)

def go_via_home(m: MEdu, cell: str, tool: str = "tool0", v: float = VEL, a: float = ACC) -> None:
    """Всегда поднимаемся в HOME.tool0 перед перелётом в другую точку."""
    move_pose(m, "HOME", "tool0", v, a)
    move_pose(m, cell, "tool0", v, a)
    if tool == "tool1":
        move_pose(m, cell, "tool1", v, a)

def grab(m: MEdu) -> None:
    m.manage_gripper(rotation=GRIP_ROTATION, gripper=GRIP_CLOSE_ANGLE)

def release(m: MEdu) -> None:
    m.manage_gripper(rotation=GRIP_ROTATION, gripper=GRIP_OPEN_ANGLE)

# ===================== ПРОТОКОЛ ВЗЯТЬ/ПОЛОЖИТЬ =====================

def pick_from(m: MEdu, cell: str) -> None:
    """Подойти над клеткой, открыть, опуститься, схватить, подняться."""
    go_via_home(m, cell, "tool0")
    release(m)                  # открыть над клеткой
    move_pose(m, cell, "tool0") # (страховочно ещё раз над клеткой)
    move_pose(m, cell, "tool1") # вниз к кубику
    grab(m)                     # схватить
    move_pose(m, cell, "tool0") # подняться

def place_to(m: MEdu, cell: str) -> None:
    """Подойти над клеткой, опуститься, отпустить, подняться."""
    go_via_home(m, cell, "tool0")
    move_pose(m, cell, "tool0")
    move_pose(m, cell, "tool1") # вниз
    release(m)                  # отпустить
    move_pose(m, cell, "tool0") # подняться

def move_cube(m: MEdu, src_cell: str, dst_cell: str) -> None:
    """Переместить один кубик между двумя клетками/буфером."""
    print(f"[→] Беру из {src_cell} и кладу в {dst_cell}")
    pick_from(m, src_cell)
    place_to(m, dst_cell)  # place_to сам поднимет в HOME перед перелётом

# ===================== СЕТАП/ТИДАУН =====================

def start(host: str, client_id: str, login: str, password: str) -> MEdu:
    m = MEdu(host, client_id, login, password)
    print("[*] Подключение...")
    m.connect()
    m.get_control()
    # Питание инструмента (для модулей, где требуется)
    m.nozzle_power(True)
    time.sleep(0.2)
    # На старте открыть «когти»
    release(m)
    print("[+] Готово к работе")
    return m

def end(m: MEdu) -> None:
    try:
        m.nozzle_power(False)
    except Exception:
        pass
    try:
        m.release_control()
    except Exception:
        pass
    try:
        m.disconnect()
    except Exception:
        pass

# ===================== ДЕМО: CELL_1 -> CELL_2 =====================

def main():
    print("ВНИМАНИЕ: убедитесь, что рабочая зона манипулятора свободна от рук и предметов.")
    ans = input("Продолжить? [y/N] ").strip().lower()
    if ans != "y":
        print("Отмена.")
        return

    m = None
    try:
        m = start(HOST, CLIENT_ID, LOGIN, PASSWORD)

        # Страховочный подъём
        move_pose(m, "HOME", "tool0")

        # Перенос одного кубика из CELL_1 в CELL_2
        move_cube(m, "CELL_1", "CELL_2")

        # Возврат в HOME
        move_pose(m, "HOME", "tool0")
        print("[✓] Готово")
    except KeyboardInterrupt:
        print("\n[!] Прервано пользователем")
    except Exception as e:
        print("[!] Ошибка:", e)
    finally:
        if m is not None:
            end(m)

if __name__ == "__main__":
    main()
