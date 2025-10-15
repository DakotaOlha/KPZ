import customtkinter as ctk

class PopupWindow(ctk.CTkToplevel):
    def __init__(self, parent, word_data, db_manager):
        super().__init__(parent)
        self.word_id = word_data[0]
        self.word = word_data[1]
        self.translation = word_data[2]
        self.db_manager = db_manager
        self.title("Learn Easy")
        self.geometry("400x280")
        self.resizable(False, False)
        screen_width = self.winfo_screenwidth()
        x = screen_width - 420
        y = 20
        self.geometry(f"400x280+{x}+{y}")
        self.attributes('-topmost', True)
        self.create_widgets()
        self.after(15000, self.destroy)

    def create_widgets(self):
        title_label = ctk.CTkLabel(
            self,
            text="Нове слово! 📚",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        word_label = ctk.CTkLabel(
            self,
            text=self.word,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#3B82F6"
        )
        word_label.pack(pady=10)
        translation_label = ctk.CTkLabel(
            self,
            text=self.translation,
            font=ctk.CTkFont(size=22),
            text_color="#94A3B8"
        )
        translation_label.pack(pady=10)
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=25)
        know_btn = ctk.CTkButton(
            button_frame,
            text="✓ Знаю",
            command=lambda: self.on_answer(True),
            fg_color="#10B981",
            hover_color="#059669",
            width=140,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        know_btn.pack(side="left", padx=10)
        dont_know_btn = ctk.CTkButton(
            button_frame,
            text="✗ Не знаю",
            command=lambda: self.on_answer(False),
            fg_color="#EF4444",
            hover_color="#DC2626",
            width=140,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        dont_know_btn.pack(side="left", padx=10)

    def on_answer(self, knows):
        self.db_manager.update_word_knowledge(self.word_id, knows, 'popup')
        self.destroy()
