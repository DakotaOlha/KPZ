import customtkinter as ctk
from tkinter import messagebox
import sys

from database import DatabaseManager
from auth import AuthManager, UserManager, RoleManager
from login_window import LoginWindow
from admin_panel import AdminPanel
from DataExporter import DataExporter

from windows.flashcard_window import FlashcardWindow
from windows.edit_word_window import EditWordWindow
from windows.popup_window import PopupWindow
from windows.statistics_window import StatisticsWindow

from datetime import datetime, timedelta
import threading
import time


class LearnEasyWithAuth(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.db = DatabaseManager()

        if not self.db.connect(use_trusted=True):
            messagebox.showerror("Помилка", "Не вдалося підключитися до бази даних")
            self.destroy()
            sys.exit(1)

        self.auth = AuthManager(self.db.conn)
        self.user_manager = UserManager(self.db.conn, self.auth)
        self.role_manager = RoleManager(self.db.conn, self.auth)

        self.withdraw()

        self.show_login()

    def show_login(self):
        login_window = LoginWindow(
            self.auth,
            self.on_login_success,
            self.db
        )
        login_window.run()

    def on_login_success(self, user_data: dict):
        print(f"Успішний вхід: {user_data['username']}, роль: {user_data['role_name']}")

        self.deiconify()
        self.create_interface(user_data)
        self.update()
        self.center_window()
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

        self.menu_buttons = []
        self.create_menu()

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

    def create_menu(self):
        menu_items = []

        if self.auth.has_permission('words.view'):
            menu_items.append(("📊 Дашборд", self.show_dashboard, "#3B82F6"))

            if not self.auth.has_permission('users.view'):
                menu_items.append(("🃏 Картки", self.show_flashcards, "#8B5CF6"))
                menu_items.append(("📖 Мої слова", self.show_words, "#10B981"))
                menu_items.append(("⚙️ Налаштування", self.show_settings, "#64748B"))


        if self.auth.has_permission('statistics.view'):
            menu_items.append(("📈 Статистика", self.show_statistics, "#F59E0B"))

        if self.auth.has_permission('words.create'):
            if not self.auth.has_permission('users.view'):
                menu_items.append(("➕ Додати слово", self.show_add_word, "#EC4899"))

        #if self.auth.has_permission('words.view'):
            # menu_items.append(("⚙️ Налаштування", self.show_settings, "#64748B"))

        has_admin_permissions = (
                self.auth.has_permission('users.view') or
                self.auth.has_permission('system.logs') or
                self.auth.has_permission('system.settings')
        )

        if has_admin_permissions:
            separator = ctk.CTkFrame(self.sidebar, height=2, fg_color="#475569")
            separator.pack(pady=15, padx=15, fill="x")

            ctk.CTkLabel(
                self.sidebar,
                text="АДМІНІСТРУВАННЯ",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#64748B"
            ).pack(pady=(5, 10), padx=15, anchor="w")

        if self.auth.has_permission('users.view'):
            menu_items.append(("👥 Користувачі", self.show_admin_panel, "#EC4899"))

        if self.auth.has_permission('system.logs'):
            menu_items.append(("📋 Журнал подій", self.show_audit_log, "#6366F1"))

        for text, command, color in menu_items:
            self.add_menu_button(text, command, color)

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

        scroll_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=30, pady=20)

        # Заголовок
        header_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 30))

        title = ctk.CTkLabel(
            header_frame,
            text="Дашборд",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        title.pack(side="left")

        date_label = ctk.CTkLabel(
            header_frame,
            text=datetime.now().strftime("%d %B %Y"),
            font=ctk.CTkFont(size=16),
            text_color="#64748B"
        )
        date_label.pack(side="right")

        # Статистика
        stats = self.db.get_statistics()

        cards_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        cards_frame.pack(fill="x", pady=20)

        cards_data = [
            ("Всього слів", stats['total_words'], "#3B82F6", "📚"),
            ("Вивчено", stats['learned_words'], "#10B981", "✅"),
            ("Вивчається", stats['learning_words'], "#F59E0B", "📖"),
            ("Нові", stats['new_words'], "#8B5CF6", "✨"),
        ]

        for i, (title_text, value, color, icon) in enumerate(cards_data):
            card = self.create_stat_card(cards_frame, title_text, value, color, icon)
            card.grid(row=i // 2, column=i % 2, padx=15, pady=15, sticky="nsew")

        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)

        # Прогрес
        progress_frame = ctk.CTkFrame(scroll_frame, fg_color="#1E293B", corner_radius=15)
        progress_frame.pack(fill="x", pady=30, padx=10)

        ctk.CTkLabel(
            progress_frame,
            text="Загальний прогрес навчання",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(30, 15))

        progress = stats['progress_percentage'] / 100
        progress_bar = ctk.CTkProgressBar(progress_frame, width=500, height=25, corner_radius=12)
        progress_bar.pack(pady=15)
        progress_bar.set(progress)

        ctk.CTkLabel(
            progress_frame,
            text=f"{stats['progress_percentage']:.1f}% слів вивчено",
            font=ctk.CTkFont(size=18),
            text_color="#64748B"
        ).pack(pady=(5, 30))

        # Швидкі дії
        actions_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        actions_frame.pack(fill="x", pady=20)

        ctk.CTkLabel(
            actions_frame,
            text="Швидкі дії",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w", pady=(0, 15))

        actions_buttons = ctk.CTkFrame(actions_frame, fg_color="transparent")
        actions_buttons.pack(fill="x")

        ctk.CTkButton(
            actions_buttons,
            text="🃏 Почати навчання",
            command=self.show_flashcards,
            height=60,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#8B5CF6",
            hover_color="#7C3AED"
        ).pack(side="left", padx=10, fill="x", expand=True)

        if self.auth.has_permission('words.create'):
            ctk.CTkButton(
                actions_buttons,
                text="➕ Додати слова",
                command=self.show_add_word,
                height=60,
                font=ctk.CTkFont(size=18, weight="bold"),
                fg_color="#F59E0B",
                hover_color="#D97706"
            ).pack(side="left", padx=10, fill="x", expand=True)

    def create_stat_card(self, parent, title, value, color, icon):
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=15, height=150)

        ctk.CTkLabel(
            card,
            text=icon,
            font=ctk.CTkFont(size=40)
        ).pack(pady=(25, 5))

        ctk.CTkLabel(
            card,
            text=str(value),
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color="white"
        ).pack(pady=5)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=16),
            text_color="white"
        ).pack(pady=(5, 25))

        return card

    def show_flashcards(self):
        self.highlight_menu_button(1)
        FlashcardWindow(self, self.db)

    def show_words(self):
        self.clear_main_container()

        for i, btn in enumerate(self.menu_buttons):
            if "Мої слова" in btn.cget("text"):
                self.highlight_menu_button(i)
                break

        from ui.main_app import MainApp

        temp_app = type('TempApp', (), {
            'db': self.db,
            'main_container': self.main_container,
            'exporter': self.exporter,
            'date_filter_start': self.date_filter_start,
            'date_filter_end': self.date_filter_end,
        })()

        MainApp.show_words(temp_app)

        self.date_filter_start = temp_app.date_filter_start
        self.date_filter_end = temp_app.date_filter_end

    def show_statistics(self):
        self.clear_main_container()

        for i, btn in enumerate(self.menu_buttons):
            if "Статистика" in btn.cget("text"):
                self.highlight_menu_button(i)
                break

        stats_window = StatisticsWindow(self.main_container, self.db)
        stats_window.exporter = self.exporter

    def show_add_word(self):
        self.clear_main_container()

        for i, btn in enumerate(self.menu_buttons):
            if "Додати слово" in btn.cget("text"):
                self.highlight_menu_button(i)
                break

        container = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=50, pady=30)

        title = ctk.CTkLabel(
            container,
            text="Додати нове слово",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        title.pack(pady=(0, 40))

        form = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=15)
        form.pack(fill="x", padx=100)

        fields = []
        self.create_form_field(form, "Слово*:", fields, 0)
        self.create_form_field(form, "Переклад*:", fields, 1)
        self.create_form_field(form, "Транскрипція:", fields, 2, "[həˈloʊ]")
        self.create_form_field(form, "Приклад речення:", fields, 3, "Hello, how are you?")
        self.create_form_field(form, "Переклад прикладу:", fields, 4, "Привіт, як справи?")

        cat_frame = ctk.CTkFrame(form, fg_color="transparent")
        cat_frame.pack(fill="x", padx=40, pady=15)

        ctk.CTkLabel(
            cat_frame,
            text="Категорія*:",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=200,
            anchor="w"
        ).pack(side="left")

        categories = self.db.get_categories()
        cat_names = [cat[1] for cat in categories]
        cat_var = ctk.StringVar(value=cat_names[0] if cat_names else "")

        ctk.CTkOptionMenu(
            cat_frame,
            values=cat_names,
            variable=cat_var,
            width=400,
            height=40
        ).pack(side="left", padx=20)

        diff_frame = ctk.CTkFrame(form, fg_color="transparent")
        diff_frame.pack(fill="x", padx=40, pady=15)

        ctk.CTkLabel(
            diff_frame,
            text="Складність:",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=200,
            anchor="w"
        ).pack(side="left")

        diff_var = ctk.StringVar(value="1")
        ctk.CTkOptionMenu(
            diff_frame,
            values=["1 - Легке", "2 - Середнє", "3 - Складне", "4 - Дуже складне", "5 - Експертне"],
            variable=diff_var,
            width=400,
            height=40
        ).pack(side="left", padx=20)

        def add_word():
            word = fields[0].get().strip()
            translation = fields[1].get().strip()

            if not word or not translation:
                messagebox.showwarning("Помилка", "Заповніть обов'язкові поля!")
                return

            cat_name = cat_var.get()
            cat_id = next((cat[0] for cat in categories if cat[1] == cat_name), 1)

            transcription = fields[2].get().strip()
            example = fields[3].get().strip()
            example_trans = fields[4].get().strip()
            difficulty = int(diff_var.get().split()[0])

            self.db.add_word(word, translation, cat_id, transcription, example, example_trans, difficulty)

            self.auth.log_action('CREATE', 'Words', None, None, f"Added word: {word}")

            messagebox.showinfo("Успіх", f"Слово '{word}' додано!")

            for field in fields:
                field.delete(0, 'end')

        ctk.CTkButton(
            form,
            text="➕ Додати слово",
            command=add_word,
            width=400,
            height=55,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669"
        ).pack(pady=40)

    def create_form_field(self, parent, label_text, fields_list, index, placeholder=""):
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.pack(fill="x", padx=40, pady=15)

        ctk.CTkLabel(
            field_frame,
            text=label_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            width=200,
            anchor="w"
        ).pack(side="left")

        entry = ctk.CTkEntry(
            field_frame,
            width=400,
            height=40,
            placeholder_text=placeholder
        )
        entry.pack(side="left", padx=20)
        fields_list.append(entry)

    def show_settings(self):
        self.clear_main_container()

        for i, btn in enumerate(self.menu_buttons):
            if "Налаштування" in btn.cget("text"):
                self.highlight_menu_button(i)
                break

        container = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=50, pady=30)

        title = ctk.CTkLabel(
            container,
            text="Налаштування",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        title.pack(pady=(0, 30))

        popup_frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=15)
        popup_frame.pack(fill="x", pady=15, padx=50)

        ctk.CTkLabel(
            popup_frame,
            text="🔔 Спливаючі вікна",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w", padx=30, pady=(20, 10))

        status_text = "🟢 Увімкнено" if self.popup_enabled else "🔴 Вимкнено"
        status_label = ctk.CTkLabel(
            popup_frame,
            text=f"Статус: {status_text}",
            font=ctk.CTkFont(size=14),
            text_color="#10B981" if self.popup_enabled else "#EF4444"
        )
        status_label.pack(anchor="w", padx=30, pady=5)

        switch_frame = ctk.CTkFrame(popup_frame, fg_color="transparent")
        switch_frame.pack(fill="x", padx=30, pady=15)

        ctk.CTkLabel(
            switch_frame,
            text="Увімкнути спливаючі вікна:",
            font=ctk.CTkFont(size=16)
        ).pack(side="left")

        popup_switch = ctk.CTkSwitch(
            switch_frame,
            text="",
            command=self.toggle_popups,
            onvalue=True,
            offvalue=False
        )
        if self.popup_enabled:
            popup_switch.select()
        popup_switch.pack(side="right")

        interval_frame = ctk.CTkFrame(popup_frame, fg_color="transparent")
        interval_frame.pack(fill="x", padx=30, pady=15)

        ctk.CTkLabel(
            interval_frame,
            text="Інтервал (хвилин):",
            font=ctk.CTkFont(size=16)
        ).pack(side="left")

        interval_entry = ctk.CTkEntry(interval_frame, width=100)
        interval_entry.insert(0, str(self.popup_interval // 60))
        interval_entry.pack(side="right")

        def save_settings():
            try:
                minutes = int(interval_entry.get())
                if minutes < 1:
                    raise ValueError

                old_interval = self.popup_interval
                self.popup_interval = minutes * 60

                if self.popup_enabled and old_interval != self.popup_interval:
                    self.popup_enabled = False
                    if self.popup_thread and self.popup_thread.is_alive():
                        self.popup_thread.join(timeout=1.0)
                    self.popup_enabled = True
                    self.start_popup_system()
                    messagebox.showinfo("Успіх",
                                        f"Налаштування збережено!\nНовий інтервал: {minutes} хв.")
                else:
                    messagebox.showinfo("Успіх", f"Налаштування збережено!")
            except ValueError:
                messagebox.showerror("Помилка", "Введіть коректне число!")

        ctk.CTkButton(
            popup_frame,
            text="💾 Зберегти",
            command=save_settings,
            width=200,
            height=45,
            fg_color="#3B82F6",
            hover_color="#2563EB"
        ).pack(pady=30)

    def toggle_popups(self):
        self.popup_enabled = not self.popup_enabled
        if self.popup_enabled:
            if self.popup_thread is None or not self.popup_thread.is_alive():
                self.start_popup_system()
                messagebox.showinfo("Увімкнено", "Спливаючі вікна увімкнено!")
        else:
            messagebox.showinfo("Вимкнено", "Спливаючі вікна вимкнено!")

    def start_popup_system(self):

        def show_popup_loop():
            while self.popup_enabled:
                time.sleep(self.popup_interval)
                if self.popup_enabled:
                    word_data = self.db.get_next_word_for_learning('popup')
                    if word_data:
                        self.show_popup_window(word_data)

        self.popup_thread = threading.Thread(target=show_popup_loop, daemon=True)
        self.popup_thread.start()

    def show_popup_window(self, word_data):

        def create_popup():
            PopupWindow(self, word_data, self.db)

        self.after(0, create_popup)

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

        for i, btn in enumerate(self.menu_buttons):
            if "Журнал" in btn.cget("text"):
                self.highlight_menu_button(i)
                break

        container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=20)

        title = ctk.CTkLabel(
            container,
            text="📋 Журнал подій",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        title.pack(pady=(0, 20))

        try:
            query = """
                    SELECT TOP 100
                    al.action_time, u.username,
                           al.action_type,
                           al.table_name,
                           al.new_value,
                           al.ip_address
                    FROM AuditLog al
                             LEFT JOIN Users u ON al.user_id = u.id
                    ORDER BY al.action_time DESC \
                    """
            self.db.cursor.execute(query)
            logs = self.db.cursor.fetchall()

            if logs:
                headers_frame = ctk.CTkFrame(container, fg_color="#334155", height=50)
                headers_frame.pack(fill="x", pady=(0, 5))
                headers_frame.pack_propagate(False)

                headers = ["Час", "Користувач", "Дія", "Таблиця", "Деталі", "IP"]
                widths = [150, 120, 100, 100, 300, 120]

                for header, width in zip(headers, widths):
                    ctk.CTkLabel(
                        headers_frame,
                        text=header,
                        font=ctk.CTkFont(size=13, weight="bold"),
                        width=width
                    ).pack(side="left", padx=10, pady=10)

                logs_frame = ctk.CTkScrollableFrame(container, fg_color="#1E293B")
                logs_frame.pack(fill="both", expand=True, pady=5)

                for log in logs:
                    row = ctk.CTkFrame(logs_frame, fg_color="#1E293B", height=50)
                    row.pack(fill="x", pady=2)
                    row.pack_propagate(False)

                    time_str = log[0].strftime("%d.%m.%Y %H:%M") if log[0] else "-"

                    ctk.CTkLabel(row, text=time_str, width=150, anchor="w").pack(side="left", padx=10)
                    ctk.CTkLabel(row, text=log[1] or "-", width=120, anchor="w").pack(side="left", padx=10)

                    action_colors = {
                        'CREATE': '#10B981',
                        'UPDATE': '#F59E0B',
                        'DELETE': '#EF4444',
                        'LOGIN': '#3B82F6',
                        'LOGOUT': '#64748B'
                    }
                    action_color = action_colors.get(log[2], '#94A3B8')

                    ctk.CTkLabel(
                        row,
                        text=log[2] or "-",
                        width=100,
                        anchor="w",
                        text_color=action_color
                    ).pack(side="left", padx=10)

                    ctk.CTkLabel(row, text=log[3] or "-", width=100, anchor="w").pack(side="left", padx=10)

                    details = log[4] or "-"
                    if len(details) > 40:
                        details = details[:37] + "..."

                    ctk.CTkLabel(
                        row,
                        text=details,
                        width=300,
                        anchor="w",
                        text_color="#94A3B8"
                    ).pack(side="left", padx=10)

                    ctk.CTkLabel(row, text=log[5] or "-", width=120, anchor="w").pack(side="left", padx=10)
            else:
                ctk.CTkLabel(
                    container,
                    text="Немає записів у журналі",
                    text_color="#94A3B8",
                    font=ctk.CTkFont(size=14)
                ).pack(pady=50)

        except Exception as e:
            ctk.CTkLabel(
                container,
                text=f"Помилка завантаження логів: {str(e)}",
                text_color="#EF4444",
                font=ctk.CTkFont(size=14)
            ).pack(pady=30)

    def show_welcome_message(self, user_data: dict):
        permissions = self.auth.get_user_permissions()

        welcome_text = f"""Вітаємо, {user_data.get('username', 'User')}!

Роль: {user_data.get('role_name', 'Невідома')}
Доступних дозволів: {len(permissions)}

Ви успішно увійшли в систему LearnEasy.
"""
        messagebox.showinfo("Вхід виконано", welcome_text)

    def logout(self):
        if messagebox.askyesno("Вихід", "Ви впевнені що хочете вийти?"):
            self.auth.log_action('LOGOUT', 'System', None, None, None)

            self.popup_enabled = False
            if self.popup_thread and self.popup_thread.is_alive():
                self.popup_thread.join(timeout=1.0)

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

            self.popup_enabled = False
            if self.popup_thread and self.popup_thread.is_alive():
                self.popup_thread.join(timeout=1.0)

            self.db.close()
            self.destroy()
            sys.exit(0)


def main():
    app = LearnEasyWithAuth()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()