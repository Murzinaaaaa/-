import sqlite3
from datetime import datetime
import os

DB_FILE = "saas_monitoring.db"


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def main():
    if not os.path.exists(DB_FILE):
        print(f"Файл {DB_FILE} не найден!")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    while True:
        print("\n" + "-" * 60)
        print("  ПРОСМОТР БАЗЫ ДАННЫХ saas_monitoring.db")
        print("-" * 60)
        print("  1. Общая статистика")
        print("  2. Таблица trends (20 трендов)")
        print("  3. Таблица objects (первые 20 из 4000)")
        print("  4. Последние 15 трендовых записей")
        print("  5. Последние 15 скалярных записей")
        print("  6. Поиск по тренду (по номеру)")
        print("  7. Выйти")
        print("-" * 60)

        choice = input("\nВыберите пункт (1-7): ").strip()

        if choice == "1":
            print_header("ОБЩАЯ СТАТИСТИКА")
            tables = ["source_types", "objects", "trends", "scalar_log", "trend_log"]
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table:15} -> {count:>8,} записей")

            size_mb = os.path.getsize(DB_FILE) / (1024 * 1024)
            print(f"\n  Размер файла БД: {size_mb:.2f} МБ")

        elif choice == "2":
            print_header("ТАБЛИЦА TRENDS (20 KPI)")
            cursor.execute("SELECT id, name, description FROM trends ORDER BY id")
            print(f"  {'ID':<6} {'Название':<20} {'Описание'}")
            print("  " + "-" * 56)
            for tid, name, desc in cursor.fetchall():
                print(f"  {tid:<6} {name:<20} {desc}")

        elif choice == "3":
            print_header("ТАБЛИЦА OBJECTS (первые 20 из 4000)")
            cursor.execute("""
                SELECT o.id, o.name, st.name
                FROM objects o
                JOIN source_types st ON o.source_type_id = st.id
                ORDER BY o.id LIMIT 20
            """)
            print(f"  {'ID':<6} {'Имя объекта':<20} {'Источник'}")
            print("  " + "-" * 40)
            for oid, name, stype in cursor.fetchall():
                print(f"  {oid:<6} {name:<20} {stype}")
            print("\n  ... и ещё 3980 объектов")

        elif choice == "4":
            print_header("ПОСЛЕДНИЕ 15 ТРЕНДОВЫХ ЗАПИСЕЙ")
            cursor.execute("""
                SELECT t.name, tl.value, tl.timestamp
                FROM trend_log tl
                JOIN trends t ON tl.trend_id = t.id
                ORDER BY tl.id DESC LIMIT 15
            """)
            print(f"  {'Тренд':<18} {'Значение':<12} {'Время'}")
            print("  " + "-" * 50)
            for name, value, ts in cursor.fetchall():
                time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                print(f"  {name:<18} {value:<12.2f} {time_str}")

        elif choice == "5":
            print_header("ПОСЛЕДНИЕ 15 СКАЛЯРНЫХ ЗАПИСЕЙ")
            cursor.execute("""
                SELECT object_id, value, timestamp
                FROM scalar_log
                ORDER BY id DESC LIMIT 15
            """)
            print(f"  {'Объект ID':<12} {'Значение':<12} {'Время'}")
            print("  " + "-" * 40)
            for oid, value, ts in cursor.fetchall():
                time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                print(f"  {oid:<12} {value:<12.2f} {time_str}")

        elif choice == "6":
            print_header("ПОИСК ПО ТРЕНДУ")
            cursor.execute("SELECT id, name FROM trends ORDER BY id")
            print("  Доступные тренды:")
            for tid, name in cursor.fetchall():
                print(f"    {tid} - {name}")

            tid_input = input("\n  Введите ID тренда (4001-4020): ").strip()
            try:
                tid = int(tid_input)
                cursor.execute("""
                    SELECT value, timestamp FROM trend_log
                    WHERE trend_id = ?
                    ORDER BY id DESC LIMIT 20
                """, (tid,))
                rows = cursor.fetchall()
                if rows:
                    print(f"\n  Последние 20 записей тренда #{tid}:")
                    print(f"  {'Значение':<12} {'Время'}")
                    print("  " + "-" * 30)
                    for value, ts in rows:
                        time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                        print(f"  {value:<12.2f} {time_str}")
                else:
                    print(f"\n  По тренду #{tid} записей не найдено")
            except ValueError:
                print("  Введите число!")

        elif choice == "7":
            print("\n  До свидания!\n")
            break

        else:
            print("  Неверный выбор, попробуйте снова")

    conn.close()


if __name__ == "__main__":
    main()