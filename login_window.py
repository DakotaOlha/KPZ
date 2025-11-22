import customtkinter as ctk
from tkinter import messagebox
import socket


class LoginWindow(ctk.CTk):

    def __init__(self, auth_manager, on_success_callback, db_manager):
        super().__init__()

        self.auth = auth_manager
        self.on_success_callback = on_success_callback
        self.db_manager = db_manager

        self.title("Learn Easy - Вхід в систему")
        self.geometry("500x750")
        self.resizable(False, False)

        self.center_window()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.create_widgets()

        self.bind('<Return>', lambda e: self.login())

    def center_window(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 750) // 2
        self.geometry(f"500x750+{x}+{y}")

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Logo
        logo_frame = ctk.CTkFrame(main_frame, fg_color="#1E293B", corner_radius=15)
        logo_frame.pack(fill="x", pady=(0, 30))

        app_title = ctk.CTkLabel(
            logo_frame,
            text="Learn Easy",
            font=ctk.CTkFont(size=42, weight="bold"),
            text_color="#3B82F6"
        )
        app_title.pack(pady=(30, 10))

        subtitle = ctk.CTkLabel(
            logo_frame,
            text="Система управління навчанням",
            font=ctk.CTkFont(size=16),
            text_color="#94A3B8"
        )
        subtitle.pack(pady=(0, 30))

        # Form
        form_frame = ctk.CTkFrame(main_frame, fg_color="#1E293B", corner_radius=15)
        form_frame.pack(fill="both", expand=True)

        form_title = ctk.CTkLabel(
            form_frame,
            text="Вхід в систему",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        form_title.pack(pady=(30, 20))

        # Тип автентифікації
        auth_type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        auth_type_frame.pack(fill="x", padx=40, pady=(10, 20))

        ctk.CTkLabel(
            auth_type_frame,
            text="Тип автентифікації",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 10))

        self.auth_type_var = ctk.StringVar(value="windows")

        auth_radio_frame = ctk.CTkFrame(auth_type_frame, fg_color="transparent")
        auth_radio_frame.pack(fill="x")

        ctk.CTkRadioButton(
            auth_radio_frame,
            text="🔐 Windows (Trusted)",
            variable=self.auth_type_var,
            value="windows",
            command=self.toggle_credentials_fields,
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=(0, 20))

        ctk.CTkRadioButton(
            auth_radio_frame,
            text="👤 SQL Server",
            variable=self.auth_type_var,
            value="sql",
            command=self.toggle_credentials_fields,
            font=ctk.CTkFont(size=13)
        ).pack(side="left")

        # Контейнер для SQL полів (буде показуватись/ховатись)
        self.sql_fields_container = ctk.CTkFrame(form_frame, fg_color="transparent")

        # Username
        username_label = ctk.CTkLabel(
            self.sql_fields_container,
            text="Ім'я користувача SQL",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        username_label.pack(fill="x", padx=40, pady=(10, 5))

        self.username_entry = ctk.CTkEntry(
            self.sql_fields_container,
            height=45,
            font=ctk.CTkFont(size=14),
            placeholder_text="learneasy_student"
        )
        self.username_entry.pack(fill="x", padx=40, pady=(0, 15))

        # Password
        password_label = ctk.CTkLabel(
            self.sql_fields_container,
            text="Пароль SQL",
            font=ctk.CTkFont(size=14),
            anchor="w"
        )
        password_label.pack(fill="x", padx=40, pady=(10, 5))

        self.password_entry = ctk.CTkEntry(
            self.sql_fields_container,
            height=45,
            font=ctk.CTkFont(size=14),
            placeholder_text="Введіть пароль",
            show="●"
        )
        self.password_entry.pack(fill="x", padx=40, pady=(0, 10))

        self.show_password_var = ctk.BooleanVar(value=False)
        show_password_checkbox = ctk.CTkCheckBox(
            self.sql_fields_container,
            text="Показати пароль",
            variable=self.show_password_var,
            command=self.toggle_password_visibility,
            font=ctk.CTkFont(size=12)
        )
        show_password_checkbox.pack(anchor="w", padx=40, pady=(0, 20))

        # Спочатку ховаємо SQL поля (Windows auth за замовчуванням)
        self.toggle_credentials_fields()

        # Login button
        self.login_button = ctk.CTkButton(
            form_frame,
            text="Увійти",
            command=self.login,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.login_button.pack(fill="x", padx=40, pady=(20, 15))

        self.status_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#EF4444"
        )
        self.status_label.pack(pady=(5, 20))

        # Hint
        hint_frame = ctk.CTkFrame(form_frame, fg_color="#334155", corner_radius=10)
        hint_frame.pack(fill="x", padx=40, pady=(10, 30))

        hint_label = ctk.CTkLabel(
            hint_frame,
            text="💡 SQL Login:\nStudent: learneasy_student / Student123!\nTeacher: learneasy_teacher / Teacher123!\n\nWindows: використовує admin / admin123",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            justify="left"
        )
        hint_label.pack(pady=15, padx=15)

    def toggle_credentials_fields(self):
        """Показати/приховати поля SQL логіна"""
        if self.auth_type_var.get() == "windows":
            # Ховаємо SQL поля
            self.sql_fields_container.pack_forget()
        else:
            # Показуємо SQL поля
            self.sql_fields_container.pack(fill="x", pady=(10, 0))
            self.username_entry.focus()

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="●")

    def login(self):
        auth_type = self.auth_type_var.get()

        # Визначаємо облікові дані залежно від типу автентифікації
        if auth_type == "sql":
            sql_username = self.username_entry.get().strip()
            sql_password = self.password_entry.get().strip()

            if not sql_username:
                self.show_error("Введіть ім'я користувача SQL")
                self.username_entry.focus()
                return

            if not sql_password:
                self.show_error("Введіть пароль SQL")
                self.password_entry.focus()
                return

            # Перепідключаємося до БД з SQL credentials
            self.status_label.configure(text="Підключення до БД...", text_color="#F59E0B")
            self.update()

            if not self.db_manager.reconnect_with_credentials(sql_username, sql_password):
                self.show_error("Не вдалося підключитися з цими обліковими даними")
                return

            # Оновлюємо auth_manager з новим підключенням
            self.auth.conn = self.db_manager.conn
            self.auth.cursor = self.db_manager.cursor

            # Для системи ролей використовуємо той самий username
            username = sql_username
            password = sql_password

        else:
            # Windows Authentication
            username = "admin"
            password = "admin123"

        self.login_button.configure(state="disabled", text="Вхід...")
        self.status_label.configure(text="Перевірка даних...", text_color="#F59E0B")

        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except:
            ip_address = "127.0.0.1"

        self.update()

        try:
            result = self.auth.login(username, password, ip_address)

            if result['success']:
                self.show_success("Успішний вхід!")
                self.after(500, self.on_login_success)
            else:
                self.show_error(result.get('message', 'Невірне ім\'я користувача або пароль'))
                self.login_button.configure(state="normal", text="Увійти")

        except Exception as e:
            self.show_error(f"Помилка: {str(e)}")
            self.login_button.configure(state="normal", text="Увійти")

    def on_login_success(self):
        user_data = self.auth.get_current_user()
        self.withdraw()
        if self.on_success_callback:
            self.on_success_callback(user_data)
        self.destroy()

    def show_error(self, message: str):
        self.status_label.configure(text=f"❌ {message}", text_color="#EF4444")

    def show_success(self, message: str):
        self.status_label.configure(text=f"✅ {message}", text_color="#10B981")

    def run(self):
        self.mainloop()


class QuickLoginDialog(ctk.CTkToplevel):

    def __init__(self, parent, auth_manager, message="Ваша сесія закінчилась. Увійдіть знову."):
        super().__init__(parent)

        self.auth = auth_manager
        self.result = None

        self.title("Повторний вхід")
        self.geometry("400x350")
        self.resizable(False, False)

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 350) // 2
        self.geometry(f"400x350+{x}+{y}")

        self.transient(parent)
        self.grab_set()

        self.create_widgets(message)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def create_widgets(self, message):

        msg_label = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        msg_label.pack(pady=(30, 20))

        # Username
        ctk.CTkLabel(self, text="Ім'я користувача:").pack(pady=(10, 5))
        self.username_entry = ctk.CTkEntry(self, width=300, height=40)
        self.username_entry.pack(pady=(0, 15))

        # Password
        ctk.CTkLabel(self, text="Пароль:").pack(pady=(10, 5))
        self.password_entry = ctk.CTkEntry(self, width=300, height=40, show="●")
        self.password_entry.pack(pady=(0, 20))

        # Кнопки
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Увійти",
            command=self.on_login,
            width=120,
            height=40,
            fg_color="#3B82F6"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Скасувати",
            command=self.on_cancel,
            width=120,
            height=40,
            fg_color="#64748B"
        ).pack(side="left", padx=10)

        self.bind('<Return>', lambda e: self.on_login())

    def on_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username:
            messagebox.showwarning("Помилка", "Введіть ім'я користувача")
            self.username_entry.focus()
            return

        if not password:
            messagebox.showwarning("Помилка", "Введіть пароль")
            self.password_entry.focus()
            return

        self.update()  # оновлення GUI перед блокуючим викликом

        try:
            import socket
            ip_address = socket.gethostbyname(socket.gethostname())
        except:
            ip_address = "127.0.0.1"

        try:
            result = self.auth.login(username, password, ip_address)

            if result.get('success'):
                self.result = True
                self.destroy()
            else:
                messagebox.showerror("Помилка", result.get('message', 'Невірні дані'))

        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка входу: {str(e)}")

    def on_cancel(self):
        self.result = False
        self.destroy()

    def get_result(self):
        return self.result