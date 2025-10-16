import customtkinter as ctk
from tkinter import messagebox


class FlashcardWindow(ctk.CTkToplevel):
    def __init__(self, parent, db_manager, category_id=None):
        super().__init__(parent)
        self.db = db_manager
        self.category_id = category_id
        self.current_word_data = None
        self.is_flipped = False
        self.session_id = None
        self.words_studied = 0
        self.correct_count = 0
        self.title("Learn Easy - Картки")
        self.geometry("800x600")

        # Оновлюємо геометрію перед центруванням
        self.update_idletasks()

        # Центрування вікна
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 800
        window_height = 600

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Робимо вікно завжди поверх інших
        self.attributes('-topmost', True)
        self.lift()
        self.focus_force()

        # Після появи прибираємо topmost, щоб не заважало іншим вікнам
        self.after(100, lambda: self.attributes('-topmost', False))

        self.session_id = self.db.start_session('flashcard')
        self.create_widgets()
        self.load_next_word()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        top_panel = ctk.CTkFrame(self, fg_color="transparent")
        top_panel.pack(pady=20, padx=40, fill="x")
        self.stats_label = ctk.CTkLabel(
            top_panel,
            text="Вивчено: 0 | Правильно: 0",
            font=ctk.CTkFont(size=16)
        )
        self.stats_label.pack(side="left")
        close_btn = ctk.CTkButton(
            top_panel,
            text="✕ Завершити",
            command=self.on_closing,
            width=120,
            fg_color="#EF4444",
            hover_color="#DC2626"
        )
        close_btn.pack(side="right")
        self.card_frame = ctk.CTkFrame(
            self,
            corner_radius=20,
            fg_color="#1E293B",
            height=350
        )
        self.card_frame.pack(pady=40, padx=80, fill="both", expand=True)
        self.card_frame.pack_propagate(False)
        self.card_content = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.card_content.place(relx=0.5, rely=0.5, anchor="center")
        self.side_indicator = ctk.CTkLabel(
            self.card_content,
            text="Слово",
            font=ctk.CTkFont(size=14),
            text_color="#64748B"
        )
        self.side_indicator.pack(pady=(0, 20))
        self.main_text = ctk.CTkLabel(
            self.card_content,
            text="",
            font=ctk.CTkFont(size=42, weight="bold"),
            text_color="#F1F5F9"
        )
        self.main_text.pack(pady=20)
        self.transcription_label = ctk.CTkLabel(
            self.card_content,
            text="",
            font=ctk.CTkFont(size=16),
            text_color="#94A3B8"
        )
        self.transcription_label.pack(pady=10)
        self.example_label = ctk.CTkLabel(
            self.card_content,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#CBD5E1",
            wraplength=600
        )
        self.example_label.pack(pady=10)
        flip_btn = ctk.CTkButton(
            self.card_frame,
            text="🔄 Перевернути (Пробіл)",
            command=self.flip_card,
            width=200,
            height=45,
            font=ctk.CTkFont(size=16),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        flip_btn.pack(side="bottom", pady=30)
        bottom_panel = ctk.CTkFrame(self, fg_color="transparent")
        bottom_panel.pack(pady=20, padx=40, fill="x")
        buttons_frame = ctk.CTkFrame(bottom_panel, fg_color="transparent")
        buttons_frame.pack()
        self.wrong_btn = ctk.CTkButton(
            buttons_frame,
            text="✗ Не знаю (←)",
            command=lambda: self.rate_card(False),
            width=180,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            state="disabled"
        )
        self.wrong_btn.pack(side="left", padx=15)
        self.correct_btn = ctk.CTkButton(
            buttons_frame,
            text="✓ Знаю (→)",
            command=lambda: self.rate_card(True),
            width=180,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            state="disabled"
        )
        self.correct_btn.pack(side="left", padx=15)
        hint_label = ctk.CTkLabel(
            self,
            text="Клавіші: Пробіл - перевернути | ← Не знаю | → Знаю",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        )
        hint_label.pack(pady=(0, 10))
        self.bind("<space>", lambda e: self.flip_card())
        self.bind("<Left>", lambda e: self.rate_card(False) if self.is_flipped else None)
        self.bind("<Right>", lambda e: self.rate_card(True) if self.is_flipped else None)

    def load_next_word(self):
        word_data = self.db.get_next_word_for_learning('flashcard', self.category_id)
        if not word_data:
            self.show_session_summary()
            return
        self.current_word_data = word_data
        self.is_flipped = False
        self.side_indicator.configure(text="Слово")
        self.main_text.configure(text=word_data[1], text_color="#F1F5F9")
        if word_data[3]:
            self.transcription_label.configure(text=word_data[3])
            self.transcription_label.pack(pady=10)
        else:
            self.transcription_label.pack_forget()
        self.example_label.pack_forget()
        self.wrong_btn.configure(state="disabled")
        self.correct_btn.configure(state="disabled")

    def flip_card(self):
        if not self.current_word_data:
            return
        self.is_flipped = not self.is_flipped
        if self.is_flipped:
            self.side_indicator.configure(text="Переклад")
            self.main_text.configure(text=self.current_word_data[2], text_color="#3B82F6")
            if self.current_word_data[4]:
                example_text = f'"{self.current_word_data[4]}"'
                if self.current_word_data[5]:
                    example_text += f'\n{self.current_word_data[5]}'
                self.example_label.configure(text=example_text)
                self.example_label.pack(pady=10)
            self.wrong_btn.configure(state="normal")
            self.correct_btn.configure(state="normal")
        else:
            self.side_indicator.configure(text="Слово")
            self.main_text.configure(text=self.current_word_data[1], text_color="#F1F5F9")
            self.example_label.pack_forget()
            self.wrong_btn.configure(state="disabled")
            self.correct_btn.configure(state="disabled")

    def rate_card(self, knows):
        if not self.is_flipped or not self.current_word_data:
            return
        self.db.update_word_knowledge(self.current_word_data[0], knows, 'flashcard')
        self.words_studied += 1
        if knows:
            self.correct_count += 1
        self.stats_label.configure(text=f"Вивчено: {self.words_studied} | Правильно: {self.correct_count}")
        self.load_next_word()

    def show_session_summary(self):
        percentage = (self.correct_count / self.words_studied * 100) if self.words_studied > 0 else 0
        summary_window = ctk.CTkToplevel(self)
        summary_window.title("Підсумок сесії")
        summary_window.geometry("400x350")
        summary_window.transient(self)
        summary_window.grab_set()
        x = (self.winfo_screenwidth() // 2) - 200
        y = (self.winfo_screenheight() // 2) - 175
        summary_window.geometry(f"400x350+{x}+{y}")
        title = ctk.CTkLabel(
            summary_window,
            text="🎉 Чудова робота!",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=30)
        stats_frame = ctk.CTkFrame(summary_window)
        stats_frame.pack(pady=20, padx=40, fill="x")
        ctk.CTkLabel(
            stats_frame,
            text=f"Вивчено слів:",
            font=ctk.CTkFont(size=16)
        ).pack(pady=10)
        ctk.CTkLabel(
            stats_frame,
            text=str(self.words_studied),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#3B82F6"
        ).pack()
        ctk.CTkLabel(
            stats_frame,
            text=f"Правильно: {self.correct_count} ({percentage:.1f}%)",
            font=ctk.CTkFont(size=16)
        ).pack(pady=10)
        btn_frame = ctk.CTkFrame(summary_window, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(
            btn_frame,
            text="Ще раз",
            command=lambda: [summary_window.destroy(), self.restart_session()],
            width=150,
            height=40
        ).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frame,
            text="Закрити",
            command=lambda: [summary_window.destroy(), self.destroy()],
            width=150,
            height=40,
            fg_color="#64748B",
            hover_color="#475569"
        ).pack(side="left", padx=10)

    def restart_session(self):
        self.words_studied = 0
        self.correct_count = 0
        self.session_id = self.db.start_session('flashcard')
        self.stats_label.configure(text="Вивчено: 0 | Правильно: 0")
        self.load_next_word()

    def on_closing(self):
        if self.session_id:
            self.db.end_session(self.session_id)
        self.destroy()