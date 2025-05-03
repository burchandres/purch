from pathlib import Path
from tomllib import load


def get_project_version() -> str:
    """Get the version of the project from pyproject.toml."""
    try:
        path_to_pyproject_toml = project_toml(__file__)
        with open(path_to_pyproject_toml, "rb") as f:
            return load(f)["project"]["version"]
    except FileNotFoundError:
        return "0.0.0"


def project_toml(start) -> Path:
    """Find the project root directory by locating pyproject.toml."""
    toml_name = "pyproject.toml"
    current_file = Path(start)
    for parent_directory in current_file.parents:
        possible_toml = parent_directory / toml_name
        if possible_toml.is_file():
            return possible_toml
    raise FileNotFoundError("Could not find project root containing pyproject.toml")


version = get_project_version()
