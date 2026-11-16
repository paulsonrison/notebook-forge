# Publish commands

From a verified checkout on the intended release branch:

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python tools/check_package.py
python skills/notebook-forge/scripts/verify_gifs.py examples/animated-demo
python skills/notebook-forge/scripts/check_readability.py examples/animated-demo/notebook.pdf
python tools/build_release.py
git add .claude-plugin .codex-plugin .github README.md CHANGELOG.md assets plugin.json requirements-dev.txt skills tests tools docs examples
git commit -m "feat!: release Notebook Forge 1.0.0 with original animated notes and ruled-text QA"
git tag -a v1.0.0 -m "Notebook Forge v1.0.0: animated learning notes"
git push origin HEAD
git push origin v1.0.0
gh release create v1.0.0 dist/notebook-forge-1.0.0.zip --repo paulsonrison/notebook-forge --title "Notebook Forge v1.0.0 — Animated learning notes" --notes-file docs/releases/v1.0.0.md --verify-tag
```

The version-release workflow can also publish automatically when `plugin.json`
changes on `main`, or through workflow dispatch. It runs verification first,
builds the ZIP, and creates the version tag/release at that exact commit. If
that workflow has already published the version, do not recreate the tag/release.

Changes cover the skill instructions and animation contract; local storyboard,
bundle, technical/editorial and ruled-page verification scripts; optional JSON
schema fields; ReportLab text masks and PDF stills; dependencies and regression
tests; original three-topic and overlap examples; icon/UI/plugin metadata;
changelog, README, package checks, release packaging and CI.
