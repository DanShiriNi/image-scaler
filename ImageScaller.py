import os
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
import sys

def resource_path(relative_path):
    """Возвращает правильный путь к файлу (работает и при разработке, и в собранном .exe)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

icon_path = resource_path("icon.ico")

class DragDropScalerApp(TkinterDnD.DnDWrapper, ctk.CTk):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.iconbitmap(icon_path)

        self.title("Image Scaler with Drag-and-Drop")
        self.geometry("800x600")
        self.minsize(700, 500)

        self.center_window()

        self.current_image_path = None
        self.original_image = None
        self.scaled_image = None
        self.scale_factor = 1.0

        self._updating = False  # флаг для предотвращения рекурсии

        # Вкладки
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.main_tab = self.tabview.add("Главная")
        self.setup_main_tab()

        self.preview_tab = self.tabview.add("Превью")
        self.setup_preview_tab()

    def center_window(self, width=None, height=None):
        if width is None:
            width = 800
        if height is None:
            height = 600
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def center_toplevel(self, toplevel):
        toplevel.update_idletasks()
        w = toplevel.winfo_width()
        h = toplevel.winfo_height()
        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        x = parent_x + (parent_w - w) // 2
        y = parent_y + (parent_h - h) // 2
        toplevel.geometry(f"+{x}+{y}")

    def setup_main_tab(self):
        main_flex_frame = ctk.CTkFrame(self.main_tab)
        main_flex_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Левая область – Drag & Drop
        self.file_frame = ctk.CTkFrame(main_flex_frame, corner_radius=15)
        self.file_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=0)

        self.drop_label = ctk.CTkLabel(
            self.file_frame,
            text="Перетащите файл сюда\nили нажмите для выбора",
            font=ctk.CTkFont(size=14),
            corner_radius=15,
            fg_color=("gray75", "gray25"),
            justify="center"
        )
        self.drop_label.pack(fill="both", expand=True, padx=10, pady=10)
        self.drop_label.bind("<Button-1>", lambda e: self.open_file_dialog())
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.on_drop)

        # Правая область – настройки
        self.settings_frame = ctk.CTkFrame(main_flex_frame, corner_radius=15)
        self.settings_frame.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=0)

        # 1) Режим (увеличение/уменьшение)
        self.mode_frame = ctk.CTkFrame(self.settings_frame)
        self.mode_frame.pack(fill="x", padx=20, pady=(20, 10))

        self.mode_var = ctk.StringVar(value="up")
        self.up_radio = ctk.CTkRadioButton(
            self.mode_frame, text="Увеличение", variable=self.mode_var,
            value="up", command=self.on_mode_changed
        )
        self.up_radio.pack(side="left", padx=10, expand=True)

        self.down_radio = ctk.CTkRadioButton(
            self.mode_frame, text="Уменьшение", variable=self.mode_var,
            value="down", command=self.on_mode_changed
        )
        self.down_radio.pack(side="left", padx=10, expand=True)

        # 2) Коэффициент масштабирования
        self.scale_frame = ctk.CTkFrame(self.settings_frame)
        self.scale_frame.pack(fill="x", padx=20, pady=10)

        self.scale_label = ctk.CTkLabel(self.scale_frame, text="Во сколько раз:", font=ctk.CTkFont(size=12))
        self.scale_label.pack(side="left", padx=5)

        self.scale_entry = ctk.CTkEntry(self.scale_frame, width=120, font=ctk.CTkFont(size=12))
        self.scale_entry.insert(0, "2")
        self.scale_entry.pack(side="left", padx=5)
        # Автоматическое обновление при любом изменении текста (KeyRelease)
        self.scale_entry.bind("<KeyRelease>", self.on_scale_changed)
        self.scale_entry.bind("<FocusOut>", self.on_scale_changed)

        # 3) Оригинальный размер
        self.original_size_label = ctk.CTkLabel(
            self.settings_frame, text="Оригинальный размер: ---", font=ctk.CTkFont(size=12)
        )
        self.original_size_label.pack(anchor="w", padx=25, pady=(0, 10))

        # 4) Поля для целевой ширины и высоты
        self.dimensions_frame = ctk.CTkFrame(self.settings_frame)
        self.dimensions_frame.pack(fill="x", padx=20, pady=10)

        self.width_label = ctk.CTkLabel(self.dimensions_frame, text="Ширина:", font=ctk.CTkFont(size=12))
        self.width_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.width_entry = ctk.CTkEntry(self.dimensions_frame, width=100, font=ctk.CTkFont(size=12))
        self.width_entry.grid(row=0, column=1, padx=5, pady=5)
        self.width_entry.bind("<KeyRelease>", self.on_width_changed)
        self.width_entry.bind("<FocusOut>", self.on_width_changed)

        self.height_label = ctk.CTkLabel(self.dimensions_frame, text="Высота:", font=ctk.CTkFont(size=12))
        self.height_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.height_entry = ctk.CTkEntry(self.dimensions_frame, width=100, font=ctk.CTkFont(size=12))
        self.height_entry.grid(row=1, column=1, padx=5, pady=5)
        self.height_entry.bind("<KeyRelease>", self.on_height_changed)
        self.height_entry.bind("<FocusOut>", self.on_height_changed)

        # 5) Метка для предупреждения о нецелых размерах (при уменьшении)
        self.warning_label = ctk.CTkLabel(
            self.settings_frame,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="red"
        )
        self.warning_label.pack(anchor="w", padx=25, pady=(0, 10))

        # 6) Кнопка масштабирования
        self.scale_btn = ctk.CTkButton(
            self.settings_frame,
            text="МАСШТАБИРОВАТЬ!",
            command=self.scale_image,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f6aa5",
            hover_color="#144870",
            height=45
        )
        self.scale_btn.pack(pady=(20, 20), padx=20, fill="x")

    def setup_preview_tab(self):
        self.canvas_frame = ctk.CTkFrame(self.preview_tab)
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.h_scroll = ctk.CTkScrollbar(self.canvas_frame, orientation="horizontal")
        self.v_scroll = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical")
        self.canvas = tk.Canvas(
            self.canvas_frame,
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set,
            bg="gray",
            highlightthickness=0
        )
        self.h_scroll.configure(command=self.canvas.xview)
        self.v_scroll.configure(command=self.canvas.yview)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        self.slider_frame = ctk.CTkFrame(self.preview_tab)
        self.slider_frame.pack(fill="x", padx=10, pady=10)

        self.zoom_label_text = ctk.CTkLabel(self.slider_frame, text="Масштаб: 1.00x", font=ctk.CTkFont(size=12))
        self.zoom_label_text.pack(side="left", padx=5)

        self.zoom_slider = ctk.CTkSlider(self.slider_frame, from_=0.1, to=16.0, command=self.update_preview_zoom)
        self.zoom_slider.set(1.0)
        self.zoom_slider.pack(side="left", fill="x", expand=True, padx=5)

        self.button_frame = ctk.CTkFrame(self.preview_tab)
        self.button_frame.pack(fill="x", padx=10, pady=10)

        self.cancel_btn = ctk.CTkButton(
            self.button_frame, text="Отмена", command=self.cancel_preview,
            fg_color="#b56576", hover_color="#8a4b5c"
        )
        self.cancel_btn.pack(side="left", padx=20, expand=True)

        self.save_btn = ctk.CTkButton(
            self.button_frame, text="Сохранить", command=self.save_options,
            fg_color="#2e8b57", hover_color="#1f6a43"
        )
        self.save_btn.pack(side="right", padx=20, expand=True)

        self.photo_image = None
        self.preview_img = None

    # ---------- Drag & Drop ----------
    def update_drop_label(self):
        if self.current_image_path:
            filename = os.path.basename(self.current_image_path)
            self.drop_label.configure(
                text=f"✓ {filename}\n(нажмите или перетащите,\nчтобы заменить)",
                fg_color=("gray70", "gray20")
            )
        else:
            self.drop_label.configure(
                text="Перетащите файл сюда\nили нажмите для выбора",
                fg_color=("gray75", "gray25")
            )

    def on_drop(self, event):
        file_path = event.data.strip('{}')
        candidates = []
        if file_path.startswith('"') and '"' in file_path[1:]:
            end_quote = file_path.find('"', 1)
            if end_quote != -1:
                candidates.append(file_path[1:end_quote])
                remaining = file_path[end_quote+1:].strip()
                if remaining and remaining.startswith('"'):
                    end_quote2 = remaining.find('"', 1)
                    if end_quote2 != -1:
                        candidates.append(remaining[1:end_quote2])
        else:
            parts = file_path.split()
            for part in parts:
                part = part.strip('"\'')
                candidates.append(part)

        found_file = None
        for candidate in candidates:
            if os.path.exists(candidate):
                found_file = candidate
                break
            abs_path = os.path.abspath(candidate)
            if os.path.exists(abs_path):
                found_file = abs_path
                break

        if not found_file and len(candidates) > 0:
            test_path = ' '.join(candidates)
            if os.path.exists(test_path):
                found_file = test_path

        if found_file and os.path.exists(found_file):
            self.load_image(found_file)
        else:
            messagebox.showerror("Ошибка", f"Не удалось найти файл. Исходный путь: {file_path}")

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff")]
        )
        if file_path:
            self.load_image(file_path)

    def load_image(self, file_path):
        try:
            self.original_image = Image.open(file_path)
            self.current_image_path = file_path
            self.update_drop_label()
            self.original_size_label.configure(
                text=f"Оригинальный размер: {self.original_image.width} x {self.original_image.height}"
            )
            # Сброс значений по умолчанию
            self.scale_entry.delete(0, tk.END)
            self.scale_entry.insert(0, "2")
            self.mode_var.set("up")
            self.update_dimensions_from_scale()  # обновит поля width/height и warning
            messagebox.showinfo("Успех", f"Изображение загружено:\n{os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение:\n{str(e)}")

    # ---------- Синхронизация и предупреждения ----------
    def update_warning(self):
        """Показывает предупреждение, если при уменьшении размеры получаются нецелыми"""
        if not self.original_image:
            self.warning_label.configure(text="")
            return
        try:
            factor = float(self.scale_entry.get())
            if factor <= 0:
                self.warning_label.configure(text="")
                return
            mode = self.mode_var.get()
            if mode == "down":
                # Проверяем, являются ли целевые размеры целыми при данном коэффициенте
                target_width = self.original_image.width / factor
                target_height = self.original_image.height / factor
                if not target_width.is_integer() or not target_height.is_integer():
                    self.warning_label.configure(
                        text="ВНИМАНИЕ: Нецелое деление!\nИтоговое изображение будет искажено.\nРекомендуется изменить коэффициент или размеры."
                    )
                else:
                    self.warning_label.configure(text="")
            else:
                self.warning_label.configure(text="")
        except Exception:
            self.warning_label.configure(text="")

    def update_dimensions_from_scale(self):
        """Обновляет поля ширины и высоты на основе оригинала, коэффициента и режима"""
        if self._updating or not self.original_image:
            return
        self._updating = True
        try:
            factor = float(self.scale_entry.get())
            if factor <= 0:
                raise ValueError
            mode = self.mode_var.get()
            if mode == "up":
                new_width = round(self.original_image.width * factor)
                new_height = round(self.original_image.height * factor)
            else:  # down
                new_width = round(self.original_image.width / factor)
                new_height = round(self.original_image.height / factor)

            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(new_width))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(new_height))

            # Обновить предупреждение
            self.update_warning()
        except Exception:
            self.width_entry.delete(0, tk.END)
            self.height_entry.delete(0, tk.END)
        finally:
            self._updating = False

    def on_mode_changed(self):
        if self._updating or not self.original_image:
            return
        # При переключении режима пересчитываем размеры по текущему коэффициенту
        self.update_dimensions_from_scale()

    def on_scale_changed(self, event=None):
        """Вызывается при изменении коэффициента (KeyRelease или FocusOut)"""
        if self._updating or not self.original_image:
            return
        try:
            factor = float(self.scale_entry.get())
            if factor <= 0:
                raise ValueError
            # Автоматически корректируем режим в зависимости от коэффициента
            if factor > 1.0:
                self.mode_var.set("up")
            elif factor < 1.0:
                self.mode_var.set("down")
            # Пересчитываем размеры
            self.update_dimensions_from_scale()
        except ValueError:
            # Если ввели не число – ничего не делаем, но можно показать предупреждение
            self.warning_label.configure(text="Некорректный коэффициент\n(должно быть положительное число)")

    def sync_scale_from_dimensions(self, trigger_by_width=True):
        """Пересчитывает коэффициент и режим на основе введённой ширины (или высоты)"""
        if self._updating or not self.original_image:
            return
        self._updating = True
        try:
            if trigger_by_width:
                width_str = self.width_entry.get().strip()
                if not width_str:
                    return
                new_width = int(float(width_str))
                if new_width <= 0:
                    return
                factor = new_width / self.original_image.width
                new_height = round(self.original_image.height * factor)
                self.height_entry.delete(0, tk.END)
                self.height_entry.insert(0, str(new_height))
            else:
                height_str = self.height_entry.get().strip()
                if not height_str:
                    return
                new_height = int(float(height_str))
                if new_height <= 0:
                    return
                factor = new_height / self.original_image.height
                new_width = round(self.original_image.width * factor)
                self.width_entry.delete(0, tk.END)
                self.width_entry.insert(0, str(new_width))

            # Определяем режим
            mode = "up" if factor > 1.0 else "down"
            self.mode_var.set(mode)
            # Записываем коэффициент (с округлением до 4 знаков)
            self.scale_entry.delete(0, tk.END)
            self.scale_entry.insert(0, f"{factor:.4g}")

            # Проверить предупреждение (особенно для уменьшения)
            self.update_warning()
        except Exception:
            pass
        finally:
            self._updating = False

    def on_width_changed(self, event=None):
        if self._updating or not self.original_image:
            return
        self.sync_scale_from_dimensions(trigger_by_width=True)

    def on_height_changed(self, event=None):
        if self._updating or not self.original_image:
            return
        self.sync_scale_from_dimensions(trigger_by_width=False)

    # ---------- Масштабирование ----------
    def scale_image(self):
        if not self.original_image:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение")
            return
        try:
            target_width = int(self.width_entry.get())
            target_height = int(self.height_entry.get())
            if target_width <= 0 or target_height <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректные целевые размеры (должны быть целыми положительными числами)")
            return

        self.scaled_image = self.original_image.resize((target_width, target_height), Image.NEAREST)
        self.tabview.set("Превью")
        self.update_preview()

    def update_preview(self, *args):
        if not self.scaled_image:
            return
        zoom = self.zoom_slider.get()
        self.zoom_label_text.configure(text=f"Масштаб: {zoom:.2f}x")
        preview_width = int(self.scaled_image.width * zoom)
        preview_height = int(self.scaled_image.height * zoom)
        preview_img = self.scaled_image.resize((preview_width, preview_height), Image.NEAREST)
        self.photo_image = ImageTk.PhotoImage(preview_img)
        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0, 0, preview_width, preview_height))
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo_image)

    def update_preview_zoom(self, value):
        self.update_preview()

    def cancel_preview(self):
        self.tabview.set("Главная")

    def save_options(self):
        if not self.scaled_image:
            return

        save_win = ctk.CTkToplevel(self)
        save_win.title("Сохранить изображение")
        save_win.geometry("400x180")
        save_win.iconbitmap(icon_path)
        save_win.transient(self)
        save_win.grab_set()
        save_win.resizable(False, False)
        self.center_toplevel(save_win)

        label = ctk.CTkLabel(save_win, text="Как вы хотите сохранить результат?", font=ctk.CTkFont(size=14))
        label.pack(pady=20)

        btn_frame = ctk.CTkFrame(save_win)
        btn_frame.pack(pady=10)

        def overwrite():
            try:
                self.scaled_image.save(self.current_image_path)
                self.original_image = self.scaled_image.copy()
                self.original_size_label.configure(
                    text=f"Оригинальный размер: {self.original_image.width} x {self.original_image.height}"
                )
                # После перезаписи обновляем поля в соответствии с текущим масштабом
                self.update_dimensions_from_scale()
                messagebox.showinfo("Успех", f"Изображение перезаписано:\n{self.current_image_path}")
                save_win.destroy()
                self.tabview.set("Главная")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{str(e)}")

        def save_as():
            file_path = filedialog.asksaveasfilename(
                title="Сохранить как",
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                try:
                    self.scaled_image.save(file_path)
                    messagebox.showinfo("Успех", f"Изображение сохранено:\n{file_path}")
                    save_win.destroy()
                    self.tabview.set("Главная")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{str(e)}")

        overwrite_btn = ctk.CTkButton(
            btn_frame, text="Перезаписать оригинал", command=overwrite,
            fg_color="#d4a373", hover_color="#b5835a"
        )
        overwrite_btn.pack(pady=5, padx=20, fill="x")

        saveas_btn = ctk.CTkButton(
            btn_frame, text="Сохранить как новый файл...", command=save_as,
            fg_color="#1f6aa5", hover_color="#144870"
        )
        saveas_btn.pack(pady=5, padx=20, fill="x")

if __name__ == "__main__":
    app = DragDropScalerApp()
    app.mainloop()