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


CELL_DESCENT_ROT = -5.0     # градусы, перед спуском в любую CELL_*
BUFFER_DESCENT_ROT = -11.0  # градусы, перед спуском в BUFFER/BUFF

# Положение "открыть/закрыть" для механического захвата (при необходимости подправь)
GRIP_OPEN_ANGLE = 15
GRIP_CLOSE_ANGLE = 45
GRIP_ROTATION = 0

# Профиль движения
VEL = 0.2
ACC = 0.2

# === КООРДИНАТЫ (твои из примера) ===
data: Dict[str, Dict[str, Dict[str, Any]]] = {
  "CELL_1": {
    "tool0": {
      "position": {
        "x": 0.22902609621945036,
        "y": 0.001168641874036047,
        "z": 0.17707931488477024
      },
      "orientation": {
        "x": 1.1202308946114374e-06,
        "y": -0.00010199384808238738,
        "z": 0.010982002235698764,
        "w": 0.9999396907928474
      }
    },
    "tool1": {
      "position": {
        "x": 0.22904220833178704,
        "y": 0.0011689958351163692,
        "z": 0.09807931652860222
      },
      "orientation": {
        "x": 1.1202308946114374e-06,
        "y": -0.00010199384808238738,
        "z": 0.010982002235698764,
        "w": 0.9999396907928474
      }
    }
  },
  "CELL_2": {
    "tool0": {
      "position": {
        "x": 0.27236315036313435,
        "y": 0.0024415883840102383,
        "z": 0.1782188237634018
      },
      "orientation": {
        "x": 1.1803008050967456e-06,
        "y": -0.00010199317062402019,
        "z": 0.01157092292901847,
        "w": 0.9999330494280958
      }
    },
    "tool1": {
      "position": {
        "x": 0.27237926204735696,
        "y": 0.0024419613235604166,
        "z": 0.09921882540723378
      },
      "orientation": {
        "x": 1.1803008050967456e-06,
        "y": -0.00010199317062402019,
        "z": 0.01157092292901847,
        "w": 0.9999330494280958
      }
    }
  },
  "CELL_3": {
    "tool0": {
      "position": {
        "x": 0.315563635432352,
        "y": 0.0036895452768883233,
        "z": 0.17795268619028753
      },
      "orientation": {
        "x": 1.2203652653201576e-06,
        "y": -0.00010199269911371181,
        "z": 0.011963711756425813,
        "w": 0.9999284270371601
      }
    },
    "tool1": {
      "position": {
        "x": 0.3155797468186092,
        "y": 0.003689930874177756,
        "z": 0.09895268783411948
      },
      "orientation": {
        "x": 1.2203652653201576e-06,
        "y": -0.00010199269911371181,
        "z": 0.011963711756425813,
        "w": 0.9999284270371601
      }
    }
  },
  "CELL_4": {
    "tool0": {
      "position": {
        "x": 0.35944996147541336,
        "y": 0.00572836865823355,
        "z": 0.17404387340126207
      },
      "orientation": {
        "x": 1.3605486509282238e-06,
        "y": -0.00010199092543609554,
        "z": 0.013338058680713688,
        "w": 0.9999110389362795
      }
    },
    "tool1": {
      "position": {
        "x": 0.35946607174082496,
        "y": 0.005728798542826572,
        "z": 0.0950438750450941
      },
      "orientation": {
        "x": 1.3605486509282238e-06,
        "y": -0.00010199092543609554,
        "z": 0.013338058680713688,
        "w": 0.9999110389362795
      }
    }
  },
  "BUFFER": {
    "tool0": {
      "position": {
        "x": 0.2746298031409517,
        "y": -0.03636509033483095,
        "z": 0.17647032022996165
      },
      "orientation": {
        "x": -5.999327495691802e-06,
        "y": -0.00010182341593910528,
        "z": -0.058817588491957166,
        "w": 0.9982687418125396
      }
    },
    "tool1": {
      "position": {
        "x": 0.2746457438593758,
        "y": -0.03636746372224744,
        "z": 0.09747032187379365
      },
      "orientation": {
        "x": -5.999416633003472e-06,
        "y": -0.00010182341068719045,
        "z": -0.05881846238713292,
        "w": 0.9982686903226072
      }
    }
  },
  "HOME": {
    "tool0": {
      "position": {
        "x": 0.3024302540056362,
        "y": 0.0054692584918479385,
        "z": 0.3168755616122176
      },
      "orientation": {
        "x": 1.573306280013831e-06,
        "y": -0.00010198786531394762,
        "z": 0.015423917819394457,
        "w": 0.9998810391017027
      }
    },
    "tool1": {
      "position": {
        "x": 0.3024463591635571,
        "y": 0.0054699329925811824,
        "z": 0.23787556325604953
      },
      "orientation": {
        "x": 1.5733361905779901e-06,
        "y": -0.0001019878648525307,
        "z": 0.015424211060221484,
        "w": 0.9998810345781991
      }
    }
  }

}

# ===================== НИЗКОУРОВНЕВЫЕ ДВИЖЕНИЯ =====================

def move(m: MEdu, x: float, y: float, z: float, ox: float, oy: float, oz: float, ow: float,
         velocity: float = VEL, acceleration: float = ACC, *, timeout: float = 60.0) -> None:
    """
    Блокирующий move: ждём завершения траектории, чтобы следующая команда не «съела» промежуточную точку.
    """
    prom = m.move_to_coordinates(
        MoveCoordinatesParamsPosition(x=x, y=y, z=z),
        MoveCoordinatesParamsOrientation(x=ox, y=oy, z=oz, w=ow),
        velocity_scaling_factor=velocity,
        acceleration_scaling_factor=acceleration
    )
    # ВАЖНО: дождаться завершения
    if hasattr(prom, "result"):
        prom.result(timeout=timeout)
    else:
        # На всякий случай — минимальная задержка, если SDK вернул не-промис
        time.sleep(0.2)

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

def _target_rotation_for(place: str) -> float:
    """Возвращает целевой поворот кисти перед спуском в клетку/буфер."""
    name = place.upper()
    if name == "BUFFER" or name == "BUFF":
        return BUFFER_DESCENT_ROT
    if name.startswith("CELL_"):
        return CELL_DESCENT_ROT
    # на всякий случай — нейтраль
    return GRIP_ROTATION

# --- ЗАМЕНИ grab/release ТАК, ЧТОБЫ ОНИ НЕ МЕНЯЛИ ОРИЕНТАЦИЮ ПО УМОЛЧАНИЮ ---
def grab(m: MEdu, *, rotation: float = None) -> None:
    """Закрыть захват. Если rotation задан — одновременно задать поворот кисти."""
    rot = GRIP_ROTATION if rotation is None else rotation
    m.manage_gripper(rotation=rot, gripper=GRIP_CLOSE_ANGLE)

def release(m: MEdu, *, rotation: float = None) -> None:
    """Открыть захват. Если rotation задан — одновременно задать поворот кисти."""
    rot = GRIP_ROTATION if rotation is None else rotation
    m.manage_gripper(rotation=rot, gripper=GRIP_OPEN_ANGLE)

# --- pick/place: ДОБАВЛЕНА ОРИЕНТАЦИЯ ПЕРЕД СПУСКОМ ---
def pick_from(m: MEdu, cell: str) -> None:
    """Подойти над клеткой, открыться, ПОВЕРНУТЬСЯ, опуститься, схватить, подняться."""
    go_via_home(m, cell, "tool0")
    # Открыться и сразу выставить нужный поворот для этой точки
    r = _target_rotation_for(cell)
    release(m, rotation=r)              # открыто + нужная ориентация
    move_pose(m, cell, "tool0")         # над клеткой (страховочно)
    move_pose(m, cell, "tool1")         # вниз к кубику (уже с нужным поворотом)
    grab(m, rotation=r)                 # схватить, сохранив ориентацию
    move_pose(m, cell, "tool0")         # подняться

def place_to(m: MEdu, cell: str) -> None:
    """Подойти над клеткой, ПОВЕРНУТЬСЯ, опуститься, отпустить, подняться."""
    go_via_home(m, cell, "tool0")
    r = _target_rotation_for(cell)
    # Мы держим кубик закрытым — просто переустановим ориентацию, не раскрываясь
    grab(m, rotation=r)                 # подтвердить/задать поворот кисти, оставить закрытым
    move_pose(m, cell, "tool0")         # над клеткой (страховочно)
    move_pose(m, cell, "tool1")         # вниз (с нужным поворотом)
    release(m, rotation=r)              # отпустить, оставив ориентацию
    move_pose(m, cell, "tool0")         # подняться

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
