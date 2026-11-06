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
    assert len(identity) == 1 and data[0]["name"] == "notebook-forge", identity
    expected_skills = {"notebook-forge", "resume-optimizer", "case-study-writing"}
    discovered = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}
    assert discovered == expected_skills, f"Expected {expected_skills}; found {discovered}"
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
    for name in sorted(expected_skills):
        package = ROOT / "skills" / name
        text = (package / "SKILL.md").read_text(encoding="utf-8-sig")
        frontmatter = yaml.safe_load(text.split("---", 2)[1])
        assert frontmatter["name"] == name
        assert 0 < len(frontmatter["description"]) <= 1024
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" not in target:
                resolved = (package / target).resolve()
                assert resolved.is_relative_to(package.resolve()) and resolved.is_file(), target
        ui_data = yaml.safe_load((package / "agents/openai.yaml").read_text(encoding="utf-8"))
        assert "$" + name in ui_data["interface"]["default_prompt"]
        for icon in ("icon_small", "icon_large"):
            if icon in ui_data["interface"]:
                assert (package / ui_data["interface"][icon]).is_file()
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
    print("Package OK: all three skills, matching identities, manifests, references and font license.")


if __name__ == "__main__":
    check_package()
