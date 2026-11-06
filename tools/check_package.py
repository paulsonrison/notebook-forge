"""Check release metadata and self-contained skill references."""
import json
from pathlib import Path
import re
import sys
import yaml
import jsonschema

ROOT = Path(__file__).resolve().parents[1]


def check_package():
    manifests = [
        ROOT / "plugin.json",
        ROOT / ".codex-plugin/plugin.json",
        ROOT / ".claude-plugin/plugin.json",
    ]
    data = [json.loads(path.read_text(encoding="utf-8")) for path in manifests]
    identity = {(d["name"], d["version"]) for d in data}
    assert identity == {("notebook-forge", "0.3.0")}, identity
    assert {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()} == {"notebook-forge"}
    skill = ROOT / "skills/notebook-forge"
    content = (skill / "SKILL.md").read_text(encoding="utf-8")
    _, header, _ = content.split("---", 2)
    meta = yaml.safe_load(header)
    assert meta["name"] == skill.name
    assert 0 < len(meta["description"]) <= 1024
    assert meta["metadata"]["version"] == data[0]["version"]
    assert len(meta["name"]) <= 64 and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", meta["name"])
    for target in re.findall(r"\]\(([^)]+)\)", content):
        if "://" not in target:
            resolved = (skill / target).resolve()
            assert resolved.is_relative_to(skill.resolve()) and resolved.is_file(), target
    ui = yaml.safe_load((skill / "agents/openai.yaml").read_text(encoding="utf-8"))
    assert "$notebook-forge" in ui["interface"]["default_prompt"]
    assert 25 <= len(ui["interface"]["short_description"]) <= 64
    for path in (ROOT / ".agents/plugins/marketplace.json", ROOT / ".claude-plugin/marketplace.json"):
        marketplace = json.loads(path.read_text(encoding="utf-8"))
        entry = marketplace["plugins"][0]
        assert entry["name"] == data[0]["name"]
        source = entry["source"]
        source_path = source["path"] if isinstance(source, dict) else source
        assert source_path.startswith("./") and (ROOT / source_path).resolve() == ROOT
    assert (ROOT / "assets/icon.svg").is_file()
    assert (skill / "assets/fonts/ComicNeue-Bold.ttf").read_bytes()[:4] == b"\x00\x01\x00\x00"
    assert "SIL OPEN FONT LICENSE" in (skill / "assets/fonts/OFL.txt").read_text()
    assert data[1]["skills"] == "./skills/"
    assert "reportlab" in (skill / "requirements.txt").read_text()
    schema = json.loads((skill / "references/job.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    example = json.loads((ROOT / "examples/learning-notebook.json").read_text(encoding="utf-8"))
    jsonschema.validate(example, schema)
    print("Package OK: matching identities, self-contained skill, manifests, references and font license.")


if __name__ == "__main__":
    check_package()
