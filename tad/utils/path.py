from pathlib import Path


def is_safe_path(basedir: Path, path: Path, follow_symlinks: bool = True) -> bool:
    # Resolve the absolute path of the base directory
    base = basedir.resolve()

    # Resolve the absolute path of the provided path
    target = path.resolve() if follow_symlinks else path

    # Check if the target path starts with the base directory path
    return target.is_relative_to(base) or base == target
