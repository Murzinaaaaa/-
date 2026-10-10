import tkinter as tk
from tkinter import ttk
import sqlite3
import os
from datetime import datetime


class TrendViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Мониторинг трендов SaaS")
        self.root.geometry("950x650")
        self.root.configure(bg="#f5f5f5")

        self.db_path = "saas_monitoring.db"

        self.create_ui()
        self.refresh()
        self.auto_update()

    def create_ui(self):
        header = tk.Frame(self.root, bg="#2c3e50", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="  Мониторинг трендов SaaS-платформы",
                font=("Segoe UI", 13, "bold"), bg="#2c3e50", fg="white",
                anchor="w").pack(fill=tk.X, side=tk.LEFT)

        self.status_label = tk.Label(header, text="● Активно",
                                    font=("Segoe UI", 10), bg="#2c3e50", fg="#2ecc71")
        self.status_label.pack(side=tk.RIGHT, padx=20)

        stats_frame = tk.Frame(self.root, bg="#ecf0f1", height=80)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        stats_frame.pack_propagate(False)

        self.stats_labels = {}
        stats_items = [
            ("Объектов", "objects_count"),
            ("Трендов", "trends_count"),
            ("Скаляров в БД", "scalars_count"),
            ("Трендов в БД", "trends_log_count")
        ]

        for label, key in stats_items:
            frame = tk.Frame(stats_frame, bg="#ecf0f1")
            frame.pack(side=tk.LEFT, expand=True, fill=tk.Y, padx=10, pady=10)

            tk.Label(frame, text=label, font=("Segoe UI", 9),
                    bg="#ecf0f1", fg="#7f8c8d").pack()
            lbl = tk.Label(frame, text="0", font=("Segoe UI", 16, "bold"),
                          bg="#ecf0f1", fg="#2c3e50")
            lbl.pack()
            self.stats_labels[key] = lbl

        btn_frame = tk.Frame(self.root, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X, padx=10)

        tk.Button(btn_frame, text="Обновить", command=self.refresh,
                 font=("Segoe UI", 10), bg="#3498db", fg="white",
                 activebackground="#2980b9", bd=0, padx=15, pady=5).pack(side=tk.LEFT)

        tk.Button(btn_frame, text="Очистить БД", command=self.clear_db,
                 font=("Segoe UI", 10), bg="#e74c3c", fg="white",
                 activebackground="#c0392b", bd=0, padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        table_frame = tk.Frame(self.root, bg="#f5f5f5")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        headers_frame = tk.Frame(table_frame, bg="#34495e", height=30)
        headers_frame.pack(fill=tk.X)
        headers_frame.pack_propagate(False)

        headers = [("ID", 70), ("Название", 180), ("Описание", 280),
                   ("Значение", 130), ("Время", 130)]

        for text, width in headers:
            tk.Label(headers_frame, text=text, font=("Segoe UI", 9, "bold"),
                    bg="#34495e", fg="white", width=width // 7, anchor="w").pack(side=tk.LEFT)

        canvas_frame = tk.Frame(table_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def get_db(self):
        return sqlite3.connect(self.db_path)

    def refresh(self):
        try:
            if not os.path.exists(self.db_path):
                self.status_label.config(text="● БД не найдена", fg="#e74c3c")
                return

            conn = self.get_db()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM objects")
            self.stats_labels["objects_count"].config(text=f"{cursor.fetchone()[0]:,}")

            cursor.execute("SELECT COUNT(*) FROM trends")
            self.stats_labels["trends_count"].config(text=f"{cursor.fetchone()[0]}")

            cursor.execute("SELECT COUNT(*) FROM scalar_log")
            self.stats_labels["scalars_count"].config(text=f"{cursor.fetchone()[0]:,}")

            cursor.execute("SELECT COUNT(*) FROM trend_log")
            self.stats_labels["trends_log_count"].config(text=f"{cursor.fetchone()[0]:,}")

            cursor.execute("SELECT id, name, description FROM trends ORDER BY id")
            trends = cursor.fetchall()

            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            for idx, (trend_id, name, description) in enumerate(trends):
                cursor.execute("""
                    SELECT value, timestamp FROM trend_log
                    WHERE trend_id = ? ORDER BY id DESC LIMIT 1
                """, (trend_id,))
                result = cursor.fetchone()

                if result:
                    value, timestamp = result
                    value_str = f"{value:.2f}"
                    time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                else:
                    value_str = "—"
                    time_str = "—"

                bg_color = "#ffffff" if idx % 2 == 0 else "#f8f9fa"

                row_frame = tk.Frame(self.scrollable_frame, bg=bg_color)
                row_frame.pack(fill=tk.X)

                tk.Label(row_frame, text=str(trend_id), font=("Segoe UI", 9),
                        bg=bg_color, width=10, anchor="w").pack(side=tk.LEFT)
                tk.Label(row_frame, text=name, font=("Segoe UI", 9, "bold"),
                        bg=bg_color, width=26, anchor="w").pack(side=tk.LEFT)
                tk.Label(row_frame, text=description, font=("Segoe UI", 9),
                        bg=bg_color, width=40, anchor="w").pack(side=tk.LEFT)

                val_color = "#27ae60" if result and 100 <= value <= 600 else "#e74c3c"
                tk.Label(row_frame, text=value_str, font=("Segoe UI", 9, "bold"),
                        bg=bg_color, fg=val_color, width=18, anchor="w").pack(side=tk.LEFT)
                tk.Label(row_frame, text=time_str, font=("Segoe UI", 9),
                        bg=bg_color, fg="#7f8c8d", width=18, anchor="w").pack(side=tk.LEFT)

            conn.close()
            self.status_label.config(text="● Обновлено", fg="#2ecc71")

        except Exception as e:
            self.status_label.config(text=f"● Ошибка: {e}", fg="#e74c3c")

    def clear_db(self):
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scalar_log")
            cursor.execute("DELETE FROM trend_log")
            conn.commit()
            conn.close()
            self.refresh()
        except Exception as e:
            print(f"Ошибка: {e}")

    def auto_update(self):
        self.refresh()
        self.root.after(2000, self.auto_update)


if __name__ == "__main__":
    root = tk.Tk()
    app = TrendViewer(root)
    root.mainloop()