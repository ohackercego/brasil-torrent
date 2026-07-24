import os
import sys


def resource_path(relative_path: str) -> str:
    """Retorna o caminho absoluto para um recurso empacotado.

    Funciona tanto em modo dev quanto em modo frozen (PyInstaller).
    """
    if getattr(sys, 'frozen', False):
        base_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)), 'client')
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def data_path(relative_path: str = "") -> str:
    """Retorna o caminho para dados de runtime (graváveis).

    Fica sempre ao lado do executável em 'data/'.
    """
    base = os.path.join(_executable_dir(), 'data')
    if relative_path:
        return os.path.join(base, relative_path)
    return base


def log_path() -> str:
    """Retorna o diretório de logs."""
    path = os.path.join(_executable_dir(), 'logs')
    os.makedirs(path, exist_ok=True)
    return path


def download_path(relative_path: str = "") -> str:
    """Retorna o diretório de downloads."""
    base = os.path.join(_executable_dir(), 'downloads')
    if relative_path:
        return os.path.join(base, relative_path)
    return base


def _executable_dir() -> str:
    """Retorna o diretório onde está o executável (ou o diretório do projeto em dev)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


# Garante que os diretórios de dados existam
os.makedirs(data_path(), exist_ok=True)
os.makedirs(log_path(), exist_ok=True)
os.makedirs(download_path(), exist_ok=True)
