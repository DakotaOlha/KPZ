import customtkinter as ctk
from tkinter import messagebox
import sys
import os

from database import DatabaseManager
from auth import AuthManager, UserManager, RoleManager
from login_window import LoginWindow
from admin_panel import AdminPanel
from ui.main_app import MainApp

class LearnEasyWithAdmin(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.db = DatabaseManager()
        if not self.db.connect():
            messagebox.showerror("Помилка", "Не вдалося підключитися до бази даних")
            self.destroy()
            sys.exit(1)

        self.auth = AuthManager(self.db.conn)
        self.user_manager = UserManager(self.db.conn, self.auth)
        self.role_manager = RoleManager(self.db.conn, self.auth)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Learn Easy - Система управління навчанням")
        self.geometry("1400x900")

        self.withdraw()

        self.show_login()

    def show_login(self):
        login_window = LoginWindow(self.auth, self.on_login_success)
        login_window.run()

    def on_login_success(self, user_data: dict):
        self.deiconify()

        self.center_window()

        self.create_interface(user_data)

        self.after(100, lambda: self.state('zoomed'))

        self.show_welcome_message(user_data)

    def center_window(self):
        self.update_idletasks()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width - 1400) // 2
        y = (screen_height - 900) // 2

        self.geometry(f"1400x900+{x}+{y}")

    def create_interface(self, user_data: dict):
        for widget in self.winfo_children():
            widget.destroy()

        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#1E293B")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        user_frame = ctk.CTkFrame(self.sidebar, fg_color="#334155", corner_radius=10)
        user_frame.pack(pady=20, padx=15, fill="x")

        ctk.CTkLabel(
            user_frame,
            text="👤",
            font=ctk.CTkFont(size=32)
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            user_frame,
            text=user_data['username'],
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)

        role_label = ctk.CTkLabel(
            user_frame,
            text=user_data['role_name'],
            font=ctk.CTkFont(size=12),
            fg_color="#3B82F6",
            corner_radius=5
        )
        role_label.pack(pady=(5, 15), padx=20)

        self.menu_buttons = []

        if self.auth.has_permission('words.view'):
            self.add_menu_button("📊 Дашборд", self.show_dashboard, "#3B82F6")

        if self.auth.has_permission('words.view'):
            self.add_menu_button("🃏 Картки", self.show_flashcards, "#8B5CF6")

        if self.auth.has_permission('words.view'):
            self.add_menu_button("📖 Мої слова", self.show_words, "#10B981")

        if self.auth.has_permission('statistics.view'):
            self.add_menu_button("📈 Статистика", self.show_statistics, "#F59E0B")
        if self.auth.has_permission('users.view'):
            ctk.CTkLabel(
                self.sidebar,
                text="АДМІНІСТРУВАННЯ",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#64748B"
            ).pack(pady=(20, 10), padx=15, anchor="w")

            self.add_menu_button("👥 Користувачі", self.show_admin_panel, "#EC4899")

        if self.auth.has_permission('system.logs'):
            self.add_menu_button("📋 Журнал подій", self.show_audit_log, "#6366F1")

        if self.auth.has_permission('system.settings'):
            self.add_menu_button("⚙️ Налаштування", self.show_settings, "#64748B")

        logout_btn = ctk.CTkButton(
            self.sidebar,
            text="🚪 Вийти",
            command=self.logout,
            height=50,
            fg_color="#EF4444",
            hover_color="#DC2626"
        )
        logout_btn.pack(side="bottom", pady=20, padx=15, fill="x")

        self.main_container = ctk.CTkFrame(self, fg_color="#0F172A")
        self.main_container.pack(side="right", fill="both", expand=True)

        self.show_dashboard()

    def add_menu_button(self, text: str, command, color: str):
        btn = ctk.CTkButton(
            self.sidebar,
            text=text,
            command=command,
            height=50,
            font=ctk.CTkFont(size=15),
            fg_color="transparent",
            hover_color="#334155",
            anchor="w",
            corner_radius=10
        )
        btn.pack(pady=5, padx=15, fill="x")
        self.menu_buttons.append(btn)

    def highlight_menu_button(self, index: int):
        for i, btn in enumerate(self.menu_buttons):
            if i == index:
                btn.configure(fg_color="#334155")
            else:
                btn.configure(fg_color="transparent")

    def clear_main_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_container()
        self.highlight_menu_button(0)

        title = ctk.CTkLabel(
            self.main_container,
            text="📊 Дашборд",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        title.pack(pady=50)

        stats = self.db.get_statistics()

        stats_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        stats_frame.pack(pady=30)

        cards = [
            ("Всього слів", stats['total_words'], "#3B82F6"),
            ("Вивчено", stats['learned_words'], "#10B981"),
            ("Вивчається", stats['learning_words'], "#F59E0B"),
            ("Нові", stats['new_words'], "#8B5CF6"),
        ]

        for i, (title_text, value, color) in enumerate(cards):
            card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=15, width=200, height=150)
            card.grid(row=0, column=i, padx=15, pady=15)

            ctk.CTkLabel(
                card,
                text=str(value),
                font=ctk.CTkFont(size=48, weight="bold"),
                text_color="white"
            ).pack(pady=(30, 5))

            ctk.CTkLabel(
                card,
                text=title_text,
                font=ctk.CTkFont(size=16),
                text_color="white"
            ).pack(pady=(5, 30))

    def show_flashcards(self):
        self.clear_main_container()
        self.highlight_menu_button(1)

        from windows.flashcard_window import FlashcardWindow
        FlashcardWindow(self, self.db)

    def show_words(self):
        self.clear_main_container()
        self.highlight_menu_button(2)

        ctk.CTkLabel(
            self.main_container,
            text="📖 Мої слова",
            font=ctk.CTkFont(size=36, weight="bold")
        ).pack(pady=50)

    def show_statistics(self):
        self.clear_main_container()
        self.highlight_menu_button(3)

        from windows.statistics_window import StatisticsWindow
        stats_window = StatisticsWindow(self.main_container, self.db)

    def show_admin_panel(self):
        self.clear_main_container()

        for i, btn in enumerate(self.menu_buttons):
            if "Користувачі" in btn.cget("text"):
                self.highlight_menu_button(i)
                break

        admin_panel = AdminPanel(
            self.main_container,
            self.auth,
            self.user_manager,
            self.role_manager
        )
        admin_panel.pack(fill="both", expand=True)

    def show_audit_log(self):
        self.clear_main_container()

        ctk.CTkLabel(
            self.main_container,
            text="📋 Журнал подій",
            font=ctk.CTkFont(size=36, weight="bold")
        ).pack(pady=50)

        ctk.CTkLabel(
            self.main_container,
            text="Журнал аудиту буде додано в наступній версії",
            font=ctk.CTkFont(size=14),
            text_color="#94A3B8"
        ).pack(pady=20)

    def show_settings(self):
        self.clear_main_container()

        ctk.CTkLabel(
            self.main_container,
            text="⚙️ Налаштування системи",
            font=ctk.CTkFont(size=36, weight="bold")
        ).pack(pady=50)

    def show_welcome_message(self, user_data: dict):
        permissions = self.auth.get_user_permissions()

        welcome_text = f"""
Вітаємо, {user_data['username']}!

Роль: {user_data['role_name']}
Дозволів: {len(permissions)}

Ви успішно увійшли в систему.
"""

        messagebox.showinfo("Вхід виконано", welcome_text)

    def logout(self):
        if messagebox.askyesno("Вихід", "Ви впевнені що хочете вийти?"):
            self.auth.log_action('LOGOUT', 'System', None, None, None)

            self.auth.logout()

            self.withdraw()

            for widget in self.winfo_children():
                widget.destroy()

            self.show_login()

    def on_closing(self):
        if messagebox.askyesno("Вихід", "Закрити додаток?"):
            if self.auth.is_authenticated():
                self.auth.log_action('LOGOUT', 'System', None, None, 'Application closed')
                self.auth.logout()

            self.db.close()

            self.destroy()
            sys.exit(0)


def main():
    app = LearnEasyWithAdmin()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()