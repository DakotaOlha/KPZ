import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
import threading
import time
import random
import calendar
from dateutil.relativedelta import relativedelta

from DataExporter import DataExporter
from database import DatabaseManager
from windows.edit_word_window import EditWordWindow
from windows.flashcard_window import FlashcardWindow
from windows.popup_window import PopupWindow


class DatePickerFrame(ctk.CTkFrame):

    def __init__(self, parent, on_date_selected):
        super().__init__(parent, fg_color="#1E293B", corner_radius=8)
        self.on_date_selected = on_date_selected
        self.current_date = datetime.now()
        self.build_calendar()

    def build_calendar(self):
        for widget in self.winfo_children():
            widget.destroy()

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=3)

        ctk.CTkButton(header, text="◀", width=25, command=self.prev_month,
                      fg_color="#3B82F6", hover_color="#2563EB").pack(side="left")

        self.month_label = ctk.CTkLabel(header, text=self.current_date.strftime("%B %Y"),
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.month_label.pack(side="left", expand=True)

        ctk.CTkButton(header, text="▶", width=25, command=self.next_month,
                      fg_color="#3B82F6", hover_color="#2563EB").pack(side="right")

        cal_frame = ctk.CTkFrame(self, fg_color="transparent")
        cal_frame.pack(padx=8, pady=5)

        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
        for i, d in enumerate(days):
            ctk.CTkLabel(cal_frame, text=d, text_color="#94A3B8",
                         font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=i, padx=2, pady=2)

        month_matrix = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        for r, week in enumerate(month_matrix, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    continue
                d_obj = datetime(self.current_date.year, self.current_date.month, day)
                is_today = d_obj.date() == datetime.now().date()
                color = "#3B82F6" if is_today else "#334155"
                ctk.CTkButton(cal_frame, text=str(day), width=25, height=25,
                              fg_color=color, hover_color="#475569",
                              command=lambda d=d_obj: self.select_date(d)).grid(row=r, column=c, padx=2, pady=2)

    def select_date(self, date_obj):
        self.on_date_selected(date_obj)

    def prev_month(self):
        self.current_date -= relativedelta(months=1)
        self.build_calendar()

    def next_month(self):
        self.current_date += relativedelta(months=1)
        self.build_calendar()


class DropdownDatePicker:

    def __init__(self, parent, on_date_selected, button_text="📅"):
        self.parent = parent
        self.on_date_selected = on_date_selected
        self.button_text = button_text
        self.date_picker_frame = None
        self.is_visible = False

        # Створюємо кнопку для відкриття календаря
        self.button = ctk.CTkButton(
            parent,
            text=button_text,
            width=40,
            height=35,
            command=self.toggle_calendar,
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )

    def toggle_calendar(self):
        if self.is_visible:
            self.hide_calendar()
        else:
            self.show_calendar()

    def show_calendar(self):
        if self.date_picker_frame is None:
            self.date_picker_frame = DatePickerFrame(self.parent, self._on_date_selected)

        self.date_picker_frame.pack(fill="x", pady=(5, 0))
        self.is_visible = True

    def hide_calendar(self):
        if self.date_picker_frame:
            self.date_picker_frame.pack_forget()
            self.is_visible = False

    def _on_date_selected(self, date_obj):
        self.hide_calendar()
        self.on_date_selected(date_obj)

    def pack(self, **kwargs):
        self.button.pack(**kwargs)


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        if not self.db.connect():
            self.destroy()
            return

        self.exporter = DataExporter(self.db)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("Learn Easy - Вивчення слів")

        self.popup_enabled = False
        self.popup_interval = 300
        self.popup_thread = None

        self.date_filter_start = None
        self.date_filter_end = None

        self.create_widgets()

        self.after(50, lambda: self.state('zoomed'))

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
        self.clear_main_container()
        self.highlight_menu_button(3)
        from windows.statistics_window import StatisticsWindow
        stats_window = StatisticsWindow(self.main_container, self.db)
        stats_window.exporter = self.exporter

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

        filter_row1 = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_row1.pack(fill="x", padx=15, pady=10)

        search_frame = ctk.CTkFrame(filter_row1, fg_color="transparent")
        search_frame.pack(side="left", padx=(0, 15))
        ctk.CTkLabel(search_frame, text="🔍 Пошук:").pack(side="left", padx=(0, 10))
        self.search_entry = ctk.CTkEntry(search_frame, width=250, height=35)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_words())

        cat_frame = ctk.CTkFrame(filter_row1, fg_color="transparent")
        cat_frame.pack(side="left", padx=15)
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

        sort_frame = ctk.CTkFrame(filter_row1, fg_color="transparent")
        sort_frame.pack(side="left", padx=15)
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

        group_frame = ctk.CTkFrame(filter_row1, fg_color="transparent")
        group_frame.pack(side="left", padx=15)
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

        filter_row2 = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_row2.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(filter_row2, text="📅 Період додання:").pack(side="left", padx=(0, 10))

        for period, days in [("Всі", None), ("Сьогодні", 0), ("7 днів", 7), ("30 днів", 30)]:
            ctk.CTkButton(
                filter_row2,
                text=period,
                width=90,
                height=35,
                command=lambda d=days: self.set_date_filter(d),
                fg_color="#3B82F6",
                hover_color="#2563EB"
            ).pack(side="left", padx=5)

        self.date_filter_label = ctk.CTkLabel(
            filter_row2,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.date_filter_label.pack(side="left", padx=(20, 0))

        calendar_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        calendar_frame.pack(fill="x", padx=15, pady=10)

        start_frame = ctk.CTkFrame(calendar_frame, fg_color="transparent")
        start_frame.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(start_frame, text="Від:").pack(side="left", padx=(0, 10))

        self.start_date_picker = DropdownDatePicker(
            start_frame,
            lambda d: self.on_start_date_selected(d),
            "📅"
        )
        self.start_date_picker.pack(side="left")

        end_frame = ctk.CTkFrame(calendar_frame, fg_color="transparent")
        end_frame.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(end_frame, text="До:").pack(side="left", padx=(0, 10))

        self.end_date_picker = DropdownDatePicker(
            end_frame,
            lambda d: self.on_end_date_selected(d),
            "📅"
        )
        self.end_date_picker.pack(side="left")

        ctk.CTkButton(
            calendar_frame,
            text="✕ Очистити",
            width=100,
            height=35,
            command=self.clear_date_filter,
            fg_color="#EF4444",
            hover_color="#DC2626"
        ).pack(side="left", padx=20)

        export_frame = ctk.CTkFrame(calendar_frame, fg_color="transparent")
        export_frame.pack(side="left", padx=(50, 0))

        ctk.CTkButton(
            export_frame,
            text="📄 Word",
            width=80,
            height=35,
            command=self.exporter.export_to_word,
            fg_color="#3B82F6",
            hover_color="#2563EB"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            export_frame,
            text="📊 Excel",
            width=80,
            height=35,
            command=self.exporter.export_to_excel,
            fg_color="#10B981",
            hover_color="#059669"
        ).pack(side="left", padx=5)

        self.words_scroll_frame = ctk.CTkScrollableFrame(container, fg_color="#1E293B")
        self.words_scroll_frame.pack(fill="both", expand=True, pady=10)
        self.load_words()

    def set_date_filter(self, days):
        if days is None:
            self.date_filter_start = None
            self.date_filter_end = None
            self.date_filter_label.configure(text="")
        else:
            today = datetime.now().date()
            self.date_filter_end = today
            self.date_filter_start = today - timedelta(days=days)
            self.date_filter_label.configure(
                text=f"З {self.date_filter_start.strftime('%d.%m.%Y')} по {self.date_filter_end.strftime('%d.%m.%Y')}"
            )
        self.load_words()

    def on_start_date_selected(self, date_obj):
        self.date_filter_start = date_obj.date()
        self.update_date_filter_label()
        self.load_words()

    def on_end_date_selected(self, date_obj):
        self.date_filter_end = date_obj.date()
        self.update_date_filter_label()
        self.load_words()

    def update_date_filter_label(self):
        if self.date_filter_start and self.date_filter_end:
            self.date_filter_label.configure(
                text=f"З {self.date_filter_start.strftime('%d.%m.%Y')} по {self.date_filter_end.strftime('%d.%m.%Y')}"
            )
        elif self.date_filter_start:
            self.date_filter_label.configure(
                text=f"З {self.date_filter_start.strftime('%d.%m.%Y')}"
            )
        elif self.date_filter_end:
            self.date_filter_label.configure(
                text=f"До {self.date_filter_end.strftime('%d.%m.%Y')}"
            )
        else:
            self.date_filter_label.configure(text="")

    def clear_date_filter(self):
        self.date_filter_start = None
        self.date_filter_end = None
        self.date_filter_label.configure(text="")
        self.start_date_picker.hide_calendar()
        self.end_date_picker.hide_calendar()
        self.load_words()

    def load_words(self):
        for widget in self.words_scroll_frame.winfo_children():
            widget.destroy()

        search = self.search_entry.get() if hasattr(self, 'search_entry') else ""

        if search and search.strip():
            words = self.db.search_words_smart(search)
            self.display_smart_search_results(words, search)
        else:
            category = self.category_var.get() if hasattr(self, 'category_var') else "Всі"
            sort = self.sort_var.get() if hasattr(self, 'sort_var') else "word"
            group = self.group_var.get() if hasattr(self, 'group_var') else "none"

            words = self.db.get_all_words(
                search, category, sort,
                start_date=self.date_filter_start,
                end_date=self.date_filter_end
            )

            print(f"Loaded {len(words)} words from database")

            if not words:
                no_data_label = ctk.CTkLabel(
                    self.words_scroll_frame,
                    text="Слова не знайдені",
                    font=ctk.CTkFont(size=16),
                    text_color="#94A3B8"
                )
                no_data_label.pack(pady=50)
                return

            if group == "none":
                self.display_words_table(words)
            else:
                self.display_grouped_words(words, group)

    def display_smart_search_results(self, words, search_term):

        header_label = ctk.CTkLabel(
            self.words_scroll_frame,
            text=f"🔍 Результати пошуку за '{search_term}' ({len(words)} слів)",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#3B82F6"
        )
        header_label.pack(anchor="w", padx=10, pady=10)

        if not words:
            no_results = ctk.CTkLabel(
                self.words_scroll_frame,
                text="Слів не знайдено",
                font=ctk.CTkFont(size=14),
                text_color="#94A3B8"
            )
            no_results.pack(pady=30)
            return

        for word in words:
            self.create_search_result_row(word, search_term)

    def create_search_result_row(self, word, search_term):
        try:
            row = ctk.CTkFrame(self.words_scroll_frame, fg_color="#1E293B", height=80)
            row.pack(fill="x", pady=3, padx=5)
            row.pack_propagate(False)

            word_id = word[0]
            word_text = word[1]
            translation = word[2]
            knowledge_level = word[4] if len(word) > 4 else 0
            category = word[5] if len(word) > 5 else "-"
            times_correct = word[7] if len(word) > 7 else 0
            times_wrong = word[8] if len(word) > 8 else 0
            is_favorite = word[9] if len(word) > 9 else False
            difficulty = word[10] if len(word) > 10 else 1
            highlight_type = word[14] if len(word) > 14 else 'NO_HIGHLIGHT'

            if knowledge_level >= 5:
                status = "Вивчено"
            elif knowledge_level > 0:
                status = "Вивчається"
            else:
                status = "Нове"

            highlight_colors = {
                'HIGHLIGHT_STRONG': ('#10B981', '🎯'),
                'HIGHLIGHT_MEDIUM': ('#3B82F6', '✓'),
                'HIGHLIGHT_LIGHT': ('#F59E0B', '◐'),
                'NO_HIGHLIGHT': ('#475569', '○')
            }

            color, icon = highlight_colors.get(highlight_type, ('#475569', '○'))

            highlight_btn = ctk.CTkButton(
                row,
                text=icon,
                width=40,
                height=40,
                fg_color=color,
                hover_color=color,
                text_color="white",
                state="disabled"
            )
            highlight_btn.pack(side="left", padx=5, pady=10)

            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10)

            word_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            word_frame.pack(fill="x", pady=5)

            ctk.CTkLabel(
                word_frame,
                text=word_text,
                font=ctk.CTkFont(size=16, weight="bold"),
                anchor="w"
            ).pack(side="left", padx=5)

            ctk.CTkLabel(
                word_frame,
                text=f"→ {translation}",
                font=ctk.CTkFont(size=14),
                text_color="#94A3B8",
                anchor="w"
            ).pack(side="left", padx=10)

            stats_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            stats_frame.pack(fill="x", pady=2)

            difficulty_text = ["Легке", "Середнє", "Складне", "Дуже складне", "Експертне"][min(difficulty - 1, 4)]

            stats_text = f"{category} | {status} | {difficulty_text} | ✓{times_correct} ✗{times_wrong}"
            ctk.CTkLabel(
                stats_frame,
                text=stats_text,
                font=ctk.CTkFont(size=12),
                text_color="#64748B",
                anchor="w"
            ).pack(side="left", padx=5)

            progress_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            progress_frame.pack(fill="x", pady=2)

            progress = min(knowledge_level / 10, 1.0)
            progress_bar = ctk.CTkProgressBar(progress_frame, width=200, height=6)
            progress_bar.set(progress)
            progress_bar.pack(side="left", padx=5)

            progress_text = f"{knowledge_level}/10"
            ctk.CTkLabel(
                progress_frame,
                text=progress_text,
                font=ctk.CTkFont(size=11),
                text_color="#64748B",
                width=40
            ).pack(side="left", padx=5)

            actions_frame = ctk.CTkFrame(row, fg_color="transparent", width=120)
            actions_frame.pack(side="right", padx=10)
            actions_frame.pack_propagate(False)

            ctk.CTkButton(
                actions_frame,
                text="✏️",
                width=35,
                height=35,
                command=lambda wid=word_id: self.edit_word(wid),
                fg_color="#3B82F6",
                hover_color="#2563EB"
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                actions_frame,
                text="⭐" if is_favorite else "☆",
                width=35,
                height=35,
                command=lambda wid=word_id: self.toggle_favorite(wid),
                fg_color="#FFB800" if is_favorite else "#64748B",
                hover_color="#FFC814"
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                actions_frame,
                text="🗑️",
                width=35,
                height=35,
                command=lambda wid=word_id: self.delete_word(wid),
                fg_color="#EF4444",
                hover_color="#DC2626"
            ).pack(side="left", padx=2)

        except Exception as e:
            print(f"Помилка при створенні рядка пошуку: {e}")
            print(f"Дані слова: {word}")

    def display_words_table(self, words):
        if not words:
            no_data_label = ctk.CTkLabel(
                self.words_scroll_frame,
                text="Немає слів для відображення",
                font=ctk.CTkFont(size=16),
                text_color="#94A3B8"
            )
            no_data_label.pack(pady=50)
            return

        headers_frame = ctk.CTkFrame(self.words_scroll_frame, fg_color="#334155", height=50)
        headers_frame.pack(fill="x", pady=(0, 5))
        headers_frame.pack_propagate(False)

        headers = ["⭐", "Слово", "Переклад", "Рівень", "Категорія", "Статистика", "Дії"]
        widths = [50, 200, 200, 120, 150, 180, 120]

        for header, width in zip(headers, widths):
            label = ctk.CTkLabel(
                headers_frame,
                text=header,
                font=ctk.CTkFont(size=14, weight="bold"),
                width=width
            )
            label.pack(side="left", padx=10, pady=10)

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

    def create_word_row(self, word):
        row = ctk.CTkFrame(self.words_scroll_frame, fg_color="#1E293B", height=60)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        fav_btn = ctk.CTkButton(
            row,
            text="⭐" if word[9] else "☆",
            command=lambda wid=word[0]: self.toggle_favorite(wid),
            width=50,
            height=35,
            fg_color="transparent",
            hover_color="#334155"
        )
        fav_btn.pack(side="left", padx=10)

        word_label = ctk.CTkLabel(
            row,
            text=word[1],
            width=200,
            anchor="w",
            font=ctk.CTkFont(size=14)
        )
        word_label.pack(side="left", padx=10)

        translation_label = ctk.CTkLabel(
            row,
            text=word[2],
            width=200,
            anchor="w",
            text_color="#94A3B8",
            font=ctk.CTkFont(size=14)
        )
        translation_label.pack(side="left", padx=10)

        level_frame = ctk.CTkFrame(row, width=120, fg_color="transparent")
        level_frame.pack(side="left", padx=10)
        level_frame.pack_propagate(False)

        knowledge_level = word[4] if word[4] is not None else 0
        progress = min(knowledge_level / 10, 1.0)

        progress_bar = ctk.CTkProgressBar(level_frame, width=100, height=8)
        progress_bar.set(progress)
        progress_bar.pack(pady=5)

        level_text = f"{knowledge_level}/10"
        level_label = ctk.CTkLabel(
            level_frame,
            text=level_text,
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        )
        level_label.pack()

        category_text = word[5] if word[5] else "-"
        category_label = ctk.CTkLabel(
            row,
            text=category_text,
            width=150,
            anchor="w",
            text_color="#64748B",
            font=ctk.CTkFont(size=14)
        )
        category_label.pack(side="left", padx=10)

        correct_attempts = word[7] if word[7] is not None else 0
        wrong_attempts = word[8] if word[8] is not None else 0
        total_attempts = correct_attempts + wrong_attempts
        success_rate = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0

        stats_text = f"✓{correct_attempts} ✗{wrong_attempts} ({success_rate:.0f}%)"
        stats_label = ctk.CTkLabel(
            row,
            text=stats_text,
            width=180,
            anchor="w",
            text_color="#64748B",
            font=ctk.CTkFont(size=14)
        )
        stats_label.pack(side="left", padx=10)

        actions_frame = ctk.CTkFrame(row, fg_color="transparent", width=120)
        actions_frame.pack(side="right", padx=10)
        actions_frame.pack_propagate(False)

        edit_btn = ctk.CTkButton(
            actions_frame,
            text="✏️",
            width=35,
            height=35,
            command=lambda wid=word[0]: self.edit_word(wid),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        edit_btn.pack(side="left", padx=2)

        delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑️",
            width=35,
            height=35,
            command=lambda wid=word[0]: self.delete_word(wid),
            fg_color="#EF4444",
            hover_color="#DC2626"
        )
        delete_btn.pack(side="left", padx=2)

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