import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import threading
import time
import random

from database import DatabaseManager
from windows.edit_word_window import EditWordWindow
from windows.flashcard_window import FlashcardWindow
from windows.popup_window import PopupWindow


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        if not self.db.connect():
            self.destroy()
            return
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("Learn Easy - Вивчення слів")
        self.geometry("1200x750")
        self.popup_enabled = False
        self.popup_interval = 300
        self.popup_thread = None
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1E293B")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        logo_label = ctk.CTkLabel(
            self.sidebar,
            text="Learn Easy",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#3B82F6"
        )
        logo_label.pack(pady=35)
        self.menu_buttons = []
        btn_config = [
            ("📊 Дашборд", self.show_dashboard, "#3B82F6"),
            ("🃏 Картки", self.show_flashcards, "#8B5CF6"),
            ("📖 Мої слова", self.show_words, "#10B981"),
            ("📈 Статистика", self.show_statistics, "#F59E0B"),
            ("➕ Додати слово", self.show_add_word, "#F59E0B"),
            ("⚙️ Налаштування", self.show_settings, "#64748B"),
        ]
        for text, command, color in btn_config:
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
            btn.pack(pady=8, padx=15, fill="x")
            self.menu_buttons.append(btn)
        self.main_container = ctk.CTkFrame(self, fg_color="#0F172A")
        self.main_container.pack(side="right", fill="both", expand=True)
        self.show_dashboard()

    def clear_main_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def highlight_menu_button(self, index):
        for i, btn in enumerate(self.menu_buttons):
            if i == index:
                btn.configure(fg_color="#334155")
            else:
                btn.configure(fg_color="transparent")

    def show_dashboard(self):
        self.clear_main_container()
        self.highlight_menu_button(0)
        scroll_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=30, pady=20)
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
        progress_frame = ctk.CTkFrame(scroll_frame, fg_color="#1E293B", corner_radius=15)
        progress_frame.pack(fill="x", pady=30, padx=10)
        progress_label = ctk.CTkLabel(
            progress_frame,
            text="Загальний прогрес навчання",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        progress_label.pack(pady=(30, 15))
        progress = stats['progress_percentage'] / 100
        progress_bar = ctk.CTkProgressBar(progress_frame, width=500, height=25, corner_radius=12)
        progress_bar.pack(pady=15)
        progress_bar.set(progress)
        percentage_label = ctk.CTkLabel(
            progress_frame,
            text=f"{stats['progress_percentage']:.1f}% слів вивчено",
            font=ctk.CTkFont(size=18),
            text_color="#64748B"
        )
        percentage_label.pack(pady=(5, 30))
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
        icon_label = ctk.CTkLabel(
            card,
            text=icon,
            font=ctk.CTkFont(size=40)
        )
        icon_label.pack(pady=(25, 5))
        value_label = ctk.CTkLabel(
            card,
            text=str(value),
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color="white"
        )
        value_label.pack(pady=5)
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=16),
            text_color="white"
        )
        title_label.pack(pady=(5, 25))
        return card

    def show_flashcards(self):
        self.highlight_menu_button(1)
        FlashcardWindow(self, self.db)

    def show_statistics(self):
        self.highlight_menu_button(3)
        from windows.statistics_window import StatisticsWindow
        StatisticsWindow(self, self.db)

    def show_words(self):
        self.clear_main_container()
        self.highlight_menu_button(2)
        container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=20)
        title = ctk.CTkLabel(
            container,
            text="Мої слова",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        title.pack(anchor="w", pady=(0, 20))
        filter_frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=10)
        filter_frame.pack(fill="x", pady=10)
        search_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        search_frame.pack(side="left", padx=15, pady=15)
        ctk.CTkLabel(search_frame, text="🔍 Пошук:").pack(side="left", padx=(0, 10))
        self.search_entry = ctk.CTkEntry(search_frame, width=250, height=35)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_words())
        cat_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        cat_frame.pack(side="left", padx=15, pady=15)
        ctk.CTkLabel(cat_frame, text="📁 Категорія:").pack(side="left", padx=(0, 10))
        categories = ["Всі"] + [cat[1] for cat in self.db.get_categories()]
        self.category_var = ctk.StringVar(value="Всі")
        self.category_menu = ctk.CTkOptionMenu(
            cat_frame,
            values=categories,
            variable=self.category_var,
            width=180,
            height=35,
            command=lambda x: self.load_words()
        )
        self.category_menu.pack(side="left")
        sort_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        sort_frame.pack(side="left", padx=15, pady=15)
        ctk.CTkLabel(sort_frame, text="↕️ Сортування:").pack(side="left", padx=(0, 10))
        self.sort_var = ctk.StringVar(value="word")
        self.sort_menu = ctk.CTkOptionMenu(
            sort_frame,
            values=["word", "translation", "knowledge_level", "category", "difficulty"],
            variable=self.sort_var,
            width=180,
            height=35,
            command=lambda x: self.load_words()
        )
        self.sort_menu.pack(side="left")
        group_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        group_frame.pack(side="left", padx=15, pady=15)
        ctk.CTkLabel(group_frame, text="📊 Групування:").pack(side="left", padx=(0, 10))
        self.group_var = ctk.StringVar(value="none")
        self.group_menu = ctk.CTkOptionMenu(
            group_frame,
            values=["none", "category", "knowledge_level", "difficulty"],
            variable=self.group_var,
            width=180,
            height=35,
            command=lambda x: self.load_words()
        )
        self.group_menu.pack(side="left")
        self.words_scroll_frame = ctk.CTkScrollableFrame(container, fg_color="#1E293B")
        self.words_scroll_frame.pack(fill="both", expand=True, pady=10)
        self.load_words()

    def load_words(self):
        for widget in self.words_scroll_frame.winfo_children():
            widget.destroy()

        search = self.search_entry.get() if hasattr(self, 'search_entry') else ""
        category = self.category_var.get() if hasattr(self, 'category_var') else "Всі"
        sort = self.sort_var.get() if hasattr(self, 'sort_var') else "word"
        group = self.group_var.get() if hasattr(self, 'group_var') else "none"

        words = self.db.get_all_words(search, category, sort)

        if group == "none":
            self.display_words_table(words)
        else:
            self.display_grouped_words(words, group)

    def display_words_table(self, words):
        headers_frame = ctk.CTkFrame(self.words_scroll_frame, fg_color="#334155", height=50)
        headers_frame.pack(fill="x", pady=(0, 5))
        headers = ["⭐", "Слово", "Переклад", "Рівень", "Категорія", "Статистика", "Дії"]
        widths = [50, 200, 200, 120, 150, 180, 120]
        for header, width in zip(headers, widths):
            ctk.CTkLabel(
                headers_frame,
                text=header,
                font=ctk.CTkFont(size=14, weight="bold"),
                width=width
            ).pack(side="left", padx=10, pady=10)

        for word in words:
            self.create_word_row(word)

    def display_grouped_words(self, words, group_by):
        from itertools import groupby

        group_labels = {
            "category": lambda w: w[5] or "Без категорії",
            "knowledge_level": lambda w: f"Рівень {w[4]}",
            "difficulty": lambda w: ["Легке", "Середнє", "Складне", "Дуже складне", "Експертне"][min(w[10] - 1, 4)]
        }

        get_group = group_labels.get(group_by)
        if not get_group:
            self.display_words_table(words)
            return

        sorted_words = sorted(words, key=get_group)

        for group_name, group_items in groupby(sorted_words, key=get_group):
            group_frame = ctk.CTkFrame(self.words_scroll_frame, fg_color="transparent")
            group_frame.pack(fill="x", pady=(20, 5), padx=10)

            header_label = ctk.CTkLabel(
                group_frame,
                text=f"▼ {group_name}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#3B82F6"
            )
            header_label.pack(anchor="w", pady=(0, 10))

            inner_frame = ctk.CTkFrame(self.words_scroll_frame, fg_color="#1E293B")
            inner_frame.pack(fill="x", pady=(0, 10))

            for word in group_items:
                self.create_word_row(word, parent=inner_frame)

    def create_word_row(self, word, parent=None):
        if parent is None:
            parent = self.words_scroll_frame

        row = ctk.CTkFrame(parent, fg_color="#1E293B", height=60)
        row.pack(fill="x", pady=2)
        fav_btn = ctk.CTkButton(
            row,
            text="⭐" if word[9] else "☆",
            command=lambda: self.toggle_favorite(word[0]),
            width=50,
            fg_color="transparent",
            hover_color="#334155"
        )
        fav_btn.pack(side="left", padx=10)
        ctk.CTkLabel(row, text=word[1], width=200, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(row, text=word[2], width=200, anchor="w", text_color="#94A3B8").pack(side="left", padx=10)
        level_frame = ctk.CTkFrame(row, width=120, fg_color="transparent")
        level_frame.pack(side="left", padx=10)
        progress = min(word[4] / 10, 1.0)
        bar = ctk.CTkProgressBar(level_frame, width=100)
        bar.set(progress)
        bar.pack()
        cat_color = "#64748B"
        ctk.CTkLabel(
            row,
            text=word[5] or "-",
            width=150,
            anchor="w",
            text_color=cat_color
        ).pack(side="left", padx=10)
        stats_text = f"✓{word[7]} ✗{word[8]} ({word[6]})"
        ctk.CTkLabel(row, text=stats_text, width=180, anchor="w", text_color="#64748B").pack(side="left", padx=10)
        actions_frame = ctk.CTkFrame(row, fg_color="transparent", width=120)
        actions_frame.pack(side="left", padx=10)
        ctk.CTkButton(
            actions_frame,
            text="✏️",
            width=35,
            command=lambda: self.edit_word(word[0]),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            actions_frame,
            text="🗑️",
            width=35,
            command=lambda: self.delete_word(word[0]),
            fg_color="#EF4444",
            hover_color="#DC2626"
        ).pack(side="left", padx=2)

    def edit_word(self, word_id):
        EditWordWindow(self, self.db, word_id, self.load_words)

    def toggle_favorite(self, word_id):
        self.db.toggle_favorite(word_id)
        self.load_words()

    def delete_word(self, word_id):
        if messagebox.askyesno("Підтвердження", "Видалити це слово?"):
            self.db.delete_word(word_id)
            self.load_words()

    def show_add_word(self):
        self.clear_main_container()
        self.highlight_menu_button(4)
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
        self.highlight_menu_button(5)
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
                                        f"Налаштування збережено!\nНовий інтервал: {minutes} хв.\nPopup перезапущено.")
                else:
                    messagebox.showinfo("Успіх", f"Налаштування збережено!\nНовий інтервал: {minutes} хв.")
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
        info_frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=15)
        info_frame.pack(fill="x", pady=15, padx=50)
        ctk.CTkLabel(
            info_frame,
            text="💡 Підказка",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w", padx=30, pady=(20, 10))
        ctk.CTkLabel(
            info_frame,
            text="Спливаючі вікна з'являються у правому верхньому куті екрану.\nВони показують в першу чергу нові слова, потім ті що вивчаються,\nта час від часу вивчені слова для повторення.\n\n⏱️ Вікно з'являється кожні " + str(
                self.popup_interval // 60) + " хвилин після увімкнення.\n⏳ Кожне вікно автоматично зникає через 15 секунд.",
            font=ctk.CTkFont(size=14),
            text_color="#94A3B8",
            justify="left"
        ).pack(anchor="w", padx=30, pady=(0, 20))

    def toggle_popups(self):
        self.popup_enabled = not self.popup_enabled
        if self.popup_enabled:
            if self.popup_thread is None or not self.popup_thread.is_alive():
                self.start_popup_system()
                messagebox.showinfo("Увімкнено", "Спливаючі вікна увімкнено!")
            else:
                messagebox.showinfo("Увімкнено", "Спливаючі вікна вже працюють!")
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

    def on_closing(self):
        self.popup_enabled = False
        if self.popup_thread and self.popup_thread.is_alive():
            self.popup_thread.join(timeout=1.0)
        self.db.close()
        self.destroy()