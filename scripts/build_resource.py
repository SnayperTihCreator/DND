import subprocess
from pathlib import Path
import hashlib

import typer
from rich.console import Console

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})
console = Console()


def get_file_hash(path: Path) -> str:
    """Вычисляет SHA256 хеш файла."""
    hash_sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


@app.command()
def main(
        folder: Path = typer.Argument(..., help="Path to folder containing resource"),
        pattern_finder: str = typer.Argument(..., help="Pattern finder for resource"),
        pattern_output: str = typer.Argument(..., help="Pattern output for resource"),
        build_command: str = typer.Argument(..., help="Build command"),
):
    for path in folder.rglob(pattern_finder):
        hash_file = path.with_suffix(f"{path.suffix}.sha256")
        
        hs = get_file_hash(path)
        
        if hash_file.exists() and (hash_file.read_text(encoding="utf-8") == hs):
            console.print(f"Cached {path.name}")
            continue
        
        console.print(f"Building {path.name}")
        hash_file.write_text(hs, encoding="utf-8")
        
        resource = path.with_name(f"{path.stem}{pattern_output}")
        command = build_command.format(input=path.as_posix(), output=resource.as_posix())
        if subprocess.check_call(command, shell=True) == 0:
            console.print(f"Build {path.name}")


if __name__ == '__main__':
    app()
