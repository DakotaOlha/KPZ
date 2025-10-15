import customtkinter as ctk
from tkinter import messagebox

class EditWordWindow(ctk.CTkToplevel):
    def __init__(self, parent, db_manager, word_id, on_save_callback):
        super().__init__(parent)
        self.db = db_manager
        self.word_id = word_id
        self.on_save_callback = on_save_callback
        self.title("Редагувати слово")
        self.geometry("600x700")
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"600x700+{x}+{y}")
        self.transient(parent)
        self.grab_set()
        word_data = self.db.get_word_by_id(word_id)
        if not word_data:
            messagebox.showerror("Помилка", "Слово не знайдено!")
            self.destroy()
            return
        self.create_widgets(word_data)

    def create_widgets(self, word_data):
        title = ctk.CTkLabel(
            self,
            text="Редагувати слово",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=20)
        form = ctk.CTkScrollableFrame(self)
        form.pack(fill="both", expand=True, padx=30, pady=10)
        _, word, translation, transcription, example, example_trans, category_id, difficulty = word_data
        self.word_entry = self.create_field(form, "Слово*:", word or "")
        self.translation_entry = self.create_field(form, "Переклад*:", translation or "")
        self.transcription_entry = self.create_field(form, "Транскрипція:", transcription or "")
        self.example_entry = self.create_field(form, "Приклад речення:", example or "")
        self.example_trans_entry = self.create_field(form, "Переклад прикладу:", example_trans or "")
        cat_frame = ctk.CTkFrame(form, fg_color="transparent")
        cat_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            cat_frame,
            text="Категорія*:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        categories = self.db.get_categories()
        cat_names = [cat[1] for cat in categories]
        current_cat = next((cat[1] for cat in categories if cat[0] == category_id), cat_names[0] if cat_names else "")
        self.category_var = ctk.StringVar(value=current_cat)
        self.categories_data = categories
        ctk.CTkOptionMenu(
            cat_frame,
            values=cat_names,
            variable=self.category_var,
            height=35
        ).pack(fill="x", pady=5)
        diff_frame = ctk.CTkFrame(form, fg_color="transparent")
        diff_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            diff_frame,
            text="Складність:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        self.difficulty_var = ctk.StringVar(value=str(difficulty or 1))
        ctk.CTkOptionMenu(
            diff_frame,
            values=["1", "2", "3", "4", "5"],
            variable=self.difficulty_var,
            height=35
        ).pack(fill="x", pady=5)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(
            btn_frame,
            text="💾 Зберегти",
            command=self.save_word,
            width=180,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669"
        ).pack(side="left", padx=10)
        ctk.CTkButton(
            btn_frame,
            text="✕ Скасувати",
            command=self.destroy,
            width=180,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#64748B",
            hover_color="#475569"
        ).pack(side="left", padx=10)

    def create_field(self, parent, label_text, initial_value):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            frame,
            text=label_text,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        entry = ctk.CTkEntry(frame, height=35)
        entry.insert(0, initial_value)
        entry.pack(fill="x", pady=5)
        return entry

    def save_word(self):
        word = self.word_entry.get().strip()
        translation = self.translation_entry.get().strip()
        if not word or not translation:
            messagebox.showwarning("Помилка", "Заповніть обов'язкові поля!")
            return
        cat_name = self.category_var.get()
        cat_id = next((cat[0] for cat in self.categories_data if cat[1] == cat_name), 1)
        transcription = self.transcription_entry.get().strip()
        example = self.example_entry.get().strip()
        example_trans = self.example_trans_entry.get().strip()
        difficulty = int(self.difficulty_var.get())
        try:
            self.db.update_word(
                self.word_id, word, translation, cat_id,
                transcription, example, example_trans, difficulty
            )
            messagebox.showinfo("Успіх", "Слово оновлено!")
            if self.on_save_callback:
                self.on_save_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти: {e}")