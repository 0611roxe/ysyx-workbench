import shutil
import sys
from pathlib import Path
import re

class FileBackupManager:
    def __init__(self, result_dir: Path):
        self.vsrc_dir = result_dir / "vsrc"
        self.vsrc_dir.mkdir(parents=True, exist_ok=True)
        self.backup_map = {} 
        self._original_content = {} 

    def backup(self, src_path: Path):
        dst_path = self.vsrc_dir / src_path.name
        if src_path.exists():
            if src_path.resolve() != dst_path.resolve():
                shutil.copy(src_path, dst_path)
            self.backup_map[src_path.resolve()] = dst_path
        else:
            print(f"Warning: {src_path} not found, skip backup.", file=sys.stderr)
        return dst_path

    def replace(self, filename: str, pattern: str, repl: str):
        file_path = self.vsrc_dir / filename
        if not file_path.exists():
            print(f"Warning: {file_path} not found, skip replacement.", file=sys.stderr)
            return
        text = file_path.read_text()
        if file_path not in self._original_content:
            self._original_content[file_path] = text 
        new_text, count = re.subn(pattern, repl, text)
        if count > 0:
            file_path.write_text(new_text)
            print(f"Replaced {pattern} with {repl} in {file_path}")
        else:
            print(f"{pattern} not found in {file_path}, no replacement made.", file=sys.stderr)

    def restore(self, filename: str):
        file_path = self.vsrc_dir / filename
        if file_path in self._original_content:
            file_path.write_text(self._original_content[file_path])
            print(f"Restored {file_path} to original content.")
        else:
            print(f"No backup found for {file_path}, nothing restored.", file=sys.stderr)

    def get_backup_path(self, src_path: Path):
        return self.backup_map.get(src_path.resolve(), self.vsrc_dir / src_path.name)