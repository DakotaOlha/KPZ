import pyodbc
from tkinter import messagebox
import random
from datetime import datetime
import time


class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = pyodbc.connect(
                'DRIVER={SQL Server};'
                'SERVER=localhost\\SQLEXPRESS;'
                'DATABASE=LearnEasy;'
                'Trusted_Connection=yes;'
            )
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося підключитися до БД:\n{e}")
            return False

    def get_all_words(self, search_term="", category="Всі", sort_by="word", include_archived=False, start_date=None,
                      end_date=None):
        query = """
                SELECT w.id, \
                       w.word, \
                       w.translation, \
                       w.transcription, \
                       w.knowledge_level,
                       c.name as category, \
                       w.times_shown, \
                       w.times_correct, \
                       w.times_wrong,
                       w.is_favorite, \
                       w.difficulty_level, \
                       w.example_sentence, \
                       w.example_translation,
                       w.category_id
                FROM Words w
                         LEFT JOIN Categories c ON w.category_id = c.id
                WHERE 1 = 1 \
                """
        params = []
        if not include_archived:
            query += " AND w.is_archived = 0"
        if search_term:
            query += " AND (w.word LIKE ? OR w.translation LIKE ?)"
            params.extend([f'%{search_term}%', f'%{search_term}%'])
        if category != "Всі":
            query += " AND c.name = ?"
            params.append(category)

        # Фільтрація за датами додання слова
        if start_date:
            query += " AND CAST(w.created_at AS DATE) >= ?"
            # Конвертуємо datetime.date у рядок у форматі YYYY-MM-DD
            if hasattr(start_date, 'strftime'):
                params.append(start_date.strftime("%Y-%m-%d"))
            else:
                params.append(str(start_date))
        if end_date:
            query += " AND CAST(w.created_at AS DATE) <= ?"
            # Конвертуємо datetime.date у рядок у форматі YYYY-MM-DD
            if hasattr(end_date, 'strftime'):
                params.append(end_date.strftime("%Y-%m-%d"))
            else:
                params.append(str(end_date))

        sort_mapping = {
            "word": "w.word",
            "translation": "w.translation",
            "knowledge_level": "w.knowledge_level DESC",
            "category": "c.name",
            "difficulty": "w.difficulty_level DESC"
        }
        query += f" ORDER BY {sort_mapping.get(sort_by, 'w.word')}"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_word_by_id(self, word_id):
        query = """
                SELECT w.id, \
                       w.word, \
                       w.translation, \
                       w.transcription, \
                       w.example_sentence,
                       w.example_translation, \
                       w.category_id, \
                       w.difficulty_level
                FROM Words w
                WHERE w.id = ? \
                """
        self.cursor.execute(query, (word_id,))
        return self.cursor.fetchone()

    def update_word(self, word_id, word, translation, category_id, transcription="", example="", example_trans="",
                    difficulty=1):
        query = """
                UPDATE Words
                SET word                = ?, \
                    translation         = ?, \
                    transcription       = ?, \
                    example_sentence    = ?,
                    example_translation = ?, \
                    category_id         = ?, \
                    difficulty_level    = ?
                WHERE id = ? \
                """
        self.cursor.execute(query, (word, translation, transcription, example, example_trans, category_id, difficulty,
                                    word_id))
        self.conn.commit()

    def add_word(self, word, translation, category_id, transcription="", example="", example_trans="", difficulty=1):
        query = """
                INSERT INTO Words (word, translation, transcription, example_sentence,
                                   example_translation, category_id, difficulty_level)
                VALUES (?, ?, ?, ?, ?, ?, ?) \
                """
        self.cursor.execute(query, (word, translation, transcription, example, example_trans, category_id, difficulty))
        self.conn.commit()

    def update_word_knowledge(self, word_id, knows, mode_name='popup'):
        try:
            self.cursor.execute("EXEC sp_RecordInteraction ?, ?, ?", (word_id, mode_name, knows))
            self.conn.commit()
        except:
            if knows:
                query = """
                        UPDATE Words
                        SET knowledge_level = knowledge_level + 1,
                            times_shown     = times_shown + 1,
                            times_correct   = times_correct + 1,
                            last_shown      = GETDATE()
                        WHERE id = ? \
                        """
            else:
                query = """
                        UPDATE Words
                        SET knowledge_level = CASE WHEN knowledge_level > 0 THEN knowledge_level - 1 ELSE 0 END,
                            times_shown     = times_shown + 1,
                            times_wrong     = times_wrong + 1,
                            last_shown      = GETDATE()
                        WHERE id = ? \
                        """
            self.cursor.execute(query, (word_id,))
            self.conn.commit()

    def get_categories(self):
        self.cursor.execute("SELECT id, name, color_hex FROM Categories WHERE is_active = 1")
        return self.cursor.fetchall()

    def get_next_word_for_learning(self, mode='flashcard', category_id=None):

        if random.random() < 0.75:
            query = """
                    SELECT TOP 1 w.id, w.word, \
                           w.translation, \
                           w.transcription,
                           w.example_sentence, \
                           w.example_translation, \
                           w.knowledge_level
                    FROM Words w
                    WHERE w.is_archived = 0 \
                      AND w.knowledge_level = 0 \
                    """
            if category_id:
                query += " AND w.category_id = ?"
                self.cursor.execute(query + " ORDER BY NEWID()", (category_id,))
            else:
                self.cursor.execute(query + " ORDER BY NEWID()")
            result = self.cursor.fetchone()
            if result:
                return result

        if random.random() < 0.85:
            query = """
                    SELECT TOP 1 w.id, w.word, \
                           w.translation, \
                           w.transcription,
                           w.example_sentence, \
                           w.example_translation, \
                           w.knowledge_level,
                           w.times_wrong, \
                           w.times_correct
                    FROM Words w
                    WHERE w.is_archived = 0 \
                      AND w.knowledge_level BETWEEN 1 AND 4
                      AND (w.last_shown IS NULL OR w.last_shown < DATEADD(minute, -30, GETDATE())) \
                    """
            if category_id:
                query += " AND w.category_id = ?"
                self.cursor.execute(query + " ORDER BY w.times_wrong DESC, NEWID()", (category_id,))
            else:
                self.cursor.execute(query + " ORDER BY w.times_wrong DESC, NEWID()")
            result = self.cursor.fetchone()
            if result:
                return result

        query = """
                SELECT TOP 1 w.id, w.word, \
                       w.translation, \
                       w.transcription,
                       w.example_sentence, \
                       w.example_translation, \
                       w.knowledge_level
                FROM Words w
                WHERE w.is_archived = 0 \
                  AND w.knowledge_level >= 5
                  AND (w.last_shown IS NULL OR w.last_shown < DATEADD(day, -1, GETDATE())) \
                """
        if category_id:
            query += " AND w.category_id = ?"
            self.cursor.execute(query + " ORDER BY w.last_shown ASC, NEWID()", (category_id,))
        else:
            self.cursor.execute(query + " ORDER BY w.last_shown ASC, NEWID()")
        result = self.cursor.fetchone()
        if result:
            return result

        query = """
                SELECT TOP 1 w.id, w.word, \
                       w.translation, \
                       w.transcription,
                       w.example_sentence, \
                       w.example_translation, \
                       w.knowledge_level
                FROM Words w
                WHERE w.is_archived = 0 \
                """
        if category_id:
            query += " AND w.category_id = ?"
            self.cursor.execute(query + " ORDER BY NEWID()", (category_id,))
        else:
            self.cursor.execute(query + " ORDER BY NEWID()")
        return self.cursor.fetchone()

    def get_statistics(self):
        try:
            self.cursor.execute("SELECT * FROM vw_Dashboard")
            row = self.cursor.fetchone()
            if row:
                return {
                    'total_words': row[0],
                    'learned_words': row[1],
                    'learning_words': row[2],
                    'new_words': row[3],
                    'favorite_words': row[4],
                    'progress_percentage': row[10] if len(row) > 10 else 0
                }
        except:
            pass
        stats = {}
        self.cursor.execute("SELECT COUNT(*) FROM Words WHERE is_archived = 0")
        stats['total_words'] = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM Words WHERE knowledge_level >= 5 AND is_archived = 0")
        stats['learned_words'] = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM Words WHERE knowledge_level BETWEEN 1 AND 4 AND is_archived = 0")
        stats['learning_words'] = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM Words WHERE knowledge_level = 0 AND is_archived = 0")
        stats['new_words'] = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM Words WHERE is_favorite = 1")
        stats['favorite_words'] = self.cursor.fetchone()[0]
        if stats['total_words'] > 0:
            stats['progress_percentage'] = (stats['learned_words'] / stats['total_words']) * 100
        else:
            stats['progress_percentage'] = 0
        return stats

    def toggle_favorite(self, word_id):
        query = "UPDATE Words SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END WHERE id = ?"
        self.cursor.execute(query, (word_id,))
        self.conn.commit()

    def delete_word(self, word_id):
        self.cursor.execute("DELETE FROM Words WHERE id = ?", (word_id,))
        self.conn.commit()

    def archive_word(self, word_id):
        query = "UPDATE Words SET is_archived = 1 WHERE id = ?"
        self.cursor.execute(query, (word_id,))
        self.conn.commit()

    def start_session(self, mode_name):
        try:
            self.cursor.execute("EXEC sp_StartSession ?", (mode_name,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except:
            return None

    def end_session(self, session_id):
        try:
            self.cursor.execute("EXEC sp_EndSession ?", (session_id,))
            self.conn.commit()
        except:
            pass

    def close(self):
        if self.conn:
            self.conn.close()

    def get_words_statistics(self, start_date=None, end_date=None):
        query = """
                SELECT CAST(w.last_shown AS DATE) as study_date, \
                       COUNT(*)                   as words_count
                FROM Words w
                WHERE w.is_archived = 0 \
                """
        params = []

        if start_date:
            query += " AND CAST(w.last_shown AS DATE) >= ?"
            if hasattr(start_date, 'strftime'):
                params.append(start_date.strftime("%Y-%m-%d"))
            else:
                params.append(str(start_date))
        if end_date:
            query += " AND CAST(w.last_shown AS DATE) <= ?"
            if hasattr(end_date, 'strftime'):
                params.append(end_date.strftime("%Y-%m-%d"))
            else:
                params.append(str(end_date))

        query += " GROUP BY CAST(w.last_shown AS DATE) ORDER BY study_date"

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_words_by_difficulty(self):
        try:
            query = """
                    SELECT w.difficulty_level, \
                           COUNT(*) as count,
                    SUM(CASE WHEN w.knowledge_level >= 5 THEN 1 ELSE 0 END) as learned
                    FROM Words w
                    WHERE w.is_archived = 0
                    GROUP BY w.difficulty_level
                    ORDER BY w.difficulty_level \
                    """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Помилка в get_words_by_difficulty: {e}")
            return []

    def get_knowledge_level_distribution(self):
        try:
            query = """
                    SELECT w.knowledge_level, \
                           COUNT(*) as count
                    FROM Words w
                    WHERE w.is_archived = 0
                    GROUP BY w.knowledge_level
                    ORDER BY w.knowledge_level \
                    """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Помилка в get_knowledge_level_distribution: {e}")
            return []

    def get_category_statistics(self):
        try:
            query = """
                SELECT 
                    ISNULL(c.name, 'Без категорії') as name,
                    COUNT(w.id) as total,
                    SUM(CASE WHEN w.knowledge_level >= 5 THEN 1 ELSE 0 END) as learned,
                    SUM(CASE WHEN w.knowledge_level BETWEEN 1 AND 4 THEN 1 ELSE 0 END) as learning,
                    SUM(CASE WHEN w.knowledge_level = 0 THEN 1 ELSE 0 END) as new_words
                FROM Words w
                LEFT JOIN Categories c ON w.category_id = c.id
                WHERE w.is_archived = 0
                GROUP BY c.name, c.id
                ORDER BY c.name
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Помилка в get_category_statistics: {e}")
            return []

    def get_daily_statistics(self, days=30):
        """Отримати щоденну статистику з кращою обробкою помилок"""
        try:
            # Перевіряємо, чи існує таблиця Interactions
            self.cursor.execute("""
                                SELECT COUNT(*)
                                FROM INFORMATION_SCHEMA.TABLES
                                WHERE TABLE_NAME = 'Interactions'
                                """)
            has_interactions = self.cursor.fetchone()[0] > 0

            if has_interactions:
                query = """
                        SELECT CAST(i.interaction_date AS DATE)                  as study_date,
                               SUM(CASE WHEN i.is_correct = 1 THEN 1 ELSE 0 END) as correct_answers,
                               COUNT(*)                                          as total_interactions
                        FROM Interactions i
                        WHERE i.interaction_date >= DATEADD(day, -?, GETDATE())
                        GROUP BY CAST(i.interaction_date AS DATE)
                        ORDER BY study_date \
                        """
                self.cursor.execute(query, (days,))
            else:
                # Альтернативний запит для статистики з таблиці Words
                query = """
                        SELECT CAST(COALESCE(w.last_shown, w.created_at) AS DATE)                 as study_date, \
                               SUM(CASE WHEN w.times_correct > 0 THEN w.times_correct ELSE 0 END) as correct_answers, \
                               SUM(COALESCE(w.times_correct, 0) + COALESCE(w.times_wrong, 0))     as total_interactions
                        FROM Words w
                        WHERE w.is_archived = 0
                          AND (w.last_shown IS NOT NULL OR w.created_at IS NOT NULL)
                          AND (COALESCE(w.last_shown, w.created_at) >= DATEADD(day, -?, GETDATE())
                            OR w.times_correct > 0 OR w.times_wrong > 0)
                        GROUP BY CAST(COALESCE(w.last_shown, w.created_at) AS DATE)
                        ORDER BY study_date \
                        """
                self.cursor.execute(query, (days,))

            results = self.cursor.fetchall()

            # Фільтруємо None значення і переконуємося, що дати коректні
            filtered_results = []
            for row in results:
                if row[0] is not None and row[1] is not None and row[2] is not None:
                    filtered_results.append(row)

            return filtered_results if filtered_results else []

        except Exception as e:
            print(f"Помилка в get_daily_statistics: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_words_added_by_date(self, start_date=None, end_date=None):
        query = """
                SELECT CAST(w.created_at AS DATE) as added_date, \
                       COUNT(*)                   as words_count
                FROM Words w
                WHERE w.is_archived = 0 \
                """
        params = []

        if start_date:
            query += " AND CAST(w.created_at AS DATE) >= ?"
            if hasattr(start_date, 'strftime'):
                params.append(start_date.strftime("%Y-%m-%d"))
            else:
                params.append(str(start_date))
        if end_date:
            query += " AND CAST(w.created_at AS DATE) <= ?"
            if hasattr(end_date, 'strftime'):
                params.append(end_date.strftime("%Y-%m-%d"))
            else:
                params.append(str(end_date))

        query += " GROUP BY CAST(w.created_at AS DATE) ORDER BY added_date"

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_learning_progress(self, days=30):
        query = """
                SELECT CAST(DATEADD(day, -ROW_NUMBER() OVER (ORDER BY GETDATE()), CAST(GETDATE() AS DATE)) AS DATE) as date,
                (SELECT COUNT(*) FROM Words WHERE knowledge_level >= 5 AND is_archived = 0
                 AND CAST(last_shown AS DATE) <= CAST(DATEADD(day, -ROW_NUMBER() OVER (ORDER BY GETDATE()), CAST(GETDATE() AS DATE)) AS DATE)) as learned_count
                FROM (SELECT TOP ? 1 as n FROM (SELECT 1 UNION ALL SELECT 1) a CROSS JOIN (SELECT 1 UNION ALL SELECT 1) b) numbers
                ORDER BY date \
                """
        self.cursor.execute(query, (days,))
        return self.cursor.fetchall()