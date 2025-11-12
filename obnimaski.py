import time
import sys
import json

from sdk.commands.move_coordinates_command import MoveCoordinatesParamsPosition, MoveCoordinatesParamsOrientation, \
    PlannerType
from sdk.manipulators.medu import MEdu

HOST = "172.16.2.190"
CLIENT_ID = "test-client"
LOGIN = "user"
PASSWORD = "pass"

# Диапазон положений клешни (условные единицы SDK/сервопривода)
GRIP_MIN = 0          # полностью закрыта (подберите под ваш инструмент)
GRIP_MAX = 60         # максимально безопасно открыта (не обязательно физический максимум 80 мм)
GRIP_STEP = 3         # шаг закрытия при поиске контакта
GRIP_SPEED = 40       # скорость привода захвата (умеренная)
HOLD_SEC = 0.35       # задержка сжатия, чтобы «подхватить» кубик
AFTER_MOVE_SETTLE = 0.2  # пауза после подлёта к точке перед захватом

json_file_path = 'coords.json'


# --- Универсальные обёртки для управления клешнёй ---

def _try_call_variants(obj, variants):
    """
    Пытается вызвать на объекте один из методов из списка variants.
    Каждый элемент variants — это кортеж: (method_name, kwargs_variants),
    где kwargs_variants — список словарей с разными сигнатурами.
    Возвращает True, если удалось вызвать хоть что-то.
    """
    for method_name, kwargs_list in variants:
        if not hasattr(obj, method_name):
            continue
        method = getattr(obj, method_name)
        for kwargs in kwargs_list:
            try:
                method(**kwargs)
                return True
            except TypeError:
                # неподходящая сигнатура — пробуем следующую
                continue
            except Exception as e:
                # метод есть, но упал — логируем и пробуем следующее
                print(f"[!] {method_name} вызван, но вернул ошибку: {e}")
                continue
    return False


def gripper_move(m: MEdu, position: int, speed: int = GRIP_SPEED) -> bool:
    """
    Ставит клешню в заданное положение; возвращает True, если получилось.
    Поддерживает разные имена/сигнатуры методов в SDK.
    """
    position = int(max(GRIP_MIN, min(GRIP_MAX, position)))
    variants = [
        # наиболее «говорящие» варианты
        ("gripper_move", [
            {"position": position, "speed": speed},
            {"target": position, "speed": speed},
            {"pos": position, "speed": speed},
        ]),
        ("set_gripper_position", [
            {"position": position, "speed": speed},
            {"value": position, "speed": speed},
        ]),
        ("gripper_set_position", [
            {"value": position, "speed": speed},
            {"position": position, "speed": speed},
        ]),
        # возможные универсальные PWM/servo API для GP3
        ("set_tool_servo", [
            {"port": "GP3", "position": position, "speed": speed},
            {"port": 3, "position": position, "speed": speed},
        ]),
        ("tool_servo_write", [
            {"pin": "GP3", "position": position, "speed": speed},
            {"pin": 3, "position": position, "speed": speed},
            {"pin": "GP3", "value": position},  # без скорости
        ]),
        # иногда встречается «pwm» интерфейс
        ("set_pwm", [
            {"port": "GP3", "value": position},
            {"channel": "GP3", "value": position},
        ]),
    ]
    ok = _try_call_variants(m, variants)
    if not ok:
        print("[!] Не найден метод управления клешнёй в SDK. Проверьте названия методов для вашего SDK.")
    return ok


def open_gripper(m: MEdu, speed: int = GRIP_SPEED):
    return gripper_move(m, GRIP_MAX, speed)


def close_gripper(m: MEdu, speed: int = GRIP_SPEED):
    return gripper_move(m, GRIP_MIN, speed)


def close_until_contact(m: MEdu,
                        start_open: int = GRIP_MAX,
                        end_close: int = GRIP_MIN,
                        step: int = GRIP_STEP,
                        speed: int = GRIP_SPEED,
                        dwell: float = HOLD_SEC):
    """
    Плавно закрывает клешню от 'start_open' к 'end_close' с шагом 'step'.
    Если у вашего SDK есть датчик/признак контакта (например, по току/ошибке),
    вставьте проверку внутрь цикла и делайте break при срабатывании.
    """
    # На всякий случай открываемся в исходное значение
    gripper_move(m, start_open, speed)
    time.sleep(0.1)

    # Идём «лестницей» к закрытию
    if start_open < end_close:
        rng = range(start_open, end_close + 1, step)
    else:
        rng = range(start_open, end_close - 1, -step)

    for p in rng:
        gripper_move(m, p, speed)
        time.sleep(0.06)  # короткая пауза на шаг

        # --- МЕСТО ДЛЯ ДЕТЕКЦИИ КОНТАКТА, если доступно в SDK ---
        # Пример наброска:
        # if hasattr(m, "gripper_is_blocked") and m.gripper_is_blocked():
        #     print("[*] Контакт обнаружен (по току/ошибке привода).")
        #     break
        # ---------------------------------------------------------

    # Небольшая выдержка, чтобы «подхватить» предмет
    time.sleep(dwell)


def main():
    m = MEdu(HOST, CLIENT_ID, LOGIN, PASSWORD)
    try:
        print("[*] Подключение...")
        m.connect()
        print("[+] Подключено")

        print("[*] Запрашиваем доступ к управлению...")
        m.get_control()
        print("[+] Доступ получен")

        print("[*] Включаем питание инструмента на стреле...")
        m.nozzle_power(True)
        print("[+] Питание инструмента включено")

        # Небольшая задержка, чтобы всё стабилизировалось
        time.sleep(0.5)
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print("[*] Обход точек и проверка захвата...")
        for cell_name, tools in data.items():
            print(f"Обработка {cell_name}...")
            for tool_name, tool_data in tools.items():
                pos = tool_data['position']
                orient = tool_data['orientation']

                posit = MoveCoordinatesParamsPosition(
                    x=pos['x'],
                    y=pos['y'],
                    z=pos['z']
                )
                orient_obj = MoveCoordinatesParamsOrientation(
                    x=orient['x'],
                    y=orient['y'],
                    z=orient['z'],
                    w=orient['w']
                )

                # Подлёт к точке
                m.move_to_coordinates(
                    posit,
                    orient_obj,
                    velocity_scaling_factor=0.1,
                    acceleration_scaling_factor=0.1
                )
                print(f"  Перемещено к {cell_name}/{tool_name}")
                time.sleep(AFTER_MOVE_SETTLE)

                # --- СЖАТИЕ/РАЗЖАТИЕ КЛЕШНИ ---
                # Плавно закрываемся до контакта/упора
                print("  Закрытие клешни...")
                close_until_contact(m)

                # Держим предмет (имитация «зажал кубик»)
                # Если реально поднимать не нужно — просто пауза:
                # time.sleep(HOLD_SEC)

                # Разжимаем
                print("  Открытие клешни...")
                open_gripper(m)
                time.sleep(0.15)

        print("[✓] Тест завершён успешно")

    except KeyboardInterrupt:
        print("\n[!] Прервано пользователем")
    except Exception as e:
        print("[!] Ошибка во время теста:", e)
        print(type(e).__name__)
    finally:
        try:
            print("[*] Выключаем питание инструмента...")
            m.nozzle_power(False)
            print("[+] Питание инструмента выключено")
        except Exception as e:
            print("[!] Не удалось выключить питание инструмента:", e)

        try:
            print("[*] Возврат управления...")
            m.release_control()
        except Exception:
            pass

        try:
            m.disconnect()
            print("[+] Отключено")
        except Exception:
            pass


if __name__ == "__main__":
    print("ВНИМАНИЕ: убедитесь, что рабочая зона манипулятора свободна от посторонних предметов и рук.")
    print("Продолжить? [y/N] ", end="", flush=True)
    ans = sys.stdin.readline().strip().lower()
    if ans == "y":
        main()
    else:
        print("Отмена.")
