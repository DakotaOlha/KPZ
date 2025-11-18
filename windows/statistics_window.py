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

        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=30)

        self.create_widgets()

    def create_widgets(self):
        top_panel = ctk.CTkFrame(self.parent_container, fg_color="#1E293B", corner_radius=10)
        top_panel.pack(pady=15, padx=20, fill="x")

        title = ctk.CTkLabel(
            top_panel,
            text="📊 Статистика та Звіти",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(anchor="w", padx=20, pady=(15, 5))

        controls_frame = ctk.CTkFrame(top_panel, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=15)

        left_controls = ctk.CTkFrame(controls_frame, fg_color="transparent")
        left_controls.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            left_controls,
            text="📅 Період:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0, 10))

        for period, days in [("7 днів", 7), ("14 днів", 14), ("30 днів", 30), ("90 днів", 90)]:
            ctk.CTkButton(
                left_controls,
                text=period,
                command=lambda d=days: self.set_period(d),
                width=80,
                height=32,
                font=ctk.CTkFont(size=11),
                fg_color="#3B82F6",
                hover_color="#2563EB"
            ).pack(side="left", padx=2)

        right_controls = ctk.CTkFrame(controls_frame, fg_color="transparent")
        right_controls.pack(side="right")

        self.calendar_btn = ctk.CTkButton(
            right_controls,
            text="📅 Обрати дати",
            command=self.toggle_calendar,
            width=120,
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color="#475569",
            hover_color="#334155"
        )
        self.calendar_btn.pack(side="top")

        self.calendar_container = ctk.CTkFrame(controls_frame, fg_color="transparent")
        self.calendar_visible = False

        self.notebook = ctk.CTkFrame(self.parent_container, fg_color="transparent")
        self.notebook.pack(fill="both", expand=True, padx=20, pady=15)

        tabs_frame = ctk.CTkFrame(self.notebook, fg_color="transparent")
        tabs_frame.pack(fill="x", pady=(0, 15))

        self.tab_buttons = {}
        tab_titles = [
            ("📈 Загальна", "overview"),
            ("📚 По категоріям", "categories"),
            ("📖 Прогрес", "progress"),
            ("💯 Рівні", "knowledge_levels")
        ]

        for title_text, tab_id in tab_titles:
            btn = ctk.CTkButton(
                tabs_frame,
                text=title_text,
                command=lambda tid=tab_id: self.show_tab(tid),
                width=120,
                height=35,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#334155",
                hover_color="#475569"
            )
            btn.pack(side="left", padx=3)
            self.tab_buttons[tab_id] = btn

        self.tabs_container = ctk.CTkFrame(self.notebook, fg_color="transparent")
        self.tabs_container.pack(fill="both", expand=True)

        self.current_tab = None
        self.show_tab("overview")

    def toggle_calendar(self):
        if self.calendar_visible:
            self.calendar_container.pack_forget()
            self.calendar_btn.configure(text="📅 Обрати дати", fg_color="#475569")
        else:
            self.show_calendar()
            self.calendar_container.pack(side="bottom", fill="x", pady=(10, 0))
            self.calendar_btn.configure(text="📅 Приховати", fg_color="#3B82F6")

        self.calendar_visible = not self.calendar_visible

    def show_calendar(self):
        for widget in self.calendar_container.winfo_children():
            widget.destroy()

        calendar_frame = ctk.CTkFrame(self.calendar_container, fg_color="#334155", corner_radius=8)
        calendar_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            calendar_frame,
            text="Оберіть період:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#E2E8F0"
        ).pack(pady=(10, 5))

        dates_frame = ctk.CTkFrame(calendar_frame, fg_color="transparent")
        dates_frame.pack(fill="x", padx=15, pady=10)

        start_frame = ctk.CTkFrame(dates_frame, fg_color="transparent")
        start_frame.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            start_frame,
            text="З:",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        ).pack(anchor="w")

        start_date_frame = ctk.CTkFrame(start_frame, fg_color="transparent")
        start_date_frame.pack(fill="x", pady=5)

        self.start_day = ctk.CTkComboBox(
            start_date_frame,
            values=[str(i).zfill(2) for i in range(1, 32)],
            width=60,
            height=30,
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11)
        )
        self.start_day.set(self.start_date.strftime("%d"))
        self.start_day.pack(side="left", padx=2)

        self.start_month = ctk.CTkComboBox(
            start_date_frame,
            values=[str(i).zfill(2) for i in range(1, 13)],
            width=60,
            height=30,
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11)
        )
        self.start_month.set(self.start_date.strftime("%m"))
        self.start_month.pack(side="left", padx=2)

        self.start_year = ctk.CTkComboBox(
            start_date_frame,
            values=[str(i) for i in range(2020, datetime.now().year + 1)],
            width=70,
            height=30,
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11)
        )
        self.start_year.set(self.start_date.strftime("%Y"))
        self.start_year.pack(side="left", padx=2)

        end_frame = ctk.CTkFrame(dates_frame, fg_color="transparent")
        end_frame.pack(side="left", padx=(20, 0))

        ctk.CTkLabel(
            end_frame,
            text="По:",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        ).pack(anchor="w")

        end_date_frame = ctk.CTkFrame(end_frame, fg_color="transparent")
        end_date_frame.pack(fill="x", pady=5)

        self.end_day = ctk.CTkComboBox(
            end_date_frame,
            values=[str(i).zfill(2) for i in range(1, 32)],
            width=60,
            height=30,
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11)
        )
        self.end_day.set(self.end_date.strftime("%d"))
        self.end_day.pack(side="left", padx=2)

        self.end_month = ctk.CTkComboBox(
            end_date_frame,
            values=[str(i).zfill(2) for i in range(1, 13)],
            width=60,
            height=30,
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11)
        )
        self.end_month.set(self.end_date.strftime("%m"))
        self.end_month.pack(side="left", padx=2)

        self.end_year = ctk.CTkComboBox(
            end_date_frame,
            values=[str(i) for i in range(2020, datetime.now().year + 1)],
            width=70,
            height=30,
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11)
        )
        self.end_year.set(self.end_date.strftime("%Y"))
        self.end_year.pack(side="left", padx=2)

        calendar_buttons_frame = ctk.CTkFrame(calendar_frame, fg_color="transparent")
        calendar_buttons_frame.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkButton(
            calendar_buttons_frame,
            text="Застосувати",
            command=self.apply_custom_dates,
            width=100,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="#10B981",
            hover_color="#059669"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            calendar_buttons_frame,
            text="Сьогодні",
            command=self.set_today,
            width=80,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            calendar_buttons_frame,
            text="Скасувати",
            command=self.toggle_calendar,
            width=80,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="#64748B",
            hover_color="#475569"
        ).pack(side="left", padx=5)

    def set_today(self):
        today = datetime.now()
        self.end_day.set(today.strftime("%d"))
        self.end_month.set(today.strftime("%m"))
        self.end_year.set(today.strftime("%Y"))

    def apply_custom_dates(self):
        try:
            start_date_str = f"{self.start_year.get()}-{self.start_month.get()}-{self.start_day.get()}"
            end_date_str = f"{self.end_year.get()}-{self.end_month.get()}-{self.end_day.get()}"

            self.start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            self.end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

            if self.start_date > self.end_date:
                messagebox.showerror("Помилка", "Початкова дата не може бути пізніше кінцевої")
                return

            self.toggle_calendar()

            if self.current_tab:
                self.show_tab(self.current_tab)

        except ValueError as e:
            messagebox.showerror("Помилка", "Невірний формат дати")

    def set_period(self, days):
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=days)

        if self.current_tab:
            self.show_tab(self.current_tab)

    def clear_tabs_container(self):
        for widget in self.tabs_container.winfo_children():
            widget.destroy()

    def show_tab(self, tab_id):
        self.current_tab = tab_id
        self.clear_tabs_container()

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
        scroll_frame = ctk.CTkScrollableFrame(self.tabs_container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)

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

        self.create_daily_chart(scroll_frame)

    def show_categories_tab(self):
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
        scroll_frame = ctk.CTkScrollableFrame(self.tabs_container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)

        self.create_progress_chart(scroll_frame)

    def show_knowledge_levels_tab(self):
        scroll_frame = ctk.CTkScrollableFrame(self.tabs_container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)

        self.create_knowledge_distribution_chart(scroll_frame)

    def create_daily_chart(self, parent):
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
                    if isinstance(date_obj, str):
                        date_obj = datetime.strptime(date_obj, "%Y-%m-%d")

                    dates.append(date_obj.strftime("%d.%m"))

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

            fig = Figure(figsize=(12, 6), facecolor="#0F172A", edgecolor="none")
            ax = fig.add_subplot(111, facecolor="#1E293B")

            x_pos = range(len(dates))

            incorrect = [total[i] - correct[i] for i in range(len(total))]

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

            for spine in ax.spines.values():
                spine.set_color("#334155")

            ax.grid(True, alpha=0.3, linestyle='--', color="#475569")

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