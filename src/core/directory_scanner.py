import os
from typing import Set, List, Optional

class DirectoryScanner:
    def __init__(self, excluded_patterns: Set[str]):
        self.excluded_patterns = excluded_patterns

    def should_exclude(self, name: str) -> bool:
        return name in self.excluded_patterns

    def scan_directory(self, path: str) -> List[tuple]:
        """
        Сканирует директорию и возвращает список кортежей (имя, полный путь, тип)
        где тип - это 'dir' для директорий и 'file' для файлов
        """
        result = []
        try:
            items = sorted(os.listdir(path), 
                         key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
            
            for item in items:
                if self.should_exclude(item):
                    continue
                    
                full_path = os.path.join(path, item)
                item_type = 'dir' if os.path.isdir(full_path) else 'file'
                result.append((item, full_path, item_type))
                
        except PermissionError:
            print(f"Отказано в доступе: {path}")
        except Exception as e:
            print(f"Ошибка при чтении {path}: {str(e)}")
            
        return result 