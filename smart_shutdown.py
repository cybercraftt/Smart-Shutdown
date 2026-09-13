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

LANGUAGES = {
    "English": {
        "title": "Creator's Smart Shutdown",
        "awaiting_start": "● Awaiting start",
        "monitoring_active": "● Monitoring Active",
        "stopped": "● Stopped",
        "executing": "● EXECUTING:",
        "current_speed": "Current network speed",
        "threshold": "Threshold:",
        "kb_s": "KB/s",
        "idle_time": "Idle time:",
        "sec": "sec.",
        "pc_action": "PC Action:",
        "actions": ["Shutdown", "Sleep / Hibernate", "Restart"],
        "safety_timer": "Safety Timer:",
        "timer_off_hint": "0 - off",
        "disabled": "Disabled",
        "safety_desc": "⚡ Performs action after specified time regardless of network traffic",
        "sound_notif": "Sound Notification:",
        "on": "On",
        "to_tray": "Minimize to Tray 📌",
        "reset_settings": "Reset Settings ↺",
        "net_ready": "Network monitoring ready to start",
        "start_btn": "Enable Auto-Monitoring",
        "stop_btn": "Stop Monitoring",
        "cancel_btn": "CANCEL PC ACTION",
        "project_support": "Project Support",
        "settings_reset": "Settings reset to default",
        "tray_restore": "Restore",
        "tray_exit": "Exit",
        "param_error": "Parameter entry error!",
        "monitoring_stopped_log": "Monitoring stopped.",
        "safety_triggered": "Safety timer triggered!",
        "traffic_drop_detected": "Traffic drop detected.",
        "action_in_60": "Action in 60 sec!",
        "action_canceled_log": "PC action canceled. Monitoring reset.",
        "traffic_drop_fmt": "Traffic drop: {idle} of {limit} sec.",
        "safety_info_fmt": " | Safety timer in: {min} min.",
        "safety_off_info": " | Safety timer: Off",
        "in_minutes_fmt": "In {min} min.",
        "traffic_dirs": ["Upload", "Download"]
    },
    "Русский": {
        "title": "Creator's Smart Shutdown",
        "awaiting_start": "● Ожидание запуска",
        "monitoring_active": "● Мониторинг запущен",
        "stopped": "● Остановлен",
        "executing": "● ВЫПОЛНЕНИЕ:",
        "current_speed": "Текущая скорость сети",
        "threshold": "Порог:",
        "kb_s": "Кб/с",
        "idle_time": "Время простоя:",
        "sec": "сек.",
        "pc_action": "Действие ПК:",
        "actions": ["Завершение работы", "Сон / Гибернация", "Перезагрузка"],
        "safety_timer": "Страховка ПК:",
        "timer_off_hint": "0 - откл",
        "disabled": "Отключена",
        "safety_desc": "⚡ Выполнит действие через указанное время независимо от сети",
        "sound_notif": "Звуковое оповещение:",
        "on": "Вкл",
        "to_tray": "В трей 📌",
        "reset_settings": "Сбросить настройки ↺",
        "net_ready": "Мониторинг сети готов к запуску",
        "start_btn": "Включить авто-мониторинг",
        "stop_btn": "Остановить контроль",
        "cancel_btn": "ОТМЕНИТЬ ДЕЙСТВИЕ ПК",
        "project_support": "Поддержка проекта",
        "settings_reset": "Настройки сброшены по умолчанию",
        "tray_restore": "Развернуть",
        "tray_exit": "Выход",
        "param_error": "Ошибка ввода параметров!",
        "monitoring_stopped_log": "Мониторинг остановлен.",
        "safety_triggered": "Сработала страховка времени!",
        "traffic_drop_detected": "Падение трафика зафиксировано.",
        "action_in_60": "Действие через 60 сек!",
        "action_canceled_log": "Действие ПК отменено. Мониторинг сброшен.",
        "traffic_drop_fmt": "Падение трафика: {idle} из {limit} сек.",
        "safety_info_fmt": " | До страховки: {min} мин.",
        "safety_off_info": " | Страховка: Откл.",
        "in_minutes_fmt": "Через {min} мин.",
        "traffic_dirs": ["Отдача (Upload)", "Загрузка (Download)"]
    },
    "Español": {
        "title": "Creator's Smart Shutdown",
        "awaiting_start": "● Esperando inicio",
        "monitoring_active": "● Monitoreo activo",
        "stopped": "● Detenido",
        "executing": "● EJECUTANDO:",
        "current_speed": "Velocidad de red actual",
        "threshold": "Umbral:",
        "kb_s": "KB/s",
        "idle_time": "Tiempo inactivo:",
        "sec": "seg.",
        "pc_action": "Acción del PC:",
        "actions": ["Apagar", "Suspender / Hibernar", "Reiniciar"],
        "safety_timer": "Temporizador de seguridad:",
        "timer_off_hint": "0 - desact",
        "disabled": "Desactivado",
        "safety_desc": "⚡ Realiza la acción tras el tiempo fijado independientemente de la red",
        "sound_notif": "Notificación de sonido:",
        "on": "Activ",
        "to_tray": "Minimizar a la bandeja 📌",
        "reset_settings": "Restablecer ajustes ↺",
        "net_ready": "Monitoreo de red listo",
        "start_btn": "Activar auto-monitoreo",
        "stop_btn": "Detener monitoreo",
        "cancel_btn": "CANCELAR ACCIÓN DEL PC",
        "project_support": "Soporte del proyecto",
        "settings_reset": "Ajustes restablecidos por defecto",
        "tray_restore": "Restaurar",
        "tray_exit": "Salir",
        "param_error": "¡Error en los parámetros!",
        "monitoring_stopped_log": "Monitoreo detenido.",
        "safety_triggered": "¡Temporizador de seguridad activado!",
        "traffic_drop_detected": "Caída de tráfico detectada.",
        "action_in_60": "¡Acción en 60 seg!",
        "action_canceled_log": "Acción del PC cancelada. Monitoreo reiniciado.",
        "traffic_drop_fmt": "Caída de tráfico: {idle} de {limit} seg.",
        "safety_info_fmt": " | Seg. en: {min} min.",
        "safety_off_info": " | Seg.: Desact.",
        "in_minutes_fmt": "En {min} min.",
        "traffic_dirs": ["Subida (Upload)", "Descarga (Download)"]
    },
    "Deutsch": {
        "title": "Creator's Smart Shutdown",
        "awaiting_start": "● Warten auf Start",
        "monitoring_active": "● Überwachung aktiv",
        "stopped": "● Gestoppt",
        "executing": "● AUSFÜHRUNG:",
        "current_speed": "Aktuelle Netzwerkgeschwindigkeit",
        "threshold": "Schwellenwert:",
        "kb_s": "KB/s",
        "idle_time": "Inaktivitätszeit:",
        "sec": "Sek.",
        "pc_action": "PC-Aktion:",
        "actions": ["Herunterfahren", "Energie sparen / Ruhezustand", "Neustart"],
        "safety_timer": "Sicherheitstimer:",
        "timer_off_hint": "0 - Aus",
        "disabled": "Deaktiviert",
        "safety_desc": "⚡ Führt die Aktion nach Ablauf der Zeit unabhängig vom Netzwerk aus",
        "sound_notif": "Soundbenachrichtigung:",
        "on": "Ein",
        "to_tray": "In den Tray minimieren 📌",
        "reset_settings": "Einstellungen zurücksetzen ↺",
        "net_ready": "Netzwerküberwachung bereit",
        "start_btn": "Auto-Überwachung aktivieren",
        "stop_btn": "Überwachung stoppen",
        "cancel_btn": "PC-AKTION ABBRECHEN",
        "project_support": "Projektunterstützung",
        "settings_reset": "Einstellungen auf Standard zurückgesetzt",
        "tray_restore": "Wiederherstellen",
        "tray_exit": "Beenden",
        "param_error": "Fehler bei der Parametereingabe!",
        "monitoring_stopped_log": "Überwachung gestoppt.",
        "safety_triggered": "Sicherheitstimer ausgelöst!",
        "traffic_drop_detected": "Datenabfall erkannt.",
        "action_in_60": "Aktion in 60 Sek.!",
        "action_canceled_log": "PC-Aktion abgebrochen. Überwachung zurückgesetzt.",
        "traffic_drop_fmt": "Datenabfall: {idle} von {limit} Sek.",
        "safety_info_fmt": " | Sich. in: {min} Min.",
        "safety_off_info": " | Sich.: Aus",
        "in_minutes_fmt": "In {min} Min.",
        "traffic_dirs": ["Upload", "Download"]
    },
    "Français": {
        "title": "Creator's Smart Shutdown",
        "awaiting_start": "● En attente",
        "monitoring_active": "● Surveillance active",
        "stopped": "● Arrêté",
        "executing": "● ÉXÉCUTION:",
        "current_speed": "Vitesse réseau actuelle",
        "threshold": "Seuil:",
        "kb_s": "Ko/s",
        "idle_time": "Temps d'inactivité:",
        "sec": "sec.",
        "pc_action": "Action PC:",
        "actions": ["Éteindre", "Veille / Hibernation", "Redémarrer"],
        "safety_timer": "Minuteur de sécurité:",
        "timer_off_hint": "0 - désact",
        "disabled": "Désactivé",
        "safety_desc": "⚡ Exécute l'action après le délai spécifié indépendamment du réseau",
        "sound_notif": "Notification sonore:",
        "on": "Actif",
        "to_tray": "Réduire dans la barre 📌",
        "reset_settings": "Réinitialiser les paramètres ↺",
        "net_ready": "Surveillance réseau prête",
        "start_btn": "Activer l'auto-surveillance",
        "stop_btn": "Arrêter la surveillance",
        "cancel_btn": "ANNULER L'ACTION DU PC",
        "project_support": "Soutien du projet",
        "settings_reset": "Paramètres réinitialisés par défaut",
        "tray_restore": "Restaurer",
        "tray_exit": "Quitter",
        "param_error": "Erreur de paramètre!",
        "monitoring_stopped_log": "Surveillance arrêtée.",
        "safety_triggered": "Minuteur de sécurité déclenché!",
        "traffic_drop_detected": "Chute de trafic détectée.",
        "action_in_60": "Action dans 60 sec!",
        "action_canceled_log": "Action PC annulée. Surveillance réinitialisée.",
        "traffic_drop_fmt": "Chute de trafic: {idle} sur {limit} sec.",
        "safety_info_fmt": " | Séc. dans: {min} min.",
        "safety_off_info": " | Séc.: Désact.",
        "in_minutes_fmt": "Dans {min} min.",
        "traffic_dirs": ["Envoi (Upload)", "Téléchargement (Download)"]
    },
    "中文": {
        "title": "Creator's Smart Shutdown",
        "awaiting_start": "● 等待启动",
        "monitoring_active": "● 监控运行中",
        "stopped": "● 已停止",
        "executing": "● 正在执行:",
        "current_speed": "当前网络速度",
        "threshold": "阈值:",
        "kb_s": "KB/s",
        "idle_time": "空闲时间:",
        "sec": "秒",
        "pc_action": "电脑操作:",
        "actions": ["关机", "睡眠 / 休眠", "重启"],
        "safety_timer": "安全定时器:",
        "timer_off_hint": "0 - 关闭",
        "disabled": "已禁用",
        "safety_desc": "⚡ 无论网络流量如何，将在指定时间后执行操作",
        "sound_notif": "声音通知:",
        "on": "开启",
        "to_tray": "最小化到托盘 📌",
        "reset_settings": "重置设置 ↺",
        "net_ready": "网络监控准备就绪",
        "start_btn": "开启自动监控",
        "stop_btn": "停止监控",
        "cancel_btn": "取消电脑操作",
        "project_support": "项目支持",
        "settings_reset": "设置已重置为默认值",
        "tray_restore": "还原",
        "tray_exit": "退出",
        "param_error": "参数输入错误！",
        "monitoring_stopped_log": "监控已停止。",
        "safety_triggered": "安全定时器已触发！",
        "traffic_drop_detected": "检测到网络流量下降。",
        "action_in_60": "60秒内执行操作！",
        "action_canceled_log": "电脑操作已取消，监控已重置。",
        "traffic_drop_fmt": "流量下降: {idle} / {limit} 秒",
        "safety_info_fmt": " | 安全倒计时: {min} 分钟",
        "safety_off_info": " | 安全定时器: 未开启",
        "in_minutes_fmt": "{min} 分钟后",
        "traffic_dirs": ["上传 (Upload)", "下载 (Download)"]
    },
    "Português": {
        "title": "Creator's Smart Shutdown",
        "awaiting_start": "● Aguardando início",
        "monitoring_active": "● Monitoramento ativo",
        "stopped": "● Parado",
        "executing": "● EXECUTANDO:",
        "current_speed": "Velocidade de rede atual",
        "threshold": "Limite:",
        "kb_s": "KB/s",
        "idle_time": "Tempo ocioso:",
        "sec": "seg.",
        "pc_action": "Ação do PC:",
        "actions": ["Desligar", "Suspender / Hibernar", "Reiniciar"],
        "safety_timer": "Temporizador de segurança:",
        "timer_off_hint": "0 - desat",
        "disabled": "Desativado",
        "safety_desc": "⚡ Executa a ação após o tempo especificado, independentemente da rede",
        "sound_notif": "Notificação de som:",
        "on": "Lig",
        "to_tray": "Minimizar para a bandeja 📌",
        "reset_settings": "Restaurar configurações ↺",
        "net_ready": "Monitoramento de rede pronto",
        "start_btn": "Ativar auto-monitoramento",
        "stop_btn": "Parar monitoramento",
        "cancel_btn": "CANCELAR AÇÃO DO PC",
        "project_support": "Suporte ao projeto",
        "settings_reset": "Configurações restauradas para o padrão",
        "tray_restore": "Restaurar",
        "tray_exit": "Sair",
        "param_error": "Erro de entrada de parâmetros!",
        "monitoring_stopped_log": "Monitoramento parado.",
        "safety_triggered": "Temporizador de segurança ativado!",
        "traffic_drop_detected": "Queda de tráfego detectada.",
        "action_in_60": "Ação em 60 seg!",
        "action_canceled_log": "Ação do PC cancelada. Monitoramento redefinido.",
        "traffic_drop_fmt": "Queda de tráfego: {idle} de {limit} seg.",
        "safety_info_fmt": " | Seg. em: {min} min.",
        "safety_off_info": " | Seg.: Desat.",
        "in_minutes_fmt": "Em {min} min.",
        "traffic_dirs": ["Envio (Upload)", "Download"]
    },
    "日本語": {
        "title": "Creator's Smart Shutdown",
        "awaiting_start": "● 待機中",
        "monitoring_active": "● 監視中",
        "stopped": "● 停止",
        "executing": "● 実行中:",
        "current_speed": "現在の通信速度",
        "threshold": "しきい値:",
        "kb_s": "KB/s",
        "idle_time": "アイドル時間:",
        "sec": "秒",
        "pc_action": "PCのアクション:",
        "actions": ["シャットダウン", "スリープ / 休止状態", "再起動"],
        "safety_timer": "安全タイマー:",
        "timer_off_hint": "0 - オフ",
        "disabled": "無効",
        "safety_desc": "⚡ ネットワーク状態に関係なく指定時間後に実行します",
        "sound_notif": "音声通知:",
        "on": "オン",
        "to_tray": "トレイに最小化 📌",
        "reset_settings": "設定をリセット ↺",
        "net_ready": "ネットワーク監視の準備完了",
        "start_btn": "自動監視を有効化",
        "stop_btn": "監視を停止",
        "cancel_btn": "PCアクションをキャンセル",
        "project_support": "プロジェクト支援",
        "settings_reset": "設定をデフォルトにリセットしました",
        "tray_restore": "元に戻す",
        "tray_exit": "終了",
        "param_error": "パラメーター入力エラー！",
        "monitoring_stopped_log": "監視が停止しました。",
        "safety_triggered": "安全タイマーが作動しました！",
        "traffic_drop_detected": "トラフィックの低下を検出しました。",
        "action_in_60": "60秒後に実行します！",
        "action_canceled_log": "PCアクションがキャンセルされました。",
        "traffic_drop_fmt": "トラフィック低下: {idle} / {limit} 秒",
        "safety_info_fmt": " | 安全タイマー: 残り{min}分",
        "safety_off_info": " | 安全タイマー: オフ",
        "in_minutes_fmt": "{min}分後",
        "traffic_dirs": ["送信 (Upload)", "受信 (Download)"]
    }
}

DEFAULT_CONFIG = {
    "threshold_kb": "300.0",
    "idle_time": "60",
    "timer_raw": "0",
    "traffic_dir_index": 0,
    "action_index": 0,
    "sound_enabled": True,
    "language": "Русский"
}

ctk.set_appearance_mode("Dark")

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

        if sys.platform == "win32":
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CyberCraft.SmartShutdown.App.1.0")
            except Exception:
                pass

        self.current_lang = DEFAULT_CONFIG["language"]
        self.is_monitoring = False
        self.monitor_thread = None
        self.tray_icon = None
        self.chosen_max_time_minutes = 0

        self.CARD_BG = "#14151C"
        self.CARD_BORDER = "#232533"
        self.ACCENT_COLOR = "#6366F1"
        self.ACCENT_HOVER = "#4F46E5"

        icon_path = get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.center_window(460, 680)
        self.setup_ui()
        self.load_config()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def tr(self, key):
        lang_dict = LANGUAGES.get(self.current_lang, LANGUAGES["English"])
        return lang_dict.get(key, LANGUAGES["English"].get(key, key))

    def center_window(self, width, height):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        self.configure(fg_color="#0B0C10")

        # --- LANG SELECTOR HEADER ---
        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.pack(fill="x", padx=16, pady=(10, 0))

        ctk.CTkLabel(lang_frame, text="🌐 Language:", font=("Segoe UI", 11, "bold"), text_color="#9CA3AF").pack(side="left")
        self.lang_option = ctk.CTkOptionMenu(
            lang_frame, values=list(LANGUAGES.keys()), width=120, height=24,
            font=("Segoe UI", 10), fg_color="#1E202E", button_color="#282A3D", button_hover_color="#374151",
            text_color="#F3F4F6", command=self.change_language
        )
        self.lang_option.pack(side="right")

        # --- STATUS DASHBOARD ---
        status_card = ctk.CTkFrame(
            self, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=14
        )
        status_card.pack(fill="x", padx=16, pady=(10, 8))

        status_box = ctk.CTkFrame(status_card, fg_color="#1E202E", corner_radius=20)
        status_box.pack(pady=(10, 4), padx=12)

        self.status_label = ctk.CTkLabel(
            status_box, text="", font=("Segoe UI", 12, "bold"), text_color="#9CA3AF"
        )
        self.status_label.pack(padx=12, pady=4)

        self.speed_label = ctk.CTkLabel(
            status_card, text="0.00 KB/s", font=("Segoe UI", 32, "bold"), text_color="#F3F4F6"
        )
        self.speed_label.pack(pady=0)

        self.info_label = ctk.CTkLabel(
            status_card, text="", font=("Segoe UI", 10), text_color="#6B7280"
        )
        self.info_label.pack(pady=(2, 10))

        # --- SETTINGS ---
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(padx=16, fill="x", pady=2)

        row1 = ctk.CTkFrame(
            settings_frame, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=10
        )
        row1.pack(fill="x", pady=3, ipady=3, ipadx=8)

        self.lbl_threshold = ctk.CTkLabel(row1, text="", font=("Segoe UI", 12, "bold"), text_color="#E5E7EB")
        self.lbl_threshold.pack(side="left", padx=5)

        self.traffic_dir_option = ctk.CTkOptionMenu(
            row1, values=[], width=145, height=26,
            font=("Segoe UI", 11), fg_color="#0B0C10", button_color="#1E202E", button_hover_color="#282A3D",
            text_color="#F3F4F6", command=lambda _: self.save_config()
        )
        self.traffic_dir_option.pack(side="left", padx=4)

        self.lbl_unit_kbs = ctk.CTkLabel(row1, text="", font=("Segoe UI", 11), text_color="#6B7280")
        self.lbl_unit_kbs.pack(side="right", padx=(2, 5))
        
        self.speed_entry = ctk.CTkEntry(
            row1, width=65, height=28, font=("Segoe UI", 12), fg_color="#0B0C10", border_color=self.CARD_BORDER, text_color="#F3F4F6"
        )
        self.speed_entry.insert(0, DEFAULT_CONFIG["threshold_kb"])
        self.speed_entry.pack(side="right", padx=2)
        self.speed_entry.bind("<KeyRelease>", lambda e: self.save_config())

        row2 = ctk.CTkFrame(
            settings_frame, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=10
        )
        row2.pack(fill="x", pady=3, ipady=3, ipadx=8)

        self.lbl_idle = ctk.CTkLabel(row2, text="", font=("Segoe UI", 12, "bold"), text_color="#E5E7EB")
        self.lbl_idle.pack(side="left", padx=5)
        
        self.lbl_unit_sec = ctk.CTkLabel(row2, text="", font=("Segoe UI", 11), text_color="#6B7280")
        self.lbl_unit_sec.pack(side="right", padx=(2, 5))
        
        self.idle_entry = ctk.CTkEntry(
            row2, width=65, height=28, font=("Segoe UI", 12), fg_color="#0B0C10", border_color=self.CARD_BORDER, text_color="#F3F4F6"
        )
        self.idle_entry.insert(0, DEFAULT_CONFIG["idle_time"])
        self.idle_entry.pack(side="right", padx=2)
        self.idle_entry.bind("<KeyRelease>", lambda e: self.save_config())

        row_action = ctk.CTkFrame(
            settings_frame, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=10
        )
        row_action.pack(fill="x", pady=3, ipady=3, ipadx=8)

        self.lbl_pc_action = ctk.CTkLabel(row_action, text="", font=("Segoe UI", 12, "bold"), text_color="#E5E7EB")
        self.lbl_pc_action.pack(side="left", padx=5)
        
        self.action_option = ctk.CTkOptionMenu(
            row_action, values=[], width=175, height=26,
            font=("Segoe UI", 11), fg_color="#0B0C10", button_color="#1E202E", button_hover_color="#282A3D",
            text_color="#F3F4F6", command=lambda _: self.save_config()
        )
        self.action_option.pack(side="right", padx=2)

        row3 = ctk.CTkFrame(
            settings_frame, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=10
        )
        row3.pack(fill="x", pady=3, ipady=3, ipadx=8)

        self.lbl_safety_timer = ctk.CTkLabel(row3, text="", font=("Segoe UI", 12, "bold"), text_color="#F59E0B")
        self.lbl_safety_timer.pack(side="left", padx=5)
        
        self.timer_entry = ctk.CTkEntry(
            row3, width=80, height=28, font=("Segoe UI", 12),
            fg_color="#0B0C10", border_color=self.CARD_BORDER, text_color="#F3F4F6"
        )
        self.timer_entry.insert(0, DEFAULT_CONFIG["timer_raw"])
        self.timer_entry.pack(side="left", padx=5)

        self.timer_preview_label = ctk.CTkLabel(row3, text="", font=("Segoe UI", 11), text_color="#6B7280")
        self.timer_preview_label.pack(side="right", padx=5)
        self.timer_entry.bind("<KeyRelease>", self.on_timer_input_change)

        self.desc3 = ctk.CTkLabel(
            settings_frame, text="", font=("Segoe UI", 10), text_color="#F59E0B", anchor="w"
        )
        self.desc3.pack(fill="x", padx=6, pady=(1, 3))

        row_sound = ctk.CTkFrame(
            settings_frame, fg_color=self.CARD_BG, border_width=1, border_color=self.CARD_BORDER, corner_radius=10
        )
        row_sound.pack(fill="x", pady=3, ipady=3, ipadx=8)

        self.lbl_sound = ctk.CTkLabel(row_sound, text="", font=("Segoe UI", 12, "bold"), text_color="#E5E7EB")
        self.lbl_sound.pack(side="left", padx=5)
        
        self.sound_switch = ctk.CTkSwitch(
            row_sound, text="", font=("Segoe UI", 11), progress_color=self.ACCENT_COLOR, text_color="#9CA3AF",
            command=self.save_config
        )
        self.sound_switch.select()
        self.sound_switch.pack(side="right", padx=5)

        extra_btns_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        extra_btns_frame.pack(fill="x", pady=(4, 0))

        if TRAY_AVAILABLE:
            self.btn_tray = ctk.CTkButton(
                extra_btns_frame, text="", font=("Segoe UI", 11), height=28,
                fg_color="#1E202E", hover_color="#282A3D", text_color="#9CA3AF",
                border_width=1, border_color="#282A3D", command=self.hide_to_tray
            )
            self.btn_tray.pack(side="left", expand=True, fill="x", padx=(0, 2))

        self.btn_reset = ctk.CTkButton(
            extra_btns_frame, text="", font=("Segoe UI", 11), height=28,
            fg_color="#1E202E", hover_color="#371B1E", text_color="#EF4444",
            border_width=1, border_color="#282A3D", command=self.reset_to_defaults
        )
        self.btn_reset.pack(side="right", expand=True, fill="x", padx=(2, 0))

        # --- INFO LOG & BUTTONS ---
        self.log_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 11), text_color="#06B6D4"
        )
        self.log_label.pack(pady=6)

        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(pady=2, padx=16, fill="x")

        self.btn_start = ctk.CTkButton(
            btn_container, text="", font=("Segoe UI", 13, "bold"), height=40,
            corner_radius=10, fg_color=self.ACCENT_COLOR, hover_color=self.ACCENT_HOVER, command=self.toggle_monitoring
        )
        self.btn_start.pack(expand=True, fill="x")

        self.btn_cancel_shutdown = ctk.CTkButton(
            self, text="", font=("Segoe UI", 12, "bold"), height=40,
            corner_radius=10, fg_color="#DC2626", hover_color="#B91C1C", command=self.abort_system_shutdown
        )

        # --- FOOTER ---
        links_frame = ctk.CTkFrame(self, fg_color="transparent")
        links_frame.pack(side="bottom", pady=12)

        self.lbl_support = ctk.CTkLabel(links_frame, text="", font=("Segoe UI", 10), text_color="#4B5563")
        self.lbl_support.pack(pady=(0, 4))

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

        self.retranslate_ui()

    def retranslate_ui(self):
        self.title(self.tr("title"))
        self.lang_option.set(self.current_lang)

        if not self.is_monitoring:
            self.status_label.configure(text=self.tr("awaiting_start"))
            self.btn_start.configure(text=self.tr("start_btn"))
            self.log_label.configure(text=self.tr("net_ready"))

        self.info_label.configure(text=self.tr("current_speed"))
        self.lbl_threshold.configure(text=self.tr("threshold"))
        self.lbl_unit_kbs.configure(text=self.tr("kb_s"))
        self.lbl_idle.configure(text=self.tr("idle_time"))
        self.lbl_unit_sec.configure(text=self.tr("sec"))
        self.lbl_pc_action.configure(text=self.tr("pc_action"))
        self.lbl_safety_timer.configure(text=self.tr("safety_timer"))
        self.timer_entry.configure(placeholder_text=self.tr("timer_off_hint"))
        self.desc3.configure(text=self.tr("safety_desc"))
        self.lbl_sound.configure(text=self.tr("sound_notif"))
        self.sound_switch.configure(text=self.tr("on"))

        if TRAY_AVAILABLE:
            self.btn_tray.configure(text=self.tr("to_tray"))
        self.btn_reset.configure(text=self.tr("reset_settings"))
        self.btn_cancel_shutdown.configure(text=self.tr("cancel_btn"))
        self.lbl_support.configure(text=self.tr("project_support"))

        curr_dir_idx = self.get_current_dir_index()
        self.traffic_dir_option.configure(values=self.tr("traffic_dirs"))
        self.traffic_dir_option.set(self.tr("traffic_dirs")[curr_dir_idx])

        curr_act_idx = self.get_current_action_index()
        self.action_option.configure(values=self.tr("actions"))
        self.action_option.set(self.tr("actions")[curr_act_idx])

        self.on_timer_input_change(None)

    def change_language(self, new_lang):
        if new_lang in LANGUAGES:
            self.current_lang = new_lang
            self.retranslate_ui()
            self.save_config()

    def get_current_dir_index(self):
        current_val = self.traffic_dir_option.get()
        for lang, d in LANGUAGES.items():
            if current_val in d["traffic_dirs"]:
                return d["traffic_dirs"].index(current_val)
        return 0

    def get_current_action_index(self):
        current_val = self.action_option.get()
        for lang, d in LANGUAGES.items():
            if current_val in d["actions"]:
                return d["actions"].index(current_val)
        return 0

    def apply_config_dict(self, cfg):
        self.speed_entry.delete(0, "end")
        self.speed_entry.insert(0, str(cfg.get("threshold_kb", DEFAULT_CONFIG["threshold_kb"])))

        self.idle_entry.delete(0, "end")
        self.idle_entry.insert(0, str(cfg.get("idle_time", DEFAULT_CONFIG["idle_time"])))

        self.timer_entry.delete(0, "end")
        self.timer_entry.insert(0, str(cfg.get("timer_raw", DEFAULT_CONFIG["timer_raw"])))

        self.current_lang = cfg.get("language", DEFAULT_CONFIG["language"])
        if self.current_lang not in LANGUAGES:
            self.current_lang = "English"

        dir_idx = cfg.get("traffic_dir_index", 0)
        act_idx = cfg.get("action_index", 0)

        dirs = LANGUAGES[self.current_lang]["traffic_dirs"]
        actions = LANGUAGES[self.current_lang]["actions"]

        self.traffic_dir_option.set(dirs[dir_idx if 0 <= dir_idx < len(dirs) else 0])
        self.action_option.set(actions[act_idx if 0 <= act_idx < len(actions) else 0])

        if cfg.get("sound_enabled", DEFAULT_CONFIG["sound_enabled"]):
            self.sound_switch.select()
        else:
            self.sound_switch.deselect()

        self.retranslate_ui()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.apply_config_dict(cfg)
                    return
            except Exception:
                pass
        self.apply_config_dict(DEFAULT_CONFIG)

    def save_config(self):
        try:
            cfg = {
                "threshold_kb": self.speed_entry.get(),
                "idle_time": self.idle_entry.get(),
                "timer_raw": self.timer_entry.get(),
                "traffic_dir_index": self.get_current_dir_index(),
                "action_index": self.get_current_action_index(),
                "sound_enabled": bool(self.sound_switch.get()),
                "language": self.current_lang
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def reset_to_defaults(self):
        self.apply_config_dict(DEFAULT_CONFIG)
        self.save_config()
        self.log_label.configure(text=self.tr("settings_reset"), text_color="#10B981")

    def on_closing(self):
        self.save_config()
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()

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
            pystray.MenuItem(self.tr("tray_restore"), self.restore_from_tray, default=True),
            pystray.MenuItem(self.tr("tray_exit"), self.exit_from_tray)
        )
        self.tray_icon = pystray.Icon("SmartShutdown", icon_img, self.tr("title"), menu)
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

    def parse_time_string(self, text):
        text = text.lower().strip()
        if not text or text == "0" or text in ["off", "откл", "desact", "aus", "désact", "关闭", "desat", "オフ"]:
            return 0
        if text.isdigit():
            return int(text)

        digits = re.search(r'([0-9.]+)', text)
        if digits:
            try:
                return int(float(digits.group(1)))
            except ValueError:
                pass

        return 0

    def on_timer_input_change(self, event):
        raw_text = self.timer_entry.get()
        parsed_min = self.parse_time_string(raw_text)

        if parsed_min > 0:
            self.chosen_max_time_minutes = parsed_min
            txt = self.tr("in_minutes_fmt").format(min=parsed_min)
            self.timer_preview_label.configure(text=txt, text_color="#10B981")
        else:
            self.chosen_max_time_minutes = 0
            self.timer_preview_label.configure(text=self.tr("disabled"), text_color="#6B7280")
            
        self.save_config()

    def toggle_monitoring(self):
        if not self.is_monitoring:
            self.save_config()
            self.is_monitoring = True
            self.btn_start.configure(text=self.tr("stop_btn"), fg_color="#374151", hover_color="#4B5563")
            self.status_label.configure(text=self.tr("monitoring_active"), text_color="#10B981")

            self.timer_entry.configure(state="disabled")
            self.traffic_dir_option.configure(state="disabled")
            self.action_option.configure(state="disabled")
            self.sound_switch.configure(state="disabled")
            self.lang_option.configure(state="disabled")

            try:
                self.threshold_bytes = float(self.speed_entry.get()) * 1024
                self.idle_limit = int(self.idle_entry.get())
                self.max_time_seconds = self.chosen_max_time_minutes * 60
            except ValueError:
                self.log_label.configure(text=self.tr("param_error"), text_color="#EF4444")
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
            self.lang_option.configure(state="normal")
            self.btn_start.configure(text=self.tr("start_btn"), fg_color=self.ACCENT_COLOR, hover_color=self.ACCENT_HOVER)
            self.status_label.configure(text=self.tr("stopped"), text_color="#9CA3AF")
            self.speed_label.configure(text="0.00 KB/s")
            self.log_label.configure(text=self.tr("monitoring_stopped_log"), text_color="#F59E0B")

    def update_speed_ui(self, speed_text, log_text, is_idle, timer_text=None):
        if not self.is_monitoring:
            return
        self.speed_label.configure(text=speed_text)
        self.log_label.configure(
            text=log_text,
            text_color="#F59E0B" if is_idle else "#06B6D4"
        )
        if timer_text and self.max_time_seconds > 0:
            self.timer_preview_label.configure(text=timer_text)

    def network_monitor_loop(self):
        start_time = time.time()
        idle_counter = 0
        check_upload = (self.get_current_dir_index() == 0)

        while self.is_monitoring:
            net_start = psutil.net_io_counters()
            bytes_start = net_start.bytes_sent if check_upload else net_start.bytes_recv
            time.sleep(1)

            if not self.is_monitoring:
                break

            net_end = psutil.net_io_counters()
            bytes_end = net_end.bytes_sent if check_upload else net_end.bytes_recv

            current_speed_bytes = bytes_end - bytes_start
            current_speed_kb = current_speed_bytes / 1024

            if current_speed_kb > 1024:
                speed_str = f"{current_speed_kb/1024:.2f} MB/s"
            else:
                speed_str = f"{current_speed_kb:.2f} KB/s"

            elapsed_time = time.time() - start_time
            remaining_time_min = 0
            timer_str = None

            if self.max_time_seconds > 0:
                remaining_time_min = max(0, int((self.max_time_seconds - elapsed_time) / 60))
                timer_str = self.tr("in_minutes_fmt").format(min=remaining_time_min)

                if elapsed_time >= self.max_time_seconds:
                    self.after(0, lambda: self.trigger_shutdown(self.tr("safety_triggered")))
                    break

            if current_speed_bytes < self.threshold_bytes:
                idle_counter += 1
            else:
                idle_counter = 0

            time_info = self.tr("safety_info_fmt").format(min=remaining_time_min) if self.max_time_seconds > 0 else self.tr("safety_off_info")
            log_str = self.tr("traffic_drop_fmt").format(idle=idle_counter, limit=self.idle_limit) + time_info

            self.after(0, self.update_speed_ui, speed_str, log_str, idle_counter > 0, timer_str)

            if idle_counter >= self.idle_limit:
                self.after(0, lambda: self.trigger_shutdown(self.tr("traffic_drop_detected")))
                break

    def trigger_shutdown(self, reason):
        self.is_monitoring = False
        action_idx = self.get_current_action_index()
        action_name = self.tr("actions")[action_idx]

        if self.tray_icon:
            self.restore_from_tray()

        if bool(self.sound_switch.get()):
            sound_path = get_resource_path("alert.wav")
            if sys.platform == "win32" and os.path.exists(sound_path):
                try:
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                except Exception:
                    pass
            elif sys.platform == "win32":
                try:
                    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
                except Exception:
                    pass

        self.status_label.configure(text=f"{self.tr('executing')} {action_name.upper()}", text_color="#EF4444")
        self.log_label.configure(text=f"{reason}\n{self.tr('action_in_60')}", text_color="#EF4444")
        self.btn_start.pack_forget()
        self.btn_cancel_shutdown.pack(pady=8, padx=16, fill="x")

        if sys.platform == "win32":
            if action_idx == 0:
                os.system("shutdown /s /t 60")
            elif action_idx == 2:
                os.system("shutdown /r /t 60")
            elif action_idx == 1:
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    def abort_system_shutdown(self):
        if sys.platform == "win32":
            os.system("shutdown /a")

        self.is_monitoring = False
        self.max_time_seconds = 0

        self.timer_entry.configure(state="normal")
        self.traffic_dir_option.configure(state="normal")
        self.action_option.configure(state="normal")
        self.sound_switch.configure(state="normal")
        self.lang_option.configure(state="normal")

        if self.chosen_max_time_minutes > 0:
            txt = self.tr("in_minutes_fmt").format(min=self.chosen_max_time_minutes)
            self.timer_preview_label.configure(text=txt, text_color="#10B981")
        else:
            self.timer_preview_label.configure(text=self.tr("disabled"), text_color="#6B7280")

        self.btn_cancel_shutdown.pack_forget()
        self.btn_start.pack(pady=4, padx=16, fill="x")
        self.btn_start.configure(text=self.tr("start_btn"), fg_color=self.ACCENT_COLOR, hover_color=self.ACCENT_HOVER)
        
        self.status_label.configure(text=self.tr("awaiting_start"), text_color="#9CA3AF")
        self.speed_label.configure(text="0.00 KB/s")
        self.log_label.configure(text=self.tr("action_canceled_log"), text_color="#10B981")

if __name__ == "__main__":
    app = AutoShutdownApp()
    app.mainloop()