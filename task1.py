import sys
import time
from typing import Dict, Any, List

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

# Положение "открыть/закрыть" для механического захвата (при необходимости подправь)
GRIP_OPEN_ANGLE = 45
GRIP_CLOSE_ANGLE = 0
GRIP_ROTATION = 0

# Профиль движения
VEL = 0.2
ACC = 0.2

# === КООРДИНАТЫ (твои из примера) ===
data: Dict[str, Dict[str, Dict[str, Any]]] = {
    "CELL_1": {
        "tool0": {
            "position": {"x": 0.22755050002486693, "y": 0.002476957662608077, "z": 0.18495216086666},
            "orientation": {"x": 1.4206303810959728e-06, "y": -0.00010199010625184164, "z": 0.013927095259560414, "w": 0.9999030081031015},
        },
        "tool1": {
            "position": {"x": 0.2275666097726147, "y": 0.0024774065277337258, "z": 0.10595216251049194},
            "orientation": {"x": 1.4206303810959728e-06, "y": -0.00010199010625184164, "z": 0.013927095259560414, "w": 0.9999030081031015},
        },
    },
    "CELL_2": {
        "tool0": {
            "position": {"x": 0.2746911402342351, "y": 0.00390698782184568, "z": 0.1835391566998359},
            "orientation": {"x": 1.442258708863234e-06, "y": -0.00010198980269485759, "z": 0.014139137689875892, "w": 0.9999000321939122},
        },
        "tool1": {
            "position": {"x": 0.2747053540157846, "y": 0.003908250384547219, "z": 0.10454031259284141},
            "orientation": {"x": 1.442418377617392e-06, "y": -0.00010198980043674965, "z": 0.014140703069837963, "w": 0.9999000100573511},
        },
    },
    "CELL_3": {
        "tool0": {
            "position": {"x": 0.3194296876987808, "y": 0.005162434416828922, "z": 0.1828371406643466},
            "orientation": {"x": 1.4406484924327027e-06, "y": -0.00010198982545247866, "z": 0.014123351254200509, "w": 0.9999002552981725},
        },
        "tool1": {
            "position": {"x": 0.319445797269085, "y": 0.005162889605811008, "z": 0.10383714230817853},
            "orientation": {"x": 1.4406484924327027e-06, "y": -0.00010198982545247866, "z": 0.014123351254200509, "w": 0.9999002552981725},
        },
    },
    "CELL_4": {
        "tool0": {
            "position": {"x": 0.36244258812148633, "y": 0.0038860524789116092, "z": 0.18145266069139193},
            "orientation": {"x": 1.090189000331486e-06, "y": -0.00010199417361737055, "z": 0.010687473864690397, "w": 0.9999428821179696},
        },
        "tool1": {
            "position": {"x": 0.3624587004395427, "y": 0.0038863969484253654, "z": 0.10245266233522393},
            "orientation": {"x": 1.090189000331486e-06, "y": -0.00010199417361737055, "z": 0.010687473864690397, "w": 0.9999428821179696},
        },
    },
    "BUFFER": {
        "tool0": {
            "position": {"x": 0.2774658663122415, "y": -0.033644419948043146, "z": 0.18082358544639707},
            "orientation": {"x": -5.457979821336838e-06, "y": -0.00010185386796868743, "z": -0.05328386075682551, "w": 0.9985794008384348},
        },
        "tool1": {
            "position": {"x": 0.27748189041189114, "y": -0.03364613857622218, "z": 0.10182358709022907},
            "orientation": {"x": -5.457979821336838e-06, "y": -0.00010185386796868743, "z": -0.05328386075682551, "w": 0.9985794008384348},
        },
    },
    "HOME": {
        "tool0": {
            "position": {"x": 0.3024302540056362, "y": 0.0054692584918479385, "z": 0.3168755616122176},
            "orientation": {"x": 1.573306280013831e-06, "y": -0.00010198786531394762, "z": 0.015423917819394457, "w": 0.9998810391017027},
        },
        "tool1": {
            "position": {"x": 0.3024463591635571, "y": 0.0054699329925811824, "z": 0.23787556325604953},
            "orientation": {"x": 1.5733361905779901e-06, "y": -0.0001019878648525307, "z": 0.015424211060221484, "w": 0.9998810345781991},
        },
    },
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
    move_pose(m, cell, "tool0", v, a)  # прибываем над клеткой
    if tool == "tool1":
        move_pose(m, cell, "tool1", v, a)

def grab(m: MEdu) -> None:
    m.manage_gripper(rotation=GRIP_ROTATION, gripper=GRIP_CLOSE_ANGLE)

def release(m: MEdu) -> None:
    m.manage_gripper(rotation=GRIP_ROTATION, gripper=GRIP_OPEN_ANGLE)

# ===================== ПРОТОКОЛ ВЗЯТЬ/ПОЛОЖИТЬ =====================

def pick_from(m: MEdu, cell: str) -> None:
    """Подойти над клеткой, открыться, опуститься, схватить, подняться."""
    go_via_home(m, cell, "tool0")
    release(m)                      # открыть над клеткой
    move_pose(m, cell, "tool1")     # вниз к кубику
    grab(m)                         # схватить
    move_pose(m, cell, "tool0")     # подняться

def place_to(m: MEdu, cell: str) -> None:
    """Подойти над клеткой, опуститься, отпустить, подняться."""
    go_via_home(m, cell, "tool0")
    move_pose(m, cell, "tool1")     # вниз
    release(m)                      # отпустить
    move_pose(m, cell, "tool0")     # подняться

def move_cube(m: MEdu, src_cell: str, dst_cell: str) -> None:
    """Переместить один кубик между двумя клетками/буфером, соблюдая подъём перед перелётом."""
    print(f"    - Беру из {src_cell} → кладу в {dst_cell}")
    pick_from(m, src_cell)
    go_via_home(m, dst_cell, "tool0")
    place_to(m, dst_cell)

# ===================== СЕТАП/ТИДАУН =====================

def start(host: str, client_id: str, login: str, password: str) -> MEdu:
    m = MEdu(host, client_id, login, password)
    print("[*] Подключение...")
    m.connect()
    m.get_control()
    m.nozzle_power(True)
    time.sleep(0.2)
    # На старте всегда открыть «когти»
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

# ===================== АЛГОРИТМ СОРТИРОВКИ С 1 БУФЕРОМ =====================

def sort_with_one_buffer_and_move(m: MEdu, A: List[int]) -> None:
    """
    A — 1-индексный список актуальной расстановки кубиков по клеткам 1..n.
    Цель: добиться A[i] == i. Доступны клетки CELL_1..CELL_n и BUFFER.
    Для минимизации перемещений используем разбор циклов перестановки:
    - из начала цикла переносим кубик в BUFFER,
    - протягиваем правильные кубики на их места по цепочке,
    - замыкаем цикл, забирая из BUFFER.
    """
    n = len(A) - 1
    # Быстрый доступ: pos[val] = где стоит кубик с номером val
    pos = [0]*(n+1)
    for i in range(1, n+1):
        pos[A[i]] = i

    for start in range(1, n+1):
        if A[start] == start:
            continue

        print(f"[ЦИКЛ] Начинаю цикл от клетки {start}: кубик {A[start]} не на месте")

        # 1) В BUFFER уводим кубик из клетки start
        buf_val = A[start]
        move_cube(m, f"CELL_{start}", "BUFFER")
        A[start] = None          # дырка появилась в start
        hole = start

        # 2) Тянем по цепочке «правильные кубики» на их места
        while True:
            need = hole  # какой номер должен стоять в дырке
            if need == buf_val:
                break  # пора замыкать цикл

            p = pos[need]            # где сейчас нужный кубик
            move_cube(m, f"CELL_{p}", f"CELL_{hole}")  # ставим его на место

            # Обновляем структуру данных
            pos[A[p]] = hole         # кубик need уехал в hole
            A[hole] = A[p]
            A[p] = None              # в p теперь дырка
            hole = p

        # 3) Замыкаем цикл: ставим кубик из BUFFER на своё целевое место (в текущую дырку)
        move_cube(m, "BUFFER", f"CELL_{hole}")
        A[hole] = buf_val
        pos[buf_val] = hole

        print(f"[ЦИКЛ] Готово: цикл, начинавшийся в {start}, закрыт")

    print("[✓] Сортировка завершена")

# ===================== MAIN =====================

def parse_order(s: str) -> List[int]:
    """
    Допускаем форматы:
      - '2 3 4 1'
      - '2,3,4,1'
    """
    raw = s.replace(",", " ").split()
    nums = list(map(int, raw))
    if len(nums) != 4 or any(not (1 <= x <= 4) for x in nums):
        raise ValueError("Нужно ввести 4 числа от 1 до 4, например: 2 3 4 1")
    # Делаем 1-индексный массив A: A[i] = номер кубика в клетке i
    A = [0] + nums
    return A

def main():
    print("ВНИМАНИЕ: убедитесь, что рабочая зона манипулятора свободна от рук и предметов.")
    ans = input("Продолжить? [y/N] ").strip().lower()
    if ans != "y":
        print("Отмена.")
        return

    order_str = input("Введите порядок кубиков в клетках 1..4 (например: 2 3 4 1): ")
    A = parse_order(order_str)

    m = None
    try:
        m = start(HOST, CLIENT_ID, LOGIN, PASSWORD)
        # Страховочный подъём перед началом
        move_pose(m, "HOME", "tool0")

        print(f"[=] Исходная расстановка: {A[1:]}")
        sort_with_one_buffer_and_move(m, A)
        print(f"[=] Итоговая расстановка:  {A[1:]}")
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
