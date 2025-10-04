from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Callable

# -------- Геометрия рабочего пространства (всё — константы) --------
# Замените координаты на реальные. Индексы клеток: 1..4, буфер = 0.
CELL_COORDS: Dict[int, Tuple[float, float]] = {
    0: (0.000, 0.300),  # BUF
    1: (0.000, 0.000),
    2: (0.100, 0.000),
    3: (0.200, 0.000),
    4: (0.300, 0.000),
}

# Уровни по оси Z (мм или м — по вашей системе)
Z_SAFE   = 0.150  # безопасная высота для пролётов
Z_APPROACH = 0.050  # пред-подход над кубиком
Z_PICK   = 0.000  # высота захвата/посадки (подберите)
Z_PLACE  = Z_PICK  # обычно то же, что Z_PICK

SPEED_TRAVEL = 0.25  # м/с или относительная скорость — как поддерживает ваш драйвер
SPEED_PICK   = 0.10

@dataclass
class MoveLog:
    action: str
    args: tuple

class ManipulatorController:
    """
    Адаптер над реальным манипулятором.
    Реализует move(i -> j) и сортировку по циклам с одним буфером.
    Низкоуровневые методы go/open/close — заглушки для интеграции.
    """
    def __init__(self):
        # Журнал команд — удобно для отладки/симуляции
        self.log: List[MoveLog] = []

        # Хуки/коллбеки (опционально можно подменить снаружи)
        self.on_before_pick: Optional[Callable[[int], None]] = None
        self.on_after_place: Optional[Callable[[int], None]] = None

    # -------- Низкоуровневые операции (ЗАПОЛНИТЬ ПОД ВАШ API) --------
    def go(self, x: float, y: float, z: float, speed: float):
        """Линейное перемещение TCP. TODO: заменить на вызов SDK/драйвера."""
        self.log.append(MoveLog("go", (x, y, z, speed)))
        # TODO: robot.move_linear(x, y, z, speed)

    def open_gripper(self):
        """Открыть хват. TODO: заменить на вызов вашего грипера."""
        self.log.append(MoveLog("open_gripper", ()))
        # TODO: gripper.open()

    def close_gripper(self):
        """Закрыть хват. TODO: заменить на вызов вашего грипера."""
        self.log.append(MoveLog("close_gripper", ()))
        # TODO: gripper.close()

    def wait(self, seconds: float):
        """(опционально) пауза для стабилизации."""
        self.log.append(MoveLog("wait", (seconds,)))
        # TODO: time.sleep(seconds)

    # -------- Вспомогательные высокоуровневые примитивы --------
    def _pose_above(self, cell: int, z: float) -> Tuple[float, float, float]:
        x, y = CELL_COORDS[cell]
        return (x, y, z)

    def pick_from_cell(self, cell: int):
        """Подъехать, схватить, поднять."""
        if self.on_before_pick:
            self.on_before_pick(cell)

        # Подход сверху
        self.go(*self._pose_above(cell, Z_SAFE), SPEED_TRAVEL)
        self.go(*self._pose_above(cell, Z_APPROACH), SPEED_TRAVEL)
        self.go(*self._pose_above(cell, Z_PICK), SPEED_PICK)

        # Захват
        self.open_gripper()
        self.wait(0.05)
        self.close_gripper()
        self.wait(0.05)

        # Подняться на безопасную
        self.go(*self._pose_above(cell, Z_SAFE), SPEED_TRAVEL)

    def place_to_cell(self, cell: int):
        """Спуститься, положить, подняться."""
        # Подлет над целевой
        self.go(*self._pose_above(cell, Z_SAFE), SPEED_TRAVEL)
        self.go(*self._pose_above(cell, Z_APPROACH), SPEED_TRAVEL)
        self.go(*self._pose_above(cell, Z_PLACE), SPEED_PICK)

        # Отпустить
        self.open_gripper()
        self.wait(0.05)

        # Отлет вверх
        self.go(*self._pose_above(cell, Z_SAFE), SPEED_TRAVEL)

        if self.on_after_place:
            self.on_after_place(cell)

    # -------- ОПЕРАЦИЯ move(i -> j) --------
    def move(self, i: int, j: int, A: List[Optional[int]], pos: List[Optional[int]]):
        """
        Переместить кубик из клетки i в пустую клетку j.
        Обновляет модель A/pos.
        Правила: j ДОЛЖНА быть пустой (None), i — занята.
        """
        assert i in CELL_COORDS and j in CELL_COORDS, f"unknown cell index i={i} j={j}"
        assert A[i] is not None, f"source cell {i} is empty"
        assert A[j] is None, f"destination cell {j} must be empty"

        # Реальное перемещение
        self.pick_from_cell(i)
        self.place_to_cell(j)

        # Обновить внутреннюю модель
        val = A[i]
        A[j] = val
        if val is not None:
            pos[val] = j
        A[i] = None

        # Логически: теперь j занят, i пуст

    # -------- Сортировка по циклам с 1 буфером --------
    def sort_with_one_buffer(self, A: List[int]) -> List[MoveLog]:
        """
        A — 1-индексный массив: A[i] = номер кубика в клетке i.
        Буфер — индекс 0. A[0] не используется (будет None).
        Возвращает журнал команд.
        """
        n = len(A) - 1
        # Модель занятости
        A = A[:]  # копия
        A[0] = None
        # Таблица позиций
        pos: List[Optional[int]] = [None] * (n + 1)
        for i in range(1, n + 1):
            pos[A[i]] = i

        BUF = 0

        for start in range(1, n + 1):
            if A[start] == start:
                continue  # уже на месте

            # 1) старт цикла — вынести в буфер
            self.move(start, BUF, A, pos)
            hole = start
            buf_val = A[BUF]  # номер во временном буфере

            # 2) протягиваем «правильные» кубики до тех пор,
            # пока дырка не совпадёт с целевой позицией буферного кубика
            while hole != buf_val:
                p = pos[hole]       # где сейчас кубик с номером 'hole'
                self.move(p, hole, A, pos)
                hole = p

            # 3) закрыть цикл — вернуть буферный кубик на своё место
            self.move(BUF, hole, A, pos)

        return self.log


# ------------------------- ПРИМЕР -------------------------
if __name__ == "__main__":
    ctrl = ManipulatorController()

    # Пример: 4 клетки, буфер — 0.
    # A[1..4] — текущий порядок кубиков (уникальные 1..4)
    A = [None, 4, 1, 3, 2]  # 1-индексный список; A[0] зарезервирован под буфер

    logs = ctrl.sort_with_one_buffer(A)

    # Печать маршрута действий (для проверки)
    for rec in logs:
        print(f"{rec.action} {rec.args}")
