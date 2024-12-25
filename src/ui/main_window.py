import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from typing import Optional, Callable

from ..core.directory_scanner import DirectoryScanner
from ..core.profile_manager import ProfileManager
from .tree_view import TreeView
from ..config.default_excludes import DEFAULT_EXCLUDES

class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Генератор структуры каталогов")
        
        # Инициализация компонентов
        self.current_directory: Optional[str] = None
        self.profile_manager = ProfileManager(
            os.path.join(os.path.expanduser("~"), ".dir_tree_app")
        )
        self.directory_scanner = DirectoryScanner(set(DEFAULT_EXCLUDES))
        
        self._init_ui()
        self._bind_events()
        
    def _init_ui(self) -> None:
        """Инициализация пользовательского интерфейса"""
        # Главный контейнер
        main_container = ttk.Frame(self.root, padding="5")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Фрейм для профилей
        self._init_profile_frame(top_frame)
        
        # Фрейм для текущей директории
        self._init_directory_frame(top_frame)
        
        # Фрейм с кнопками управления
        self._init_control_buttons(main_container)
        
        # Дерево директорий
        tree_container = ttk.Frame(main_container)
        tree_container.pack(fill=tk.BOTH, expand=True)
        self.tree_view = TreeView(tree_container)
        
        # Строка состояния
        self._init_status_bar(main_container)
        
    def _init_profile_frame(self, parent: ttk.Frame) -> None:
        """Инициализация фрейма с профилями"""
        profile_frame = ttk.LabelFrame(parent, text="Профиль исключений", padding="5")
        profile_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Комбобокс для выбора профиля
        self.current_profile = tk.StringVar(value="Стандартный")
        self.profile_combo = ttk.Combobox(
            profile_frame,
            textvariable=self.current_profile,
            values=self.profile_manager.get_profile_names(),
            state="readonly"
        )
        self.profile_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Кнопки управления профилями
        ttk.Button(profile_frame, text="Сохранить", 
                  command=self._save_current_profile).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(profile_frame, text="Сохранить как...", 
                  command=self._save_profile_as).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(profile_frame, text="Удалить", 
                  command=self._delete_profile).pack(side=tk.LEFT)
                  
    def _init_directory_frame(self, parent: ttk.Frame) -> None:
        """Инициализация фрейма с текущей директорией"""
        dir_frame = ttk.LabelFrame(parent, text="Текущая директория", padding="5")
        dir_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.directory_label = ttk.Label(dir_frame, text="Не выбрана", wraplength=700)
        self.directory_label.pack(fill=tk.X)
        
    def _init_control_buttons(self, parent: ttk.Frame) -> None:
        """Инициализация кнопок управления"""
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Левая часть с кнопками
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(side=tk.LEFT, fill=tk.X)
        
        ttk.Button(button_frame, text="Выбрать директорию", 
                  command=self._select_directory).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Сохранить в TXT", 
                  command=self._save_structure).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Очистить исключения", 
                  command=self._clear_exclusions).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Управление шаблонами", 
                  command=self._show_patterns_dialog).pack(side=tk.LEFT)
                  
        # Правая часть с информацией об исключениях
        info_frame = ttk.Frame(controls_frame)
        info_frame.pack(side=tk.RIGHT)
        
        self.excluded_count_var = tk.StringVar(value="Исключено: 0")
        excluded_count_label = ttk.Label(
            info_frame,
            textvariable=self.excluded_count_var,
            font=("", 9, "italic")
        )
        excluded_count_label.pack(side=tk.RIGHT)
        
    def _init_status_bar(self, parent: ttk.Frame) -> None:
        """Инициализация строки состояния"""
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            parent,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            padding=(5, 2)
        )
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        self.update_status("Готов к работе")
        
    def _bind_events(self) -> None:
        """Привязка обработчиков событий"""
        self.profile_combo.bind('<<ComboboxSelected>>', self._on_profile_changed)
        self.tree_view.bind_events(
            on_exclude=self._exclude_selected,
            on_include=self._include_selected,
            on_add_pattern=self._add_to_patterns,
            on_double_click=self._on_double_click
        )
        
    def update_status(self, message: str) -> None:
        """Обновление строки состояния"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"[{timestamp}] {message}")
        
    def _update_excluded_count(self) -> None:
        """Обновление счетчика исключенных элементов"""
        count = len(self.tree_view.excluded_items)
        self.excluded_count_var.set(f"Исключено: {count}")
        
    def _select_directory(self) -> None:
        """Выбор директории для сканирования"""
        directory = filedialog.askdirectory(title="Выберите директорию для сканирования")
        if directory:
            self.current_directory = directory
            self.directory_label.config(text=directory)
            self._scan_directory()
            
    def _scan_directory(self) -> None:
        """Сканирование выбранной директории"""
        if not self.current_directory:
            return
            
        self.tree_view.clear()
        root_node = self.tree_view.add_root(
            os.path.basename(self.current_directory),
            [self.current_directory]
        )
        self._scan_recursive(root_node, self.current_directory)
        self.update_status(f"Загружена структура директории: {self.current_directory}")
        
    def _scan_recursive(self, parent: str, path: str) -> None:
        """Рекурсивное сканирование директории"""
        items = self.directory_scanner.scan_directory(path)
        for name, full_path, item_type in items:
            icon = "🗀 " if item_type == 'dir' else "📄 "
            node = self.tree_view.add_item(parent, icon + name, [full_path])
            if item_type == 'dir':
                self._scan_recursive(node, full_path)
                
    def _save_structure(self) -> None:
        """Сохранение структуры в файл"""
        if not self.current_directory:
            messagebox.showwarning("Предупреждение", "Сначала выберите директорию!")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
            initialfile=f"structure_{os.path.basename(self.current_directory)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if not save_path:
            return
            
        try:
            self._save_tree_to_file(save_path)
            self.update_status(f"Структура сохранена в файл: {save_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")
            self.update_status(f"Ошибка при сохранении: {str(e)}")
            
    def _save_tree_to_file(self, save_path: str) -> None:
        """Сохранение дерева в файл"""
        def traverse(iid: str, depth: int = 0) -> list:
            if iid in self.tree_view.excluded_items:
                return []
            item_text = self.tree_view.get_item_text(iid)
            if item_text.startswith(("🗀 ", "📄 ")):
                item_text = item_text[2:]
            lines = [f"{'    '*depth}{item_text}"]
            for child in self.tree_view.tree.get_children(iid):
                lines.extend(traverse(child, depth + 1))
            return lines
            
        lines = []
        for root_item in self.tree_view.tree.get_children():
            lines.extend(traverse(root_item, 0))
            
        with open(save_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
    def _exclude_selected(self) -> None:
        """Исключение выбранных элементов"""
        selected_items = self.tree_view.get_selected_items()
        if not selected_items:
            self.update_status("Не выбраны элементы для исключения")
            return
            
        self.tree_view.exclude_items(selected_items)
        self.update_status(f"Исключено элементов: {len(selected_items)}")
        self._update_excluded_count()
        
    def _include_selected(self) -> None:
        """Включение выбранных элементов"""
        selected_items = self.tree_view.get_selected_items()
        if not selected_items:
            self.update_status("Не выбраны элементы для включения")
            return
            
        self.tree_view.include_items(selected_items)
        self.update_status(f"Включено обратно элементов: {len(selected_items)}")
        self._update_excluded_count()
        
    def _clear_exclusions(self) -> None:
        """Очистка всех исключений"""
        if not self.tree_view.excluded_items:
            self.update_status("Нет исключенных элементов")
            return
            
        count = len(self.tree_view.excluded_items)
        self.tree_view.excluded_items.clear()
        for item in self.tree_view.tree.get_children():
            self.tree_view.tree.item(item, tags=())
        self.update_status(f"Очищены все исключения ({count} элементов)")
        self._update_excluded_count()
        
    def _add_to_patterns(self) -> None:
        """Добавление выбранных элементов в шаблоны"""
        selected_items = self.tree_view.get_selected_items()
        if not selected_items:
            return
            
        added_count = 0
        for item in selected_items:
            item_text = self.tree_view.get_item_text(item)
            if item_text.startswith(("🗀 ", "📄 ")):
                item_text = item_text[2:]
                
            if item_text not in self.directory_scanner.excluded_patterns:
                self.directory_scanner.excluded_patterns.add(item_text)
                added_count += 1
                
                # Автоматически исключаем элемент
                self.tree_view.exclude_items([item])
                
        if added_count > 0:
            profile_name = self.current_profile.get()
            if profile_name != "Стандартный":
                self.profile_manager.save_profile(profile_name, self.directory_scanner.excluded_patterns)
                self.update_status(f"Добавлено {added_count} шаблонов исключений")
                self._update_excluded_count()
                
    def _on_double_click(self, event) -> None:
        """Обработка двойного клика по элементу"""
        item = self.tree_view.get_selected_items()[0]
        if item:
            path = self.tree_view.get_item_values(item)[0]
            if os.path.isdir(path):
                os.startfile(path)
                self.update_status(f"Открыта директория: {path}")
                
    def _on_profile_changed(self, event=None) -> None:
        """Обработка изменения профиля"""
        profile_name = self.current_profile.get()
        self.directory_scanner.excluded_patterns = self.profile_manager.get_profile(profile_name)
        self.update_status(f"Загружен профиль: {profile_name}")
        if self.current_directory:
            self._scan_directory()
            
    def _save_current_profile(self) -> None:
        """Сохранение текущего профиля"""
        try:
            profile_name = self.current_profile.get()
            self.profile_manager.save_profile(profile_name, self.directory_scanner.excluded_patterns)
            self.update_status(f"Профиль {profile_name} сохранен")
        except ValueError as e:
            messagebox.showwarning("Предупреждение", str(e))
            
    def _save_profile_as(self) -> None:
        """Сохранение профиля под новым именем"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Сохранить профиль как")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Название профиля:").pack(padx=5, pady=5)
        entry = ttk.Entry(dialog)
        entry.pack(padx=5, pady=5, fill=tk.X)
        
        def save():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Предупреждение", "Введите название профиля")
                return
            if name == "Стандартный":
                messagebox.showwarning("Предупреждение", "Нельзя использовать название 'Стандартный'")
                return
                
            self.profile_manager.save_profile(name, self.directory_scanner.excluded_patterns)
            self.profile_combo['values'] = self.profile_manager.get_profile_names()
            self.current_profile.set(name)
            self.update_status(f"Создан новый профиль: {name}")
            dialog.destroy()
            
        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=5)
        
        # Центрируем диалог
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
    def _delete_profile(self) -> None:
        """Удаление текущего профиля"""
        try:
            profile_name = self.current_profile.get()
            if messagebox.askyesno("Подтверждение", f"Удалить профиль {profile_name}?"):
                self.profile_manager.delete_profile(profile_name)
                self.profile_combo['values'] = self.profile_manager.get_profile_names()
                self.current_profile.set("Стандартный")
                self._on_profile_changed()
                self.update_status(f"Удален профиль: {profile_name}")
        except ValueError as e:
            messagebox.showwarning("Предупреждение", str(e))
            
    def _show_patterns_dialog(self) -> None:
        """Отображение диалога управления шаблонами"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Управление шаблонами исключений")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="5")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Текущие шаблоны исключений:").pack(fill=tk.X)
        
        # Список с прокруткой
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        patterns_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        patterns_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=patterns_list.yview)
        
        # Заполняем список
        for pattern in sorted(self.directory_scanner.excluded_patterns):
            patterns_list.insert(tk.END, pattern)
            
        # Поле ввода для нового шаблона
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        entry = ttk.Entry(input_frame)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        def add_pattern():
            pattern = entry.get().strip()
            if pattern and pattern not in self.directory_scanner.excluded_patterns:
                self.directory_scanner.excluded_patterns.add(pattern)
                patterns_list.insert(tk.END, pattern)
                entry.delete(0, tk.END)
                self.update_status(f"Добавлен шаблон: {pattern}")
                
        def remove_selected():
            selection = patterns_list.curselection()
            if not selection:
                return
                
            patterns_to_remove = [patterns_list.get(i) for i in selection]
            for pattern in patterns_to_remove:
                if pattern not in DEFAULT_EXCLUDES:
                    self.directory_scanner.excluded_patterns.remove(pattern)
                    patterns_list.delete(patterns_list.index(pattern))
                    
            self.update_status(f"Удалено шаблонов: {len(patterns_to_remove)}")
            
        ttk.Button(input_frame, text="Добавить", command=add_pattern).pack(side=tk.LEFT)
        ttk.Button(frame, text="Удалить выбранные", command=remove_selected).pack(fill=tk.X, pady=5)
        ttk.Button(frame, text="Закрыть", command=dialog.destroy).pack(fill=tk.X)
        
        # Центрируем диалог
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}") 