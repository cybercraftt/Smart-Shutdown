import os
import sys
import time
import threading
import re
import psutil
import customtkinter as ctk

# Настройка внешнего вида UI
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def get_minutes_declension(n):
    """Возвращает правильную форму слова 'минута' для числительного."""
    if 11 <= n % 100 <= 19:
        return "минут"
    remainder = n % 10
    if remainder == 1:
        return "минуту"
    if 2 <= remainder <= 4:
        return "минуты"
    return "минут"

class AutoShutdownApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Creator's Smart Shutdown v1.0")
        self.geometry("540x720")
        self.resizable(False, False)

        # ХИТРАЯ ПРОВЕРКА ИКОНКИ ДЛЯ PORTABLE (.EXE) ВЕРСИИ
        try:
            if getattr(sys, 'frozen', False):
                # Если это собранный .exe, берём иконку прямо из самого исполняемого файла
                self.iconbitmap(sys.executable)
            else:
                # Если запускаем просто как скрипт .py
                if os.path.exists("icon.ico"):
                    self.iconbitmap("icon.ico")
        except Exception:
            pass

        # Переменные управления
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Настройки по умолчанию
        self.default_threshold_kb = 300.0  
        self.default_idle_time = 60        
        self.chosen_max_time_minutes = 0  # Страховка по умолчанию отключена

        # --- Элементы интерфейса ---
        
        # Главный статус
        self.status_label = ctk.CTkLabel(self, text="Статус: Ожидание запуска", font=("Arial", 16, "bold"), text_color="gray")
        self.status_label.pack(pady=15)

        # Спидометр
        self.speed_label = ctk.CTkLabel(self, text="0.00 Кб/с", font=("Arial", 32, "bold"))
        self.speed_label.pack(pady=5)
        
        self.info_label = ctk.CTkLabel(self, text="Текущая скорость отдачи сети", font=("Arial", 11), text_color="gray")
        self.info_label.pack(pady=2)

        # Разделитель
        frame_sep = ctk.CTkFrame(self, height=2, fg_color="gray30")
        frame_sep.pack(fill="x", padx=20, pady=15)

        # --- Блок настроек с описаниями ---
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(padx=25, fill="x")

        # Настройка 1: Порог скорости
        row1 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        ctk.CTkLabel(row1, text="Порог окончания загрузки:", font=("Arial", 13, "bold")).pack(side="left")
        self.speed_entry = ctk.CTkEntry(row1, width=70)
        self.speed_entry.insert(0, str(self.default_threshold_kb))
        self.speed_entry.pack(side="right", padx=5)
        ctk.CTkLabel(row1, text="Кб/с").pack(side="right")
        
        self.desc1 = ctk.CTkLabel(settings_frame, text="Если скорость отдачи падает ниже этого уровня, программа понимает,\nчто загрузка видео или архива на сервер завершилась.", 
                                  font=("Arial", 11), text_color="gray70", justify="left")
        self.desc1.pack(anchor="w", pady=(0, 10), padx=5)

        # Настройка 2: Время удержания
        row2 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row2.pack(fill="x", pady=5)
        ctk.CTkLabel(row2, text="Время проверки простоя:", font=("Arial", 13, "bold")).pack(side="left")
        self.idle_entry = ctk.CTkEntry(row2, width=70)
        self.idle_entry.insert(0, str(self.default_idle_time))
        self.idle_entry.pack(side="right", padx=5)
        ctk.CTkLabel(row2, text="сек.").pack(side="right")
        
        self.desc2 = ctk.CTkLabel(settings_frame, text="Защита от просадок интернета. Компьютер не выключится сразу при лаге,\nскорость должна быть стабильно низкой на протяжении этого времени.", 
                                  font=("Arial", 11), text_color="gray70", justify="left")
        self.desc2.pack(anchor="w", pady=(0, 10), padx=5)

        # Настройка 3: Умный Жесткий таймер (Страховка)
        row3 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        row3.pack(fill="x", pady=5)
        ctk.CTkLabel(row3, text="Таймер-страховка ПК:", font=("Arial", 13, "bold"), text_color="#FF9500").pack(side="left")
        
        self.timer_entry = ctk.CTkEntry(row3, width=150, placeholder_text="0 - отключено")
        self.timer_entry.insert(0, "0") 
        self.timer_entry.pack(side="left", padx=10)
        
        self.timer_preview_label = ctk.CTkLabel(row3, text="Страховка отключена", font=("Arial", 12, "bold"), text_color="gray")
        self.timer_preview_label.pack(side="left")
        
        self.timer_entry.bind("<KeyRelease>", self.on_timer_input_change)
        
        self.desc3 = ctk.CTkLabel(settings_frame, text="ЖЕСТКИЙ РУБИЛЬНИК (ВЫСШИЙ ПРИОРИТЕТ). По умолчанию выключен (0).\nЕсли включить (например, написать '2 часа'), ПК гарантированно выключится\nчерез это время в любом случае, даже если сеть будет забита на 100%.", 
                                  font=("Arial", 11, "bold"), text_color="#FF9500", justify="left")
        self.desc3.pack(anchor="w", pady=(0, 10), padx=5)

        # Текстовый блок динамических логов
        self.log_label = ctk.CTkLabel(self, text="Программа работает полностью по трафику сети.", font=("Arial", 12), text_color="cyan")
        self.log_label.pack(pady=15)

        # Кнопки управления
        self.btn_start = ctk.CTkButton(self, text="Включить авто-мониторинг", font=("Arial", 14, "bold"), height=42, command=self.toggle_monitoring)
        self.btn_start.pack(pady=5, padx=30, fill="x")

        self.btn_cancel_shutdown = ctk.CTkButton(self, text="ОТМЕНИТЬ ВЫКЛЮЧЕНИЕ ПК", font=("Arial", 13, "bold"), height=40, fg_color="darkred", hover_color="red", command=self.abort_system_shutdown)

    def parse_time_string(self, text):
        """Разборщик живой речи в чистые минуты."""
        text = text.lower().strip()
        if not text or text == "0" or text == "откл":
            return 0
            
        if text.isdigit():
            return int(text)
            
        replacements = {
            "полтора часа": "1.5 часа",
            "полтора": "1.5 часа",
            "полчаса": "30 минут",
            "один час": "1 час",
            "один": "1",
            "два часа": "2 часа",
            "два": "2",
            "три часа": "3 часа",
            "три": "3",
            "четыре часа": "4 часа",
            "четыре": "4",
            "пять часов": "5 часов",
            "пять": "5"
        }
        
        for word, rep in replacements.items():
            if word in text:
                text = text.replace(word, rep)
                
        hours = 0.0
        minutes = 0.0
        
        hour_match = re.search(r'([0-9.]+)\s*(?:час|ч)', text)
        min_match = re.search(r'([0-9.]+)\s*(?:мин|м)', text)
        
        if hour_match:
            try: hours = float(hour_match.group(1))
            except ValueError: pass
        if min_match:
            try: minutes = float(min_match.group(1))
            except ValueError: pass
            
        total_minutes = int(hours * 60 + minutes)
        
        if total_minutes == 0:
            digits = re.search(r'([0-9.]+)', text)
            if digits:
                try: total_minutes = int(float(digits.group(1)))
                except ValueError: pass
                
        return total_minutes

    def on_timer_input_change(self, event):
        """Мгновенно показывает пользователю чистые цифры при вводе текста."""
        raw_text = self.timer_entry.get()
        parsed_min = self.parse_time_string(raw_text)
        
        if parsed_min > 0:
            self.chosen_max_time_minutes = parsed_min
            word = get_minutes_declension(parsed_min)
            self.timer_preview_label.configure(text=f"Выключится через {parsed_min} {word}", text_color="green")
        else:
            self.chosen_max_time_minutes = 0
            self.timer_preview_label.configure(text="Страховка отключена", text_color="gray")

    def toggle_monitoring(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            self.btn_start.configure(text="Остановить ручной контроль", fg_color="gray40", hover_color="gray50")
            self.status_label.configure(text="Статус: Мониторинг запущен", text_color="green")
            
            self.timer_entry.configure(state="disabled")
            
            try:
                self.threshold_bytes = float(self.speed_entry.get()) * 1024
                self.idle_limit = int(self.idle_entry.get())
                self.max_time_seconds = self.chosen_max_time_minutes * 60
            except ValueError:
                self.log_label.configure(text="Ошибка данных порога скорости!", text_color="red")
                self.threshold_bytes = self.default_threshold_kb * 1024
                self.idle_limit = self.default_idle_time
                self.max_time_seconds = 0

            self.monitor_thread = threading.Thread(target=self.network_monitor_loop, daemon=True)
            self.monitor_thread.start()
        else:
            self.is_monitoring = False
            self.timer_entry.configure(state="normal")
            self.btn_start.configure(text="Включить авто-мониторинг", fg_color=["#3B8ED0", "#1F6AA5"])
            self.status_label.configure(text="Статус: Остановлен", text_color="gray")
            self.speed_label.configure(text="0.00 Кб/с")
            self.log_label.configure(text="Мониторинг сброшен пользователем.", text_color="yellow")

    def network_monitor_loop(self):
        start_time = time.time()
        idle_counter = 0

        while self.is_monitoring:
            net_start = psutil.net_io_counters()
            bytes_start = net_start.bytes_sent
            time.sleep(1)
            net_end = psutil.net_io_counters()
            bytes_end = net_end.bytes_sent
            
            current_speed_bytes = bytes_end - bytes_start
            current_speed_kb = current_speed_bytes / 1024
            
            if current_speed_kb > 1024:
                self.speed_label.configure(text=f"{current_speed_kb/1024:.2f} Мб/с")
            else:
                self.speed_label.configure(text=f"{current_speed_kb:.2f} Кб/с")

            # 1. Проверка жесткого таймера-страховки
            elapsed_time = time.time() - start_time
            remaining_time_min = 0
            
            if self.max_time_seconds > 0:
                remaining_time_min = max(0, int((self.max_time_seconds - elapsed_time) / 60))
                word = get_minutes_declension(remaining_time_min)
                self.timer_preview_label.configure(text=f"Выключится через {remaining_time_min} {word}")
                
                if elapsed_time >= self.max_time_seconds:
                    self.trigger_shutdown("Сработала железная страховка времени!")
                    break

            # 2. Проверка падения трафика
            if current_speed_bytes < self.threshold_bytes:
                idle_counter += 1
            else:
                idle_counter = 0
                
            time_info = f" | До страховки: {remaining_time_min} мин." if self.max_time_seconds > 0 else " | Страховка: Откл."
            self.log_label.configure(
                text=f"Падение трафика: {idle_counter} из {self.idle_limit} сек.{time_info}",
                text_color="orange" if idle_counter > 0 else "cyan"
            )

            if idle_counter >= self.idle_limit:
                self.trigger_shutdown("Выгрузка успешно завершена (трафик упал).")
                break

    def trigger_shutdown(self, reason):
        self.is_monitoring = False
        self.status_label.configure(text="СТАТУС: ВЫКЛЮЧЕНИЕ СИСТЕМЫ", text_color="red")
        self.log_label.configure(text=f"{reason}\nКомпьютер завершит работу через 60 сек!", text_color="#FF3B30")
        self.btn_start.pack_forget()
        self.btn_cancel_shutdown.pack(pady=10, padx=30, fill="x")
        
        if sys.platform == "win32":
            os.system("shutdown /s /t 60")

    def abort_system_shutdown(self):
        if sys.platform == "win32":
            os.system("shutdown /a")
        self.timer_entry.configure(state="normal")
        
        if self.chosen_max_time_minutes > 0:
            word = get_minutes_declension(self.chosen_max_time_minutes)
            self.timer_preview_label.configure(text=f"Выключится через {self.chosen_max_time_minutes} {word}", text_color="green")
        else:
            self.timer_preview_label.configure(text="Страховка отключена", text_color="gray")
            
        self.btn_cancel_shutdown.pack_forget()
        self.btn_start.pack(pady=5, padx=30, fill="x")
        self.btn_start.configure(text="Включить авто-мониторинг", fg_color=["#3B8ED0", "#1F6AA5"])
        self.status_label.configure(text="Статус: Отменено пользователем", text_color="gray")
        self.log_label.configure(text="Выключение ПК успешно отменено. Параметры сброшены.", text_color="green")

if __name__ == "__main__":
    app = AutoShutdownApp()
    app.mainloop()