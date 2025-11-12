from pathlib import Path
import shutil
import re
from typing import List, Union
from workflow_utils import WorkflowFileNotFound

class FileBackupManager:
    def __init__(self, result_dir: Path):
        self.vsrc_dir = result_dir / "vsrc"
        self.vsrc_dir.mkdir(parents=True, exist_ok=True)
        self.backup_map = {}
        self._original_content = {}

    def backup(self, src_path: Union[Path, str, List[Union[Path, str]]]):
        if isinstance(src_path, (list, tuple)):
            result = []
            for p in src_path:
                result.append(self.backup(Path(p)))
            return result
        src_path = Path(src_path)
        dst_path = self.vsrc_dir / src_path.name
        if src_path.exists():
            if src_path.resolve() != dst_path.resolve():
                shutil.copy(src_path, dst_path)
            self.backup_map[src_path.resolve()] = dst_path
        else:
            raise WorkflowFileNotFound(f"{src_path} not found, cannot backup.")
        return dst_path

    def replace(self, filename: Union[str, List[str]], pattern: str, repl: str):
        if isinstance(filename, (list, tuple)):
            for f in filename:
                self.replace(f, pattern, repl)
            return
        file_path = self.vsrc_dir / filename
        if not file_path.exists():
            raise WorkflowFileNotFound(f"{file_path} not found, cannot replace.")
        text = file_path.read_text()
        if file_path not in self._original_content:
            self._original_content[file_path] = text
        new_text, count = re.subn(pattern, repl, text)
        if count > 0:
            file_path.write_text(new_text)

    def restore(self, filename: Union[str, List[str]]):
        if isinstance(filename, (list, tuple)):
            for f in filename:
                self.restore(f)
            return
        file_path = self.vsrc_dir / filename
        if file_path in self._original_content:
            file_path.write_text(self._original_content[file_path])

    def get_backup_path(self, src_path: Union[Path, str, List[Union[Path, str]]]):
        if isinstance(src_path, (list, tuple)):
            return [self.get_backup_path(Path(p)) for p in src_path]
        src_path = Path(src_path)
        return self.backup_map.get(src_path.resolve(), self.vsrc_dir / src_path.name)