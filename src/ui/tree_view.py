import tkinter as tk
from tkinter import ttk
from typing import Callable, Set, Optional

class TreeView:
    def __init__(self, parent: ttk.Frame):
        self.tree = ttk.Treeview(parent, selectmode="extended")
        self.tree_scroll = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        
        # Настройка стилей
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        
        # Размещение элементов
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Набор исключённых элементов
        self.excluded_items: Set[str] = set()
        
        # Настройка тегов
        self.tree.tag_configure("excluded", foreground="red")
        
        # Контекстное меню
        self.popup_menu = tk.Menu(parent, tearoff=0)
        
    def bind_events(self, 
                   on_exclude: Callable, 
                   on_include: Callable,
                   on_add_pattern: Callable,
                   on_double_click: Callable) -> None:
        """Привязка обработчиков событий"""
        self.popup_menu.add_command(label="Исключить выбранные (Del)", command=on_exclude)
        self.popup_menu.add_command(label="Включить выбранные", command=on_include)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label="Добавить в шаблоны", command=on_add_pattern)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Double-1>", on_double_click)
        self.tree.bind("<Delete>", lambda e: on_exclude())
        self.tree.bind("<Control-a>", self._select_all)
        
    def clear(self) -> None:
        """Очистка дерева"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.excluded_items.clear()
        
    def add_root(self, text: str, values: list) -> str:
        """Добавление корневого элемента"""
        return self.tree.insert("", "end", text=text, open=True, values=values)
        
    def add_item(self, parent: str, text: str, values: list) -> str:
        """Добавление элемента в дерево"""
        return self.tree.insert(parent, "end", text=text, values=values)
        
    def exclude_items(self, items: list) -> None:
        """Исключение элементов"""
        for item in items:
            self.excluded_items.add(item)
            self.tree.item(item, tags=("excluded",))
            
    def include_items(self, items: list) -> None:
        """Включение элементов"""
        for item in items:
            if item in self.excluded_items:
                self.excluded_items.remove(item)
                self.tree.item(item, tags=())
                
    def get_selected_items(self) -> list:
        """Получение выбранных элементов"""
        return self.tree.selection()
        
    def get_item_text(self, item: str) -> str:
        """Получение текста элемента"""
        return self.tree.item(item)["text"]
        
    def get_item_values(self, item: str) -> list:
        """Получение значений элемента"""
        return self.tree.item(item)["values"]
        
    def _show_context_menu(self, event) -> None:
        """Отображение контекстного меню"""
        if len(self.tree.selection()) > 0:
            self.popup_menu.post(event.x_root, event.y_root)
            
    def _select_all(self, event=None) -> str:
        """Выделение всех элементов"""
        self.tree.selection_set(self.tree.get_children())
        return "break"  # Предотвращаем стандартное поведение Ctrl+A 