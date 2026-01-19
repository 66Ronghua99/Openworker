import os
from typing import List
from openworker.state import StateDB, get_db

class PathGuard:
    def __init__(self, db: StateDB = None):
        self.db = db or get_db()

    def _get_allowed_folders(self) -> List[str]:
        return self.db.list_folders()

    def validate_path(self, target_path: str) -> bool:
        """
        Checks if the target_path (resolved) is within any of the allowed folders.
        """
        try:
            real_target = os.path.realpath(os.path.abspath(target_path))
            allowed_folders = self._get_allowed_folders()
            
            for folder in allowed_folders:
                real_folder = os.path.realpath(os.path.abspath(folder))
                # Check if target is inside the folder (common prefix)
                if os.path.commonpath([real_folder, real_target]) == real_folder:
                    return True
            return False
        except Exception:
            return False

    def list_allowed_files(self, recursive=True) -> List[str]:
        """
        Actually lists all safe files (optional helper).
        """
        # Implementation depends on need, for now just path validation is key.
        pass

_guard = None
def get_guard():
    global _guard
    if _guard is None:
        _guard = PathGuard()
    return _guard
