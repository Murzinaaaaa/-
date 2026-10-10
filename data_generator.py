import asyncio
import sqlite3
import json
import random
import time
import os
import glob
from dataclasses import dataclass
from typing import List, Dict

total_generated = {"scalars": 0, "trends": 0}


@dataclass
class MetricPoint:
    tag_id: int
    value: float
    timestamp: float
    is_trend: bool

class BaseDataSource:
    def __init__(self, source_id: int, start_tag: int, end_tag: int, trends: List[int]):
        self._source_id = source_id
        self._tags = list(range(start_tag, end_tag + 1))  # 1000 тегов на источник
        self._trends = trends
        self._buffer_file = f"disk_buffer_source_{source_id}.json"

    @property
    def source_id(self):
        return self._source_id

    def generate_batch(self) -> List[MetricPoint]:
        count = random.randint(100, 600)
        data = []
        now = time.time()
        for _ in range(count):
            if random.random() < 0.15 and self._trends:
                tag_id = random.choice(self._trends)
                is_trend = True
            else:
                tag_id = random.choice(self._tags)
                is_trend = False
            value = random.uniform(100.0, 600.0)
            data.append(MetricPoint(tag_id, value, now, is_trend))
        return data

    def write_to_disk(self, batch: List[MetricPoint]):
        payload = [{"t": d.tag_id, "v": d.value, "ts": d.timestamp, "tr": d.is_trend} for d in batch]
        temp_file = self._buffer_file + ".tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, self._buffer_file)


class ComputeSource(BaseDataSource):
    pass


class DatabaseSource(BaseDataSource):
    pass


class NetworkSource(BaseDataSource):
    pass


class ApplicationSource(BaseDataSource):
    pass



class DatabaseManager:
    def __init__(self, db_name: str = "saas_monitoring.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS source_types (
            id INTEGER PRIMARY KEY, name TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS objects (
            id INTEGER PRIMARY KEY, name TEXT, source_type_id INTEGER,
            FOREIGN KEY(source_type_id) REFERENCES source_types(id))""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY, name TEXT, description TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS scalar_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER, value REAL, timestamp REAL)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS trend_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trend_id INTEGER, value REAL, timestamp REAL)""")
        self.conn.commit()

    def insert_batch(self, scalars: List[Dict], trends: List[Dict]):
        cursor = self.conn.cursor()
        if scalars:
            cursor.executemany(
                "INSERT INTO scalar_log (object_id, value, timestamp) VALUES (?, ?, ?)",
                [(s['t'], s['v'], s['ts']) for s in scalars]
            )
        if trends:
            cursor.executemany(
                "INSERT INTO trend_log (trend_id, value, timestamp) VALUES (?, ?, ?)",
                [(t['t'], t['v'], t['ts']) for t in trends]
            )
        self.conn.commit()

    def close(self):
        self.conn.close()


class JournalManager:
    @staticmethod
    def save_non_trends_to_json(scalars: List[Dict], source_id: int):
        file_name = f"json_journal_source_{source_id}.json"
        with open(file_name, 'a', encoding='utf-8') as f:
            for item in scalars:
                f.write(json.dumps(item) + "\n")

    @staticmethod
    def process_disk_buffer(source: BaseDataSource, db: DatabaseManager) -> int:
        if not os.path.exists(source._buffer_file):
            return 0
        try:
            with open(source._buffer_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return 0
        if not data:
            return 0

        trends = [d for d in data if d['tr']]
        scalars = [d for d in data if not d['tr']]

        global total_generated
        total_generated["trends"] += len(trends)
        total_generated["scalars"] += len(scalars)

        db.insert_batch(scalars, trends)
        JournalManager.save_non_trends_to_json(scalars, source.source_id)
        os.remove(source._buffer_file)
        return len(data)


async def producer(source: BaseDataSource):
    while True:
        batch = source.generate_batch()
        source.write_to_disk(batch)
        await asyncio.sleep(1.0)


async def consumer(sources: List[BaseDataSource], db: DatabaseManager):
    while True:
        total = 0
        for source in sources:
            total += JournalManager.process_disk_buffer(source, db)
        if total > 0:
            print(f"[{time.strftime('%H:%M:%S')}] Сохранено: {total} записей")
        await asyncio.sleep(0.2)


async def main():
    print("=== Запуск генератора данных ===\n")

    db = DatabaseManager("saas_monitoring.db")

    db.conn.executemany("INSERT OR IGNORE INTO source_types VALUES (?, ?)", [
        (1, "Compute"), (2, "Database"), (3, "Network"), (4, "Application")
    ])

    trends_data = [
        (4001, "DAU", "Daily Active Users"),
        (4002, "MAU", "Monthly Active Users"),
        (4003, "Conversion", "Конверсия в покупку"),
        (4004, "Revenue", "Выручка в минуту"),
        (4005, "NPS", "Net Promoter Score"),
        (4006, "Retention", "Удержание пользователей"),
        (4007, "ChurnRate", "Отток клиентов"),
        (4008, "ARPU", "Средний доход на пользователя"),
        (4009, "LTV", "Lifetime Value"),
        (4010, "CAC", "Стоимость привлечения"),
        (4011, "MRR", "Monthly Recurring Revenue"),
        (4012, "ActiveSessions", "Активные сессии"),
        (4013, "TimeInApp", "Время в приложении"),
        (4014, "CartAbandonment", "Брошенные корзины"),
        (4015, "SupportTickets", "Тикеты поддержки"),
        (4016, "FeatureAdoption", "Использование фич"),
        (4017, "PageLoadTime", "Время загрузки страниц"),
        (4018, "ErrorRate", "Процент ошибок"),
        (4019, "APIAvailability", "Доступность API"),
        (4020, "UserSatisfaction", "Удовлетворённость")
    ]
    db.conn.executemany("INSERT OR IGNORE INTO trends VALUES (?, ?, ?)", trends_data)

    objects_data = []
    for source_id in range(1, 5):
        for i in range(1, 1001):
            obj_id = (source_id - 1) * 1000 + i
            objects_data.append((obj_id, f"Object_{obj_id}", source_id))
    for i in range(0, len(objects_data), 500):
        db.conn.executemany("INSERT OR IGNORE INTO objects VALUES (?, ?, ?)", objects_data[i:i+500])
    db.conn.commit()

    print("Проверка дискового буфера...")
    leftover_files = glob.glob("disk_buffer_source_*.json")
    if leftover_files:
        print(f"Найдено {len(leftover_files)} файлов. Восстанавливаем...")
        for f in leftover_files:
            src_id = int(f.split('_')[-1].split('.')[0])
            temp_source = BaseDataSource(src_id, 0, 0, [])
            temp_source._buffer_file = f
            recovered = JournalManager.process_disk_buffer(temp_source, db)
            print(f"  -> Восстановлено {recovered} записей из {f}")
    else:
        print("  -> Несохраненных данных не найдено.")

    sources = [
        ComputeSource(1, 1, 1000, list(range(4001, 4021))),
        DatabaseSource(2, 1001, 2000, list(range(4001, 4021))),
        NetworkSource(3, 2001, 3000, list(range(4001, 4021))),
        ApplicationSource(4, 3001, 4000, list(range(4001, 4021)))
    ]

    print("\nГенератор запущен. Данные сохраняются в БД.")
    print("Не закрывайте это окно — генератор должен работать постоянно.\n")

    tasks = [asyncio.create_task(producer(src)) for src in sources]
    tasks.append(asyncio.create_task(consumer(sources, db)))

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        print("\n=== Завершение работы ===")
        for src in sources:
            JournalManager.process_disk_buffer(src, db)
        print(f"\n ВСЕГО СГЕНЕРИРОВАНО И СОХРАНЕНО:")
        print(f"   Скаляров: {total_generated['scalars']:,}")
        print(f"   Трендов:  {total_generated['trends']:,}")
        print(f"   Итого:    {total_generated['scalars'] + total_generated['trends']:,}")
        db.close()
        print("\nГенератор остановлен.")


if __name__ == "__main__":
    try:
        import sys
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass
    asyncio.run(main())