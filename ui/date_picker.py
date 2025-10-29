import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
import threading
import time
import random
import calendar
from dateutil.relativedelta import relativedelta

class DatePicker(ctk.CTkFrame):
    """Календар для вибору дати"""

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



    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(header, text="◀", width=25, command=self.prev_month,
                      fg_color="#3B82F6", hover_color="#2563EB").pack(side="left")

        self.month_label = ctk.CTkLabel(header, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.month_label.pack(side="left", expand=True)

        ctk.CTkButton(header, text="▶", width=25, command=self.next_month,
                      fg_color="#3B82F6", hover_color="#2563EB").pack(side="right")

        self.cal_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cal_frame.pack(fill="both", expand=True)
        self.update_calendar()

    def update_calendar(self):
        for widget in self.cal_frame.winfo_children():
            widget.destroy()

        self.month_label.configure(text=self.current_date.strftime("%B %Y"))

        days_of_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
        for i, day in enumerate(days_of_week):
            ctk.CTkLabel(self.cal_frame, text=day, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#94A3B8", width=25).grid(row=0, column=i, padx=2, pady=2)

        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        for row, week in enumerate(cal, start=1):
            for col, day in enumerate(week):
                if not day:
                    continue
                date_obj = datetime(self.current_date.year, self.current_date.month, day)
                is_today = date_obj.date() == datetime.now().date()
                fg_color = "#3B82F6" if is_today else "#334155"
                btn = ctk.CTkButton(self.cal_frame, text=str(day),
                                    width=25, height=25,
                                    font=ctk.CTkFont(size=11),
                                    fg_color=fg_color,
                                    hover_color="#475569",
                                    command=lambda d=date_obj: self.select_date(d))
                btn.grid(row=row, column=col, padx=2, pady=2)

    def select_date(self, date_obj):
        self.on_date_selected(date_obj)

    def prev_month(self):
        self.current_date -= relativedelta(months=1)
        self.build_calendar()

    def next_month(self):
        self.current_date += relativedelta(months=1)
        self.build_calendar()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Випадаючий календар")
        self.geometry("400x300")
        self.calendar_visible = False

        self.btn = ctk.CTkButton(self, text="📅 Обрати дату", command=self.toggle_calendar)
        self.btn.pack(pady=40)

        self.label = ctk.CTkLabel(self, text="Дата не вибрана")
        self.label.pack(pady=10)

        self.calendar = DatePicker(self, on_date_selected=self.set_date)

    def toggle_calendar(self):
        if self.calendar_visible:
            self.calendar.place_forget()
            self.calendar_visible = False
            self.btn.configure(text="📅 Обрати дату", fg_color="#475569")
        else:
            # позиціонуємо календар біля кнопки
            x = self.btn.winfo_x()
            y = self.btn.winfo_y() + self.btn.winfo_height() + 5
            self.calendar.place(x=x, y=y)
            self.calendar_visible = True
            self.btn.configure(text="📅 Приховати", fg_color="#3B82F6")

    def set_date(self, date_obj):
        self.label.configure(text=f"Вибрано: {date_obj.strftime('%d.%m.%Y')}")
        self.toggle_calendar()