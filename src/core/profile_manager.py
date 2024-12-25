import os
import json
from typing import Dict, List, Set

class ProfileManager:
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "profiles.json")
        self.profiles: Dict[str, List[str]] = {}
        self.current_profile = "Стандартный"
        self.load_profiles()

    def load_profiles(self) -> None:
        """Загрузка профилей из файла конфигурации"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.profiles = json.load(f)
        except Exception:
            self.profiles = {"Стандартный": []}
            self.save_profiles()

    def save_profiles(self) -> None:
        """Сохранение профилей в файл конфигурации"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"Не удалось сохранить профили: {str(e)}")

    def get_profile(self, name: str) -> Set[str]:
        """Получение профиля по имени"""
        return set(self.profiles.get(name, []))

    def save_profile(self, name: str, patterns: Set[str]) -> None:
        """Сохранение профиля"""
        if name == "Стандартный":
            raise ValueError("Нельзя изменить стандартный профиль")
        self.profiles[name] = list(patterns)
        self.save_profiles()

    def delete_profile(self, name: str) -> None:
        """Удаление профиля"""
        if name == "Стандартный":
            raise ValueError("Нельзя удалить стандартный профиль")
        if name in self.profiles:
            del self.profiles[name]
            self.save_profiles()

    def get_profile_names(self) -> List[str]:
        """Получение списка имен профилей"""
        return list(self.profiles.keys()) 