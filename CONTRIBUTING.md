# Contributing

Keep changes within the documented contract and add regression cases for changed behavior.
Run `python -m unittest -v`, `python -m compileall -q .`, and the clean-environment
wheel/installed-command check in `.github/workflows/test.yml`. Preserve conservative
unsupported states; do not weaken checks to make defective output pass.
