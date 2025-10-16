import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class StatisticsWindow:
    def __init__(self, parent_container, db_manager):
        self.parent_container = parent_container
        self.db = db_manager

        # Дефолтні дати
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=30)

        self.create_widgets()

    def create_widgets(self):
        # Верхня панель з контролями
        top_panel = ctk.CTkFrame(self.parent_container, fg_color="#1E293B", corner_radius=10)
        top_panel.pack(pady=15, padx=20, fill="x")

        title = ctk.CTkLabel(
            top_panel,
            text="📊 Статистика та Звіти",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(anchor="w", padx=20, pady=(15, 5))

        # Контроль дат
        controls_frame = ctk.CTkFrame(top_panel, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            controls_frame,
            text="📅 Період:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0, 10))

        # Кнопки для швидкого вибору періоду
        for period, days in [("7 днів", 7), ("14 днів", 14), ("30 днів", 30), ("90 днів", 90)]:
            ctk.CTkButton(
                controls_frame,
                text=period,
                command=lambda d=days: self.set_period(d),
                width=100,
                height=35,
                font=ctk.CTkFont(size=12),
                fg_color="#3B82F6",
                hover_color="#2563EB"
            ).pack(side="left", padx=5)

        # Основний контент з вкладками
        self.notebook = ctk.CTkFrame(self.parent_container, fg_color="transparent")
        self.notebook.pack(fill="both", expand=True, padx=20, pady=15)

        # Кнопки для перемикання вкладок
        tabs_frame = ctk.CTkFrame(self.notebook, fg_color="transparent")
        tabs_frame.pack(fill="x", pady=(0, 15))

        self.tab_buttons = {}
        tab_titles = [
            ("📈 Загальна статистика", "overview"),
            ("📚 По категоріям", "categories"),
            ("📖 Прогрес навчання", "progress"),
            ("💯 Рівні знань", "knowledge_levels")
        ]

        for title_text, tab_id in tab_titles:
            btn = ctk.CTkButton(
                tabs_frame,
                text=title_text,
                command=lambda tid=tab_id: self.show_tab(tid),
                width=150,
                height=40,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#334155",
                hover_color="#475569"
            )
            btn.pack(side="left", padx=5)
            self.tab_buttons[tab_id] = btn

        # Контейнер для вкладок
        self.tabs_container = ctk.CTkFrame(self.notebook, fg_color="transparent")
        self.tabs_container.pack(fill="both", expand=True)

        self.current_tab = None
        self.show_tab("overview")

    def set_period(self, days):
        """Встановити період для графіків"""
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=days)

        if self.current_tab:
            self.show_tab(self.current_tab)

    def clear_tabs_container(self):
        """Очистити контейнер вкладок"""
        for widget in self.tabs_container.winfo_children():
            widget.destroy()

    def show_tab(self, tab_id):
        """Показати вкладку"""
        self.current_tab = tab_id
        self.clear_tabs_container()

        # Оновити стан кнопок
        for bid, btn in self.tab_buttons.items():
            if bid == tab_id:
                btn.configure(fg_color="#3B82F6")
            else:
                btn.configure(fg_color="#334155")

        if tab_id == "overview":
            self.show_overview_tab()
        elif tab_id == "categories":
            self.show_categories_tab()
        elif tab_id == "progress":
            self.show_progress_tab()
        elif tab_id == "knowledge_levels":
            self.show_knowledge_levels_tab()

    def show_overview_tab(self):
        """Вкладка з загальною статистикою"""
        scroll_frame = ctk.CTkScrollableFrame(self.tabs_container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)

        # Статистичні картки
        stats = self.db.get_statistics()

        cards_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        cards_frame.pack(fill="x", pady=15)

        cards_data = [
            ("Всього слів", stats['total_words'], "#3B82F6"),
            ("Вивчено", stats['learned_words'], "#10B981"),
            ("Вивчається", stats['learning_words'], "#F59E0B"),
            ("Нові", stats['new_words'], "#8B5CF6"),
        ]

        for i, (title_text, value, color) in enumerate(cards_data):
            card = ctk.CTkFrame(cards_frame, fg_color=color, corner_radius=12, height=100)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")

            value_label = ctk.CTkLabel(
                card,
                text=str(value),
                font=ctk.CTkFont(size=40, weight="bold"),
                text_color="white"
            )
            value_label.pack(pady=(15, 5))

            title_label = ctk.CTkLabel(
                card,
                text=title_text,
                font=ctk.CTkFont(size=14),
                text_color="white"
            )
            title_label.pack(pady=(0, 10))

        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Графік вивчених слів
        self.create_daily_chart(scroll_frame)

    def show_categories_tab(self):
        """Вкладка зі статистикою по категоріям"""
        scroll_frame = ctk.CTkScrollableFrame(self.tabs_container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10)

        categories_stats = self.db.get_category_statistics()

        if not categories_stats:
            empty_label = ctk.CTkLabel(
                scroll_frame,
                text="Немає даних",
                font=ctk.CTkFont(size=16),
                text_color="#94A3B8"
            )
            empty_label.pack(pady=50)
            return

        # Таблиця категорій
        header_frame = ctk.CTkFrame(scroll_frame, fg_color="#334155", height=50)
        header_frame.pack(fill="x", pady=(0, 10))

        headers = ["Категорія", "Всього", "Вивчено", "Вивчається", "Нові", "Прогрес"]
        widths = [250, 100, 100, 120, 100, 200]

        for header, width in zip(headers, widths):
            ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=13, weight="bold"),
                width=width
            ).pack(side="left", padx=10, pady=10)

        for cat_data in categories_stats:
            cat_name, total, learned, learning, new = cat_data
            if total > 0:
                progress = (learned / total) * 100
            else:
                progress = 0

            row = ctk.CTkFrame(scroll_frame, fg_color="#1E293B", height=60)
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(row, text=cat_name or "-", width=250, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=str(total), width=100, anchor="center").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=str(learned), width=100, anchor="center", text_color="#10B981").pack(side="left",
                                                                                                        padx=10)
            ctk.CTkLabel(row, text=str(learning), width=120, anchor="center", text_color="#F59E0B").pack(side="left",
                                                                                                         padx=10)
            ctk.CTkLabel(row, text=str(new), width=100, anchor="center", text_color="#8B5CF6").pack(side="left",
                                                                                                    padx=10)

            progress_frame = ctk.CTkFrame(row, fg_color="transparent", width=200)
            progress_frame.pack(side="left", padx=10)
            progress_bar = ctk.CTkProgressBar(progress_frame, width=180, height=20)
            progress_bar.pack()
            progress_bar.set(progress / 100)

    def show_progress_tab(self):
        """Вкладка з прогресом навчання"""
        scroll_frame = ctk.CTkScrollableFrame(self.tabs_container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)

        self.create_progress_chart(scroll_frame)

    def show_knowledge_levels_tab(self):
        """Вкладка з розподілом по рівням знань"""
        scroll_frame = ctk.CTkScrollableFrame(self.tabs_container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)

        self.create_knowledge_distribution_chart(scroll_frame)

    def create_daily_chart(self, parent):
        """Створити графік щоденної статистики"""
        try:
            daily_stats = self.db.get_daily_statistics(days=30)

            if not daily_stats:
                ctk.CTkLabel(
                    parent,
                    text="🔄 Недостатньо даних для графіку. Почніть вивчати слова!",
                    font=ctk.CTkFont(size=14),
                    text_color="#94A3B8"
                ).pack(pady=50)
                return

            dates = []
            correct = []
            total = []

            for row in daily_stats:
                try:
                    date_obj = row[0]
                    # Конвертуємо дату у правильний формат
                    if isinstance(date_obj, str):
                        date_obj = datetime.strptime(date_obj, "%Y-%m-%d")

                    # Форматуємо дату для відображення
                    dates.append(date_obj.strftime("%d.%m"))

                    # Отримуємо значення
                    correct_count = row[1] if row[1] is not None else 0
                    total_count = row[2] if row[2] is not None else 0

                    correct.append(correct_count)
                    total.append(total_count)

                except Exception as e:
                    print(f"Помилка при обробці рядка {row}: {e}")
                    continue

            if not dates:
                ctk.CTkLabel(
                    parent,
                    text="🔄 Немає коректних даних для графіку",
                    font=ctk.CTkFont(size=14),
                    text_color="#94A3B8"
                ).pack(pady=50)
                return

            # Створюємо графік
            fig = Figure(figsize=(12, 6), facecolor="#0F172A", edgecolor="none")
            ax = fig.add_subplot(111, facecolor="#1E293B")

            x_pos = range(len(dates))

            # Переконуємося, що дані коректні
            incorrect = [total[i] - correct[i] for i in range(len(total))]

            # Малюємо стовпчики
            ax.bar([i - 0.2 for i in x_pos], correct, width=0.4,
                   label="Правильно", color="#10B981", alpha=0.8)
            ax.bar([i + 0.2 for i in x_pos], incorrect, width=0.4,
                   label="Неправильно", color="#EF4444", alpha=0.8)

            ax.set_xlabel("Дата", fontsize=12, color="#E2E8F0")
            ax.set_ylabel("Кількість відповідей", fontsize=12, color="#E2E8F0")
            ax.set_title("Щоденна статистика вивчання", fontsize=16,
                         weight="bold", color="#E2E8F0", pad=20)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(dates, rotation=45, ha="right", color="#94A3B8")
            ax.tick_params(colors="#94A3B8")
            ax.grid(axis="y", alpha=0.2, color="#475569")
            ax.legend(facecolor="#1E293B", edgecolor="#334155",
                      labelcolor="#E2E8F0", loc='upper left')

            # Стилізуємо рамку
            for spine in ax.spines.values():
                spine.set_color("#334155")

            # Додаємо сітку
            ax.grid(True, alpha=0.3, linestyle='--', color="#475569")

            # Упаковуємо canvas
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

        except Exception as e:
            print(f"Помилка при створенні графіку: {e}")
            import traceback
            traceback.print_exc()

            ctk.CTkLabel(
                parent,
                text=f"Помилка при завантаженні графіку: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color="#EF4444"
            ).pack(pady=30)

    def create_progress_chart(self, parent):
        """Створити графік прогресу навчання"""
        try:
            daily_stats = self.db.get_daily_statistics(days=30)

            if not daily_stats:
                ctk.CTkLabel(
                    parent,
                    text="Немає даних для графіку",
                    font=ctk.CTkFont(size=14),
                    text_color="#94A3B8"
                ).pack(pady=30)
                return

            dates = []
            correct_percentages = []

            for row in daily_stats:
                date_obj = row[0]
                if isinstance(date_obj, str):
                    try:
                        date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
                        dates.append(date_obj.strftime("%d.%m"))
                    except:
                        dates.append(str(date_obj)[:10])
                elif hasattr(date_obj, 'strftime'):
                    dates.append(date_obj.strftime("%d.%m"))
                else:
                    dates.append("N/A")

                percentage = (row[1] / row[2] * 100) if row[2] > 0 else 0
                correct_percentages.append(percentage)

            fig = Figure(figsize=(12, 6), facecolor="#0F172A", edgecolor="none")
            ax = fig.add_subplot(111, facecolor="#1E293B")

            ax.plot(range(len(dates)), correct_percentages, marker="o", linewidth=3,
                    markersize=8, color="#3B82F6", label="% Правильних відповідей")
            ax.fill_between(range(len(dates)), correct_percentages, alpha=0.2, color="#3B82F6")

            ax.set_xlabel("Дата", fontsize=12, color="#E2E8F0")
            ax.set_ylabel("Відсоток (%)", fontsize=12, color="#E2E8F0")
            ax.set_title("Прогрес навчання - Відсоток правильних відповідей", fontsize=16, weight="bold",
                         color="#E2E8F0", pad=20)
            ax.set_xticks(range(len(dates)))
            ax.set_xticklabels(dates, rotation=45, ha="right", color="#94A3B8")
            ax.set_ylim(0, 105)
            ax.tick_params(colors="#94A3B8")
            ax.grid(True, alpha=0.2, color="#475569")
            ax.legend(facecolor="#1E293B", edgecolor="#334155", labelcolor="#E2E8F0")

            for spine in ax.spines.values():
                spine.set_color("#334155")

            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        except Exception as e:
            print(f"Помилка при створенні графіку: {e}")
            ctk.CTkLabel(
                parent,
                text="Помилка при завантаженні графіку",
                font=ctk.CTkFont(size=14),
                text_color="#EF4444"
            ).pack(pady=30)

    def create_knowledge_distribution_chart(self, parent):
        """Створити графік розподілу слів по рівням знань"""
        try:
            knowledge_stats = self.db.get_knowledge_level_distribution()

            if not knowledge_stats:
                ctk.CTkLabel(
                    parent,
                    text="Немає даних для графіку",
                    font=ctk.CTkFont(size=14),
                    text_color="#94A3B8"
                ).pack(pady=30)
                return

            levels = [f"Рівень {row[0]}" for row in knowledge_stats]
            counts = [row[1] for row in knowledge_stats]

            colors = ["#8B5CF6", "#6366F1", "#3B82F6", "#10B981", "#F59E0B", "#EF4444"]
            colors = colors[:len(levels)]

            fig = Figure(figsize=(12, 6), facecolor="#0F172A", edgecolor="none")
            ax = fig.add_subplot(111, facecolor="#1E293B")

            wedges, texts, autotexts = ax.pie(counts, labels=levels, autopct="%1.1f%%",
                                              colors=colors, startangle=90,
                                              textprops={"color": "#E2E8F0", "fontsize": 12})

            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_weight("bold")
                autotext.set_fontsize(11)

            ax.set_title("Розподіл слів по рівням знань", fontsize=16, weight="bold",
                         color="#E2E8F0", pad=20)

            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        except Exception as e:
            print(f"Помилка при створенні графіку: {e}")
            ctk.CTkLabel(
                parent,
                text="Помилка при завантаженні графіку",
                font=ctk.CTkFont(size=14),
                text_color="#EF4444"
            ).pack(pady=30)