import customtkinter as ctk
from tkinter import messagebox
import sys

from database import DatabaseManager
from auth import AuthManager, UserManager, RoleManager
from login_window import LoginWindow
from admin_panel import AdminPanel


class LearnEasyWithAdmin(ctk.CTk):  

    def __init__(self):
        super().__init__()

        # Підключення до бази даних
        self.db = DatabaseManager()
        if not self.db.connect():
            messagebox.showerror("Помилка", "Не вдалося підключитися до бази даних")
            self.destroy()
            sys.exit(1)

        # Ініціалізація менеджерів
        self.auth = AuthManager(self.db.conn)
        self.user_manager = UserManager(self.db.conn, self.auth)
        self.role_manager = RoleManager(self.db.conn, self.auth)

        # Налаштування теми
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Learn Easy - Система управління навчанням")
        self.geometry("1400x900")

        # Ховаємо головне вікно до входу
        self.withdraw()

        # Показуємо вікно входу
        self.show_login()

    def show_login(self):
        """Показати вікно входу/реєстрації"""
        login_window = LoginWindow(
            self.auth,
            self.on_login_success
        )
        login_window.run()

    def on_login_success(self, user_data: dict):
        """Обробка успішного входу"""
        self.deiconify()
        self.center_window()
        self.create_interface(user_data)

        # Розгортаємо вікно на весь екран
        self.after(100, lambda: self.state('zoomed'))

        # Показуємо вітальне повідомлення
        self.show_welcome_message(user_data)

    def center_window(self):
        """Центрування вікна"""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 1400) // 2
        y = (screen_height - 900) // 2
        self.geometry(f"1400x900+{x}+{y}")

    def create_interface(self, user_data: dict):
        """Створення головного інтерфейсу"""
        # Очищаємо вікно
        for widget in self.winfo_children():
            widget.destroy()

        # Бічна панель (Sidebar)
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#1E293B")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Інформація про користувача
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="#334155", corner_radius=10)
        user_frame.pack(pady=20, padx=15, fill="x")

        ctk.CTkLabel(
            user_frame,
            text="👤",
            font=ctk.CTkFont(size=32)
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            user_frame,
            text=user_data.get('username', 'User'),
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)

        role_label = ctk.CTkLabel(
            user_frame,
            text=user_data.get('role_name', 'No Role'),
            font=ctk.CTkFont(size=12),
            fg_color="#3B82F6",
            corner_radius=5
        )
        role_label.pack(pady=(5, 15), padx=20)

        # Меню
        self.menu_buttons = []
        self.create_menu()

        # Кнопка виходу
        logout_btn = ctk.CTkButton(
            self.sidebar,
            text="🚪 Вийти",
            command=self.logout,
            height=50,
            fg_color="#EF4444",
            hover_color="#DC2626"
        )
        logout_btn.pack(side="bottom", pady=20, padx=15, fill="x")

        # Головний контейнер
        self.main_container = ctk.CTkFrame(self, fg_color="#0F172A")
        self.main_container.pack(side="right", fill="both", expand=True)

        # Показуємо дашборд за замовчуванням
        self.show_dashboard()

    def create_menu(self):
        """Створення меню залежно від прав користувача"""
        menu_index = 0

        # Основні розділи
        if self.auth.has_permission('words.view'):
            self.add_menu_button("📊 Дашборд", self.show_dashboard, "#3B82F6")
            menu_index += 1

        if self.auth.has_permission('words.view'):
            self.add_menu_button("🃏 Картки", self.show_flashcards, "#8B5CF6")
            menu_index += 1

        if self.auth.has_permission('words.view'):
            self.add_menu_button("📖 Мої слова", self.show_words, "#10B981")
            menu_index += 1

        if self.auth.has_permission('statistics.view'):
            self.add_menu_button("📈 Статистика", self.show_statistics, "#F59E0B")
            menu_index += 1

        # Розділ адміністрування
        has_admin_permissions = (
                self.auth.has_permission('users.view') or
                self.auth.has_permission('system.logs') or
                self.auth.has_permission('system.settings')
        )

        if has_admin_permissions:
            ctk.CTkLabel(
                self.sidebar,
                text="АДМІНІСТРУВАННЯ",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#64748B"
            ).pack(pady=(20, 10), padx=15, anchor="w")

        if self.auth.has_permission('users.view'):
            self.add_menu_button("👥 Користувачі", self.show_admin_panel, "#EC4899")
            menu_index += 1

        if self.auth.has_permission('system.logs'):
            self.add_menu_button("📋 Журнал подій", self.show_audit_log, "#6366F1")
            menu_index += 1

        if self.auth.has_permission('system.settings'):
            self.add_menu_button("⚙️ Налаштування", self.show_settings, "#64748B")
            menu_index += 1

    def add_menu_button(self, text: str, command, color: str):
        """Додавання кнопки меню"""
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
        """Підсвічування активної кнопки меню"""
        for i, btn in enumerate(self.menu_buttons):
            if i == index:
                btn.configure(fg_color="#334155")
            else:
                btn.configure(fg_color="transparent")

    def clear_main_container(self):
        """Очищення головного контейнера"""
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        """Показати дашборд"""
        self.clear_main_container()
        self.highlight_menu_button(0)

        title = ctk.CTkLabel(
            self.main_container,
            text="📊 Дашборд",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        title.pack(pady=50)

        try:
            stats = self.db.get_statistics()

            stats_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
            stats_frame.pack(pady=30)

            cards = [
                ("Всього слів", stats.get('total_words', 0), "#3B82F6"),
                ("Вивчено", stats.get('learned_words', 0), "#10B981"),
                ("Вивчається", stats.get('learning_words', 0), "#F59E0B"),
                ("Нові", stats.get('new_words', 0), "#8B5CF6"),
            ]

            for i, (title_text, value, color) in enumerate(cards):
                card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=15,
                                    width=200, height=150)
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

            # Прогрес
            progress_frame = ctk.CTkFrame(self.main_container, fg_color="#1E293B",
                                          corner_radius=15)
            progress_frame.pack(pady=30, padx=50, fill="x")

            progress_percentage = stats.get('progress_percentage', 0)

            ctk.CTkLabel(
                progress_frame,
                text=f"Загальний прогрес: {progress_percentage:.1f}%",
                font=ctk.CTkFont(size=20, weight="bold")
            ).pack(pady=(20, 10))

            progress_bar = ctk.CTkProgressBar(progress_frame, width=600, height=30)
            progress_bar.pack(pady=(10, 20))
            progress_bar.set(progress_percentage / 100)

        except Exception as e:
            ctk.CTkLabel(
                self.main_container,
                text=f"Помилка завантаження даних: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color="#EF4444"
            ).pack(pady=20)

    def show_flashcards(self):
        """Показати режим флеш-карток"""
        self.clear_main_container()
        self.highlight_menu_button(1)

        try:
            from windows.flashcard_window import FlashcardWindow
            FlashcardWindow(self.main_container, self.db)
        except ImportError:
            ctk.CTkLabel(
                self.main_container,
                text="🃏 Режим флеш-карток\n\nМодуль в розробці",
                font=ctk.CTkFont(size=24),
                text_color="#94A3B8"
            ).pack(pady=100)

    def show_words(self):
        """Показати список слів"""
        self.clear_main_container()
        self.highlight_menu_button(2)

        ctk.CTkLabel(
            self.main_container,
            text="📖 Мої слова",
            font=ctk.CTkFont(size=36, weight="bold")
        ).pack(pady=50)

        ctk.CTkLabel(
            self.main_container,
            text="Список слів буде тут",
            font=ctk.CTkFont(size=16),
            text_color="#94A3B8"
        ).pack(pady=20)

    def show_statistics(self):
        """Показати статистику"""
        self.clear_main_container()
        self.highlight_menu_button(3)

        try:
            from windows.statistics_window import StatisticsWindow
            StatisticsWindow(self.main_container, self.db)
        except ImportError:
            ctk.CTkLabel(
                self.main_container,
                text="📈 Статистика\n\nМодуль в розробці",
                font=ctk.CTkFont(size=24),
                text_color="#94A3B8"
            ).pack(pady=100)

    def show_admin_panel(self):
        """Показати панель адміністратора"""
        self.clear_main_container()

        # Знаходимо індекс кнопки "Користувачі"
        for i, btn in enumerate(self.menu_buttons):
            if "Користувачі" in btn.cget("text"):
                self.highlight_menu_button(i)
                break

        # Показуємо панель адміністрування
        admin_panel = AdminPanel(
            self.main_container,
            self.auth,
            self.user_manager,
            self.role_manager
        )
        admin_panel.pack(fill="both", expand=True)

    def show_audit_log(self):
        """Показати журнал подій"""
        self.clear_main_container()

        for i, btn in enumerate(self.menu_buttons):
            if "Журнал" in btn.cget("text"):
                self.highlight_menu_button(i)
                break

        ctk.CTkLabel(
            self.main_container,
            text="📋 Журнал подій",
            font=ctk.CTkFont(size=36, weight="bold")
        ).pack(pady=50)

        # Тут можна додати відображення логів
        try:
            query = """
                    SELECT TOP 50
                    action_time, username, \
                           action_type,
                           table_name, \
                           new_value
                    FROM AuditLog
                    ORDER BY action_time DESC \
                    """
            self.db.cursor.execute(query)
            logs = self.db.cursor.fetchall()

            if logs:
                logs_frame = ctk.CTkScrollableFrame(
                    self.main_container,
                    fg_color="#1E293B"
                )
                logs_frame.pack(fill="both", expand=True, padx=50, pady=20)

                for log in logs:
                    log_text = f"{log[0]} | {log[1]} | {log[2]} | {log[3]}"
                    ctk.CTkLabel(
                        logs_frame,
                        text=log_text,
                        font=ctk.CTkFont(size=12),
                        anchor="w"
                    ).pack(fill="x", pady=2, padx=10)
            else:
                ctk.CTkLabel(
                    self.main_container,
                    text="Немає записів",
                    text_color="#94A3B8"
                ).pack(pady=20)

        except Exception as e:
            ctk.CTkLabel(
                self.main_container,
                text=f"Помилка: {str(e)}",
                text_color="#EF4444"
            ).pack(pady=20)

    def show_settings(self):
        """Показати налаштування"""
        self.clear_main_container()

        for i, btn in enumerate(self.menu_buttons):
            if "Налаштування" in btn.cget("text"):
                self.highlight_menu_button(i)
                break

        ctk.CTkLabel(
            self.main_container,
            text="⚙️ Налаштування системи",
            font=ctk.CTkFont(size=36, weight="bold")
        ).pack(pady=50)

        ctk.CTkLabel(
            self.main_container,
            text="Розділ в розробці",
            font=ctk.CTkFont(size=16),
            text_color="#94A3B8"
        ).pack(pady=20)

    def show_welcome_message(self, user_data: dict):
        """Показати вітальне повідомлення"""
        permissions = self.auth.get_user_permissions()

        welcome_text = f"""Вітаємо, {user_data.get('username', 'User')}!

Роль: {user_data.get('role_name', 'Невідома')}
Доступних дозволів: {len(permissions)}

Ви успішно увійшли в систему LearnEasy.
"""

        messagebox.showinfo("Вхід виконано", welcome_text)

    def logout(self):
        """Вихід з системи"""
        if messagebox.askyesno("Вихід", "Ви впевнені що хочете вийти?"):
            # Логуємо вихід
            self.auth.log_action('LOGOUT', 'System', None, None, None)

            # Виконуємо вихід
            self.auth.logout()

            # Ховаємо головне вікно
            self.withdraw()

            # Очищаємо інтерфейс
            for widget in self.winfo_children():
                widget.destroy()

            # Показуємо вікно входу
            self.show_login()

    def on_closing(self):
        """Обробка закриття програми"""
        if messagebox.askyesno("Вихід", "Закрити додаток?"):
            if self.auth.is_authenticated():
                self.auth.log_action('LOGOUT', 'System', None, None, 'Application closed')
                self.auth.logout()

            self.db.close()
            self.destroy()
            sys.exit(0)


def main():
    """Головна функція запуску програми"""
    app = LearnEasyWithAdmin()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()