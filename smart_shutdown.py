import os
import sys
import time
import threading
import re
import json
import psutil
import webbrowser
import customtkinter as ctk

if sys.platform == "win32":
    import winsound
    import ctypes

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

CONFIG_FILE = "window_config.json"

ctk.set_appearance_mode("Dark")

def get_minutes_declension(n):
    if 11 <= n % 100 <= 19:
        return "минут"
    remainder = n % 10
    if remainder == 1:
        return "минуту"
    if 2 <= remainder <= 4:
        return "минуты"
    return "минут"

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def create_tray_icon():
    image = Image.new('RGB', (64, 64), color=(11, 12, 16))
    dc = ImageDraw.Draw(image)
    dc.ellipse((16, 16, 48, 48), fill=(99, 102, 241))
    return image

class AutoShutdownApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Регистрация AppUserModelID для отображения иконки на панели задач Windows
        if sys.platform == "win32":
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CyberCraft.SmartShutdown.App.1.0")
            except Exception:
                pass

        self.title("Creator's Smart Shutdown")
        self.is_monitoring = False
        self.monitor_thread = None
        self.tray_icon = None

        self.CARD_BG = "#14151C"
        self.CARD_BORDER = "#232533"
        self.ACCENT_COLOR = "#6366F1"
        self.ACCENT_HOVER = "#4F46E5"

        # Установка иконки приложения
        icon_path = get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.setup_ui()
        self.load_config()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        self.configure(fg_color="#0B0C10")

        # --- СТАТУС-ДАШБОРД ---
        status_card = ctk.CTkFrame(
            self, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=14
        )
        status_card.pack(fill="x", padx=16, pady=(16, 8))

        status_box = ctk.CTkFrame(status_card, fg_color="#1E202E", corner_radius=20)
        status_box.pack(pady=(10, 4), padx=12)

        self.status_label = ctk.CTkLabel(
            status_box, text="● Ожидание запуска", font=("Segoe UI", 12, "bold"), text_color="#9CA3AF"
        )
        self.status_label.pack(padx=12, pady=4)

        self.speed_label = ctk.CTkLabel(
            status_card, text="0.00 Кб/с", font=("Segoe UI", 32, "bold"), text_color="#F3F4F6"
        )
        self.speed_label.pack(pady=0)

        self.info_label = ctk.CTkLabel(
            status_card, text="Текущая скорость сети", font=("Segoe UI", 10), text_color="#6B7280"
        )
        self.info_label.pack(pady=(2, 10))

        # --- НАСТРОЙКИ ---
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(padx=16, fill="x", pady=2)

        row1 = ctk.CTkFrame(
            settings_frame, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=10
        )
        row1.pack(fill="x", pady=3, ipady=3, ipadx=8)

        ctk.CTkLabel(row1, text="Порог:", font=("Segoe UI", 12, "bold"), text_color="#E5E7EB").pack(side="left", padx=5)

        self.traffic_dir_option = ctk.CTkOptionMenu(
            row1, values=["Отдача (Upload)", "Загрузка (Download)"], width=135, height=26,
            font=("Segoe UI", 11), fg_color="#0B0C10", button_color="#1E202E", button_hover_color="#282A3D",
            text_color="#F3F4F6"
        )
        self.traffic_dir_option.pack(side="left", padx=4)

        ctk.CTkLabel(row1, text="Кб/с", font=("Segoe UI", 11), text_color="#6B7280").pack(side="right", padx=(2, 5))
        self.speed_entry = ctk.CTkEntry(
            row1, width=65, height=28, font=("Segoe UI", 12), fg_color="#0B0C10", border_color=self.CARD_BORDER, text_color="#F3F4F6"
        )
        self.speed_entry.insert(0, "300.0")
        self.speed_entry.pack(side="right", padx=2)

        row2 = ctk.CTkFrame(
            settings_frame, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=10
        )
        row2.pack(fill="x", pady=3, ipady=3, ipadx=8)

        ctk.CTkLabel(row2, text="Время простоя:", font=("Segoe UI", 12, "bold"), text_color="#E5E7EB").pack(side="left", padx=5)
        ctk.CTkLabel(row2, text="сек.", font=("Segoe UI", 11), text_color="#6B7280").pack(side="right", padx=(2, 5))
        self.idle_entry = ctk.CTkEntry(
            row2, width=65, height=28, font=("Segoe UI", 12), fg_color="#0B0C10", border_color=self.CARD_BORDER, text_color="#F3F4F6"
        )
        self.idle_entry.insert(0, "60")
        self.idle_entry.pack(side="right", padx=2)

        row_action = ctk.CTkFrame(
            settings_frame, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=10
        )
        row_action.pack(fill="x", pady=3, ipady=3, ipadx=8)

        ctk.CTkLabel(row_action, text="Действие ПК:", font=("Segoe UI", 12, "bold"), text_color="#E5E7EB").pack(side="left", padx=5)
        self.action_option = ctk.CTkOptionMenu(
            row_action, values=["Завершение работы", "Сон / Гибернация", "Перезагрузка"], width=170, height=26,
            font=("Segoe UI", 11), fg_color="#0B0C10", button_color="#1E202E", button_hover_color="#282A3D",
            text_color="#F3F4F6"
        )
        self.action_option.pack(side="right", padx=2)

        row3 = ctk.CTkFrame(
            settings_frame, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=10
        )
        row3.pack(fill="x", pady=3, ipady=3, ipadx=8)

        ctk.CTkLabel(row3, text="Страховка ПК:", font=("Segoe UI", 12, "bold"), text_color="#F59E0B").pack(side="left", padx=5)
        self.timer_entry = ctk.CTkEntry(
            row3, width=80, height=28, font=("Segoe UI", 12), placeholder_text="0 - откл",
            fg_color="#0B0C10", border_color=self.CARD_BORDER, text_color="#F3F4F6"
        )
        self.timer_entry.insert(0, "0")
        self.timer_entry.pack(side="left", padx=5)

        self.timer_preview_label = ctk.CTkLabel(row3, text="Отключена", font=("Segoe UI", 11), text_color="#6B7280")
        self.timer_preview_label.pack(side="right", padx=5)
        self.timer_entry.bind("<KeyRelease>", self.on_timer_input_change)

        self.desc3 = ctk.CTkLabel(
            settings_frame, text="⚡ Выполнит действие через указанное время независимо от сети",
            font=("Segoe UI", 10), text_color="#F59E0B", anchor="w"
        )
        self.desc3.pack(fill="x", padx=6, pady=(1, 3))

        row_sound = ctk.CTkFrame(
            settings_frame, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=10
        )
        row_sound.pack(fill="x", pady=3, ipady=3, ipadx=8)

        ctk.CTkLabel(row_sound, text="Звуковое оповещение:", font=("Segoe UI", 12, "bold"), text_color="#E5E7EB").pack(side="left", padx=5)
        self.sound_switch = ctk.CTkSwitch(
            row_sound, text="Вкл", font=("Segoe UI", 11), progress_color=self.ACCENT_COLOR, text_color="#9CA3AF"
        )
        self.sound_switch.select()
        self.sound_switch.pack(side="right", padx=5)

        # Отдельная кнопка сворачивания в трей внизу интерфейса
        if TRAY_AVAILABLE:
            btn_tray = ctk.CTkButton(
                settings_frame, text="Свернуть в трей 📌", font=("Segoe UI", 11), height=28,
                fg_color="#1E202E", hover_color="#282A3D", text_color="#9CA3AF",
                border_width=1, border_color="#282A3D", command=self.hide_to_tray
            )
            btn_tray.pack(fill="x", pady=(4, 0))

        # --- ИНФО-ЛОГ И КНОПКИ ---
        self.log_label = ctk.CTkLabel(
            self, text="Мониторинг сети готов к запуску", font=("Segoe UI", 11), text_color="#06B6D4"
        )
        self.log_label.pack(pady=6)

        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(pady=2, padx=16, fill="x")

        self.btn_start = ctk.CTkButton(
            btn_container, text="Включить авто-мониторинг", font=("Segoe UI", 13, "bold"), height=40,
            corner_radius=10, fg_color=self.ACCENT_COLOR, hover_color=self.ACCENT_HOVER, command=self.toggle_monitoring
        )
        self.btn_start.pack(expand=True, fill="x")

        self.btn_cancel_shutdown = ctk.CTkButton(
            self, text="ОТМЕНИТЬ ДЕЙСТВИЕ ПК", font=("Segoe UI", 12, "bold"), height=40,
            corner_radius=10, fg_color="#DC2626", hover_color="#B91C1C", command=self.abort_system_shutdown
        )

        # --- ФУТЕР ---
        links_frame = ctk.CTkFrame(self, fg_color="transparent")
        links_frame.pack(side="bottom", pady=12)

        ctk.CTkLabel(links_frame, text="Поддержка проекта", font=("Segoe UI", 10), text_color="#4B5563").pack(pady=(0, 4))

        btn_box = ctk.CTkFrame(links_frame, fg_color="transparent")
        btn_box.pack()

        yt_btn = ctk.CTkButton(
            btn_box, text="YouTube", font=("Segoe UI", 11, "bold"), width=95, height=28, corner_radius=8,
            fg_color="#1E202E", hover_color="#282A3D", text_color="#EF4444", border_width=1, border_color="#282A3D",
            command=lambda: webbrowser.open("https://www.youtube.com/channel/UCcGfKjP4XdfkLokNgVOIAyA")
        )
        yt_btn.pack(side="left", padx=3)

        tg_btn = ctk.CTkButton(
            btn_box, text="Telegram", font=("Segoe UI", 11, "bold"), width=95, height=28, corner_radius=8,
            fg_color="#1E202E", hover_color="#282A3D", text_color="#38BDF8", border_width=1, border_color="#282A3D",
            command=lambda: webbrowser.open("https://t.me/CyberCraftLab")
        )
        tg_btn.pack(side="left", padx=3)

        boosty_btn = ctk.CTkButton(
            btn_box, text="Boosty", font=("Segoe UI", 11, "bold"), width=95, height=28, corner_radius=8,
            fg_color="#1E202E", hover_color="#282A3D", text_color="#FB923C", border_width=1, border_color="#282A3D",
            command=lambda: webbrowser.open("https://boosty.to/cyber_craft")
        )
        boosty_btn.pack(side="left", padx=3)

    # --- СОХРАНЕНИЕ / ЗАГРУЗКА ---
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.geometry(cfg.get("geometry", "450x640"))
                    
                    self.speed_entry.delete(0, "end")
                    self.speed_entry.insert(0, str(cfg.get("threshold_kb", "300.0")))

                    self.idle_entry.delete(0, "end")
                    self.idle_entry.insert(0, str(cfg.get("idle_time", "60")))

                    self.timer_entry.delete(0, "end")
                    self.timer_entry.insert(0, str(cfg.get("timer_raw", "0")))
                    self.on_timer_input_change(None)

                    dir_val = cfg.get("traffic_dir", "Отдача (Upload)")
                    if dir_val in ["Отдача (Upload)", "Загрузка (Download)"]:
                        self.traffic_dir_option.set(dir_val)

                    act_val = cfg.get("action", "Завершение работы")
                    if act_val in ["Завершение работы", "Сон / Гибернация", "Перезагрузка"]:
                        self.action_option.set(act_val)

                    if not cfg.get("sound_enabled", True):
                        self.sound_switch.deselect()
                    return
            except Exception:
                pass
        self.geometry("450x640")

    def save_config(self):
        try:
            cfg = {
                "geometry": self.geometry(),
                "threshold_kb": self.speed_entry.get(),
                "idle_time": self.idle_entry.get(),
                "timer_raw": self.timer_entry.get(),
                "traffic_dir": self.traffic_dir_option.get(),
                "action": self.action_option.get(),
                "sound_enabled": bool(self.sound_switch.get())
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def on_closing(self):
        self.save_config()
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()

    # --- ТРЕЙ ---
    def hide_to_tray(self):
        if not TRAY_AVAILABLE:
            return
        self.withdraw()
        
        icon_path = get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                icon_img = Image.open(icon_path)
            except Exception:
                icon_img = create_tray_icon()
        else:
            icon_img = create_tray_icon()

        menu = pystray.Menu(
            pystray.MenuItem("Развернуть", self.restore_from_tray, default=True),
            pystray.MenuItem("Выход", self.exit_from_tray)
        )
        self.tray_icon = pystray.Icon("SmartShutdown", icon_img, "Smart Shutdown", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def restore_from_tray(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.deiconify()
        self.state('normal')

    def exit_from_tray(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self.on_closing)

    # --- ЛОГИКА ТАЙМЕРА И МОНИТОРИНГА ---
    def parse_time_string(self, text):
        text = text.lower().strip()
        if not text or text == "0" or text == "откл":
            return 0
        if text.isdigit():
            return int(text)

        replacements = {
            "полтора часа": "1.5 часа", "полтора": "1.5 часа", "полчаса": "30 минут",
            "один час": "1 час", "один": "1", "два часа": "2 часа", "два": "2",
            "три часа": "3 часа", "три": "3", "четыре часа": "4 часа", "четыре": "4",
            "пять часов": "5 часов", "пять": "5"
        }
        for word, rep in replacements.items():
            if word in text:
                text = text.replace(word, rep)

        hours, minutes = 0.0, 0.0
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
        raw_text = self.timer_entry.get()
        parsed_min = self.parse_time_string(raw_text)

        if parsed_min > 0:
            self.chosen_max_time_minutes = parsed_min
            word = get_minutes_declension(parsed_min)
            self.timer_preview_label.configure(text=f"Через {parsed_min} {word}", text_color="#10B981")
        else:
            self.chosen_max_time_minutes = 0
            self.timer_preview_label.configure(text="Отключена", text_color="#6B7280")

    def toggle_monitoring(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            self.btn_start.configure(text="Остановить контроль", fg_color="#374151", hover_color="#4B5563")
            self.status_label.configure(text="● Мониторинг запущен", text_color="#10B981")

            self.timer_entry.configure(state="disabled")
            self.traffic_dir_option.configure(state="disabled")
            self.action_option.configure(state="disabled")
            self.sound_switch.configure(state="disabled")

            try:
                self.threshold_bytes = float(self.speed_entry.get()) * 1024
                self.idle_limit = int(self.idle_entry.get())
                self.max_time_seconds = self.chosen_max_time_minutes * 60
            except ValueError:
                self.log_label.configure(text="Ошибка ввода параметров!", text_color="#EF4444")
                self.threshold_bytes = 300.0 * 1024
                self.idle_limit = 60
                self.max_time_seconds = 0

            self.monitor_thread = threading.Thread(target=self.network_monitor_loop, daemon=True)
            self.monitor_thread.start()
        else:
            self.is_monitoring = False
            self.timer_entry.configure(state="normal")
            self.traffic_dir_option.configure(state="normal")
            self.action_option.configure(state="normal")
            self.sound_switch.configure(state="normal")
            self.btn_start.configure(text="Включить авто-мониторинг", fg_color=self.ACCENT_COLOR, hover_color=self.ACCENT_HOVER)
            self.status_label.configure(text="● Остановлен", text_color="#9CA3AF")
            self.speed_label.configure(text="0.00 Кб/с")
            self.log_label.configure(text="Мониторинг остановлен.", text_color="#F59E0B")

    def network_monitor_loop(self):
        start_time = time.time()
        idle_counter = 0
        check_upload = "Отдача" in self.traffic_dir_option.get()

        while self.is_monitoring:
            net_start = psutil.net_io_counters()
            bytes_start = net_start.bytes_sent if check_upload else net_start.bytes_recv
            time.sleep(1)
            net_end = psutil.net_io_counters()
            bytes_end = net_end.bytes_sent if check_upload else net_end.bytes_recv

            current_speed_bytes = bytes_end - bytes_start
            current_speed_kb = current_speed_bytes / 1024

            if current_speed_kb > 1024:
                self.speed_label.configure(text=f"{current_speed_kb/1024:.2f} Мб/с")
            else:
                self.speed_label.configure(text=f"{current_speed_kb:.2f} Кб/с")

            elapsed_time = time.time() - start_time
            remaining_time_min = 0

            if self.max_time_seconds > 0:
                remaining_time_min = max(0, int((self.max_time_seconds - elapsed_time) / 60))
                word = get_minutes_declension(remaining_time_min)
                self.timer_preview_label.configure(text=f"Через {remaining_time_min} {word}")

                if elapsed_time >= self.max_time_seconds:
                    self.trigger_shutdown("Сработала страховка времени!")
                    break

            if current_speed_bytes < self.threshold_bytes:
                idle_counter += 1
            else:
                idle_counter = 0

            time_info = f" | До страховки: {remaining_time_min} мин." if self.max_time_seconds > 0 else " | Страховка: Откл."
            self.log_label.configure(
                text=f"Падение трафика: {idle_counter} из {self.idle_limit} сек.{time_info}",
                text_color="#F59E0B" if idle_counter > 0 else "#06B6D4"
            )

            if idle_counter >= self.idle_limit:
                self.trigger_shutdown("Падение трафика зафиксировано.")
                break

    def trigger_shutdown(self, reason):
        self.is_monitoring = False
        action_type = self.action_option.get()

        if self.tray_icon:
            self.restore_from_tray()

        if sys.platform == "win32" and self.sound_switch.get() == 1:
            try:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass

        self.status_label.configure(text=f"● ВЫПОЛНЕНИЕ: {action_type.upper()}", text_color="#EF4444")
        self.log_label.configure(text=f"{reason}\nДействие через 60 сек!", text_color="#EF4444")
        self.btn_start.pack_forget()
        self.btn_cancel_shutdown.pack(pady=8, padx=16, fill="x")

        if sys.platform == "win32":
            if action_type == "Завершение работы":
                os.system("shutdown /s /t 60")
            elif action_type == "Перезагрузка":
                os.system("shutdown /r /t 60")
            elif action_type == "Сон / Гибернация":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    def abort_system_shutdown(self):
        if sys.platform == "win32":
            os.system("shutdown /a")

        self.timer_entry.configure(state="normal")
        self.traffic_dir_option.configure(state="normal")
        self.action_option.configure(state="normal")
        self.sound_switch.configure(state="normal")

        if self.chosen_max_time_minutes > 0:
            word = get_minutes_declension(self.chosen_max_time_minutes)
            self.timer_preview_label.configure(text=f"Через {self.chosen_max_time_minutes} {word}", text_color="#10B981")
        else:
            self.timer_preview_label.configure(text="Отключена", text_color="#6B7280")

        self.btn_cancel_shutdown.pack_forget()
        self.btn_start.pack(pady=4, padx=16, fill="x")
        self.btn_start.configure(text="Включить авто-мониторинг", fg_color=self.ACCENT_COLOR, hover_color=self.ACCENT_HOVER)
        self.status_label.configure(text="● Отменено пользователем", text_color="#9CA3AF")
        self.log_label.configure(text="Действие ПК отменено.", text_color="#10B981")

if __name__ == "__main__":
    app = AutoShutdownApp()
    app.mainloop()