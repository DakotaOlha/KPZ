import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
from typing import Optional


class AdminPanel(ctk.CTkFrame):
    def __init__(self, parent, auth_manager, user_manager, role_manager):
        super().__init__(parent, fg_color="transparent")

        self.auth = auth_manager
        self.user_manager = user_manager
        self.role_manager = role_manager

        self.create_widgets()

        self.load_users()

    def create_widgets(self):

        header = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        header.pack(fill="x", padx=20, pady=(20, 10))

        title = ctk.CTkLabel(
            header,
            text="👤 Управління користувачами",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(side="left", padx=20, pady=15)
        if self.auth.has_permission('users.create'):
            add_btn = ctk.CTkButton(
                header,
                text="➕ Додати користувача",
                command=self.show_create_user_dialog,
                height=40,
                fg_color="#10B981",
                hover_color="#059669"
            )
            add_btn.pack(side="right", padx=20, pady=10)

        filter_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        filter_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            filter_frame,
            text="🔍 Пошук:",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(20, 10), pady=10)

        self.search_entry = ctk.CTkEntry(
            filter_frame,
            width=250,
            height=35,
            placeholder_text="Ім'я користувача або email"
        )
        self.search_entry.pack(side="left", padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_users())

        ctk.CTkButton(
            filter_frame,
            text="🔄 Оновити",
            command=self.load_users,
            width=100,
            height=35,
            fg_color="#3B82F6"
        ).pack(side="right", padx=20, pady=10)

        self.create_users_table()

    def create_users_table(self):
        table_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        headers_frame = ctk.CTkFrame(table_frame, fg_color="#334155", height=50)
        headers_frame.pack(fill="x", padx=5, pady=(5, 0))
        headers_frame.pack_propagate(False)

        headers = ["ID", "Користувач", "Email", "Роль", "Статус", "Останній вхід", "Дії"]
        widths = [50, 150, 200, 120, 100, 150, 180]

        for header, width in zip(headers, widths):
            label = ctk.CTkLabel(
                headers_frame,
                text=header,
                font=ctk.CTkFont(size=13, weight="bold"),
                width=width
            )
            label.pack(side="left", padx=10, pady=10)

        self.users_scroll = ctk.CTkScrollableFrame(
            table_frame,
            fg_color="transparent"
        )
        self.users_scroll.pack(fill="both", expand=True, padx=5, pady=5)

    def load_users(self):

        for widget in self.users_scroll.winfo_children():
            widget.destroy()

        try:
            users = self.user_manager.get_all_users()

            if not users:
                no_data = ctk.CTkLabel(
                    self.users_scroll,
                    text="Немає користувачів або недостатньо прав для перегляду",
                    font=ctk.CTkFont(size=14),
                    text_color="#94A3B8"
                )
                no_data.pack(pady=50)
                return

            for user in users:
                self.create_user_row(user)

        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося завантажити користувачів:\n{str(e)}")

    def create_user_row(self, user: dict):

        row = ctk.CTkFrame(self.users_scroll, fg_color="#1E293B", height=70)
        row.pack(fill="x", pady=3)
        row.pack_propagate(False)

        ctk.CTkLabel(row, text=str(user['id']), width=50).pack(side="left", padx=10)

        username_label = ctk.CTkLabel(
            row,
            text=user['username'],
            width=150,
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        username_label.pack(side="left", padx=10)

        email_label = ctk.CTkLabel(
            row,
            text=user['email'] or "-",
            width=200,
            anchor="w",
            text_color="#94A3B8"
        )
        email_label.pack(side="left", padx=10)

        role_label = ctk.CTkLabel(
            row,
            text=user['role'],
            width=120,
            fg_color="#3B82F6",
            corner_radius=5
        )
        role_label.pack(side="left", padx=10, pady=15)

        if user['is_locked']:
            status_text = "🔒 Заблок."
            status_color = "#EF4444"
        elif not user['is_active']:
            status_text = "⏸️ Неактив."
            status_color = "#F59E0B"
        else:
            status_text = "✅ Активний"
            status_color = "#10B981"

        status_label = ctk.CTkLabel(
            row,
            text=status_text,
            width=100,
            text_color=status_color,
            font=ctk.CTkFont(weight="bold")
        )
        status_label.pack(side="left", padx=10)

        last_login = user['last_login']
        if last_login:
            if isinstance(last_login, str):
                last_login_text = last_login[:16]
            else:
                last_login_text = last_login.strftime("%d.%m.%Y %H:%M")
        else:
            last_login_text = "Ніколи"

        ctk.CTkLabel(
            row,
            text=last_login_text,
            width=150,
            text_color="#64748B"
        ).pack(side="left", padx=10)

        actions_frame = ctk.CTkFrame(row, fg_color="transparent", width=180)
        actions_frame.pack(side="right", padx=10)

        if self.auth.has_permission('users.edit'):
            ctk.CTkButton(
                actions_frame,
                text="✏️",
                width=35,
                height=35,
                command=lambda u=user: self.edit_user(u),
                fg_color="#3B82F6"
            ).pack(side="left", padx=2)

        if self.auth.has_permission('users.block'):
            if user['is_locked']:
                ctk.CTkButton(
                    actions_frame,
                    text="🔓",
                    width=35,
                    height=35,
                    command=lambda u=user: self.unblock_user(u),
                    fg_color="#10B981"
                ).pack(side="left", padx=2)
            else:
                ctk.CTkButton(
                    actions_frame,
                    text="🔒",
                    width=35,
                    height=35,
                    command=lambda u=user: self.block_user(u),
                    fg_color="#F59E0B"
                ).pack(side="left", padx=2)

        if self.auth.has_permission('users.delete'):
            if user['id'] != self.auth.current_user['user_id']:
                ctk.CTkButton(
                    actions_frame,
                    text="🗑️",
                    width=35,
                    height=35,
                    command=lambda u=user: self.delete_user(u),
                    fg_color="#EF4444"
                ).pack(side="left", padx=2)

    def filter_users(self):
        search_text = self.search_entry.get().lower()

        for row in self.users_scroll.winfo_children():
            if isinstance(row, ctk.CTkFrame):
                username_found = False
                for widget in row.winfo_children():
                    if isinstance(widget, ctk.CTkLabel):
                        text = widget.cget("text").lower()
                        if search_text in text:
                            username_found = True
                            break

                if username_found or not search_text:
                    row.pack(fill="x", pady=3)
                else:
                    row.pack_forget()

    def show_create_user_dialog(self):
        dialog = CreateUserDialog(self, self.user_manager, self.role_manager, self.load_users)

    def edit_user(self, user: dict):
        dialog = EditUserDialog(self, user, self.user_manager, self.role_manager, self.load_users)

    def block_user(self, user: dict):
        if messagebox.askyesno(
                "Блокування",
                f"Заблокувати користувача '{user['username']}'?"
        ):
            if self.user_manager.block_user(user['id'], "Заблоковано адміністратором"):
                messagebox.showinfo("Успіх", "Користувача заблоковано")
                self.load_users()
            else:
                messagebox.showerror("Помилка", "Не вдалося заблокувати користувача")

    def unblock_user(self, user: dict):
        if self.user_manager.unblock_user(user['id']):
            messagebox.showinfo("Успіх", "Користувача розблоковано")
            self.load_users()
        else:
            messagebox.showerror("Помилка", "Не вдалося розблокувати користувача")

    def delete_user(self, user: dict):
        if messagebox.askyesno(
                "Видалення",
                f"УВАГА! Видалити користувача '{user['username']}'?\nЦю дію неможливо скасувати!",
                icon='warning'
        ):
            if self.user_manager.delete_user(user['id']):
                messagebox.showinfo("Успіх", "Користувача видалено")
                self.load_users()
            else:
                messagebox.showerror("Помилка", "Не вдалося видалити користувача")


class CreateUserDialog(ctk.CTkToplevel):
    def __init__(self, parent, user_manager, role_manager, on_success_callback):
        super().__init__(parent)

        self.user_manager = user_manager
        self.role_manager = role_manager
        self.on_success = on_success_callback

        self.title("Створення користувача")
        self.geometry("500x600")
        self.resizable(False, False)

        self.center_window()

        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"500x600+{x}+{y}")

    def create_widgets(self):
        title = ctk.CTkLabel(
            self,
            text="Новий користувач",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(30, 20))

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=40)

        ctk.CTkLabel(form_frame, text="Ім'я користувача *:", anchor="w").pack(fill="x", pady=(10, 5))
        self.username_entry = ctk.CTkEntry(form_frame, height=40)
        self.username_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Пароль *:", anchor="w").pack(fill="x", pady=(10, 5))
        self.password_entry = ctk.CTkEntry(form_frame, height=40, show="●")
        self.password_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Email:", anchor="w").pack(fill="x", pady=(10, 5))
        self.email_entry = ctk.CTkEntry(form_frame, height=40)
        self.email_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Повне ім'я:", anchor="w").pack(fill="x", pady=(10, 5))
        self.fullname_entry = ctk.CTkEntry(form_frame, height=40)
        self.fullname_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Роль *:", anchor="w").pack(fill="x", pady=(10, 5))

        roles = self.role_manager.get_all_roles()
        role_names = [role['role_name'] for role in roles if role['is_active']]

        self.role_var = ctk.StringVar(value=role_names[0] if role_names else "")
        self.role_menu = ctk.CTkOptionMenu(
            form_frame,
            values=role_names,
            variable=self.role_var,
            height=40
        )
        self.role_menu.pack(fill="x", pady=(0, 20))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=30)

        ctk.CTkButton(
            btn_frame,
            text="Створити",
            command=self.create_user,
            width=150,
            height=45,
            fg_color="#10B981",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Скасувати",
            command=self.destroy,
            width=150,
            height=45,
            fg_color="#64748B"
        ).pack(side="left", padx=10)

    def create_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        email = self.email_entry.get().strip()
        fullname = self.fullname_entry.get().strip()
        role = self.role_var.get()

        if not username:
            messagebox.showwarning("Помилка", "Введіть ім'я користувача")
            return

        if not password:
            messagebox.showwarning("Помилка", "Введіть пароль")
            return

        if len(password) < 6:
            messagebox.showwarning("Помилка", "Пароль повинен містити мінімум 6 символів")
            return

        result = self.user_manager.create_user(
            username, password, email, fullname, role
        )

        if result['success']:
            messagebox.showinfo("Успіх", f"Користувача '{username}' створено!")
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            messagebox.showerror("Помилка", result['message'])


class EditUserDialog(ctk.CTkToplevel):
    def __init__(self, parent, user, user_manager, role_manager, on_success_callback):
        super().__init__(parent)

        self.user = user
        self.user_manager = user_manager
        self.role_manager = role_manager
        self.on_success = on_success_callback

        self.title(f"Редагування: {user['username']}")
        self.geometry("500x500")

        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f"500x500+{x}+{y}")

        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        title = ctk.CTkLabel(
            self,
            text=f"Редагування користувача",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(20, 10))

        info_label = ctk.CTkLabel(
            self,
            text=f"Username: {self.user['username']}",
            font=ctk.CTkFont(size=14),
            text_color="#94A3B8"
        )
        info_label.pack(pady=(0, 20))
        info_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        info_frame.pack(fill="both", expand=True, padx=40, pady=20)

        info_text = f"""
        Email: {self.user.get('email', 'Не вказано')}
        Роль: {self.user.get('role', 'Невідома')}
        Статус: {'Активний' if self.user.get('is_active') else 'Неактивний'}
        Заблокований: {'Так' if self.user.get('is_locked') else 'Ні'}
        Останній вхід: {self.user.get('last_login', 'Ніколи')}
        """

        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=13),
            justify="left"
        ).pack(pady=30, padx=30)

        ctk.CTkButton(
            self,
            text="Закрити",
            command=self.destroy,
            width=150,
            height=40
        ).pack(pady=20)