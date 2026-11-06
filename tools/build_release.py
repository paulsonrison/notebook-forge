"""Build a portable ZIP from an explicit allowlist; no caches or private inputs."""
from pathlib import Path
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ALLOW = [
    "plugin.json", ".codex-plugin", ".claude-plugin", ".agents",
    "skills", "assets", "examples", "requirements.txt", "requirements-dev.txt",
    "README.md", "LICENSE", "tests", "tools", ".github",
    ".gitignore", ".gitattributes", "docs/design.md", "docs/implementation-plan.md",
    "docs/behaviour-tests.md",
]


def build_release(destination=None):
    version = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
    destination = Path(destination or ROOT / f"dist/notebook-forge-{version}.zip")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in ALLOW:
            path = ROOT / item
            for source in sorted(path.rglob("*")) if path.is_dir() else [path]:
                if source.is_file() and "__pycache__" not in source.parts and source.suffix not in (".pyc", ".pyo"):
                    archive.write(source, "notebook-forge/" + source.relative_to(ROOT).as_posix())
    print(destination)
    return destination


if __name__ == "__main__":
    build_release()
