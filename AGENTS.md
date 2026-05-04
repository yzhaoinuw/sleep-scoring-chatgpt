# AGENTS.md

In the beginning of a new chat for this project, check inside the project folder for any MD files that may be an instruction or memory log created for the Codex agent for that project.

If the user says "commit and push" without specifying a branch, treat that as a request to push to `main` unless the user says otherwise or there is a concrete reason to pause and confirm.

## Runtime Environment

When running Python, tests, or one-off scripts for this repository, use the conda environment:

- `sleep_scoring_dash3.0`

Typical startup:

```powershell
conda activate sleep_scoring_dash3.0
```

Direct interpreter path:

```powershell
C:\Users\yzhao\miniconda3\envs\sleep_scoring_dash3.0\python.exe
```

Prefer this interpreter if `python` or `pytest` is not available on PATH in the current shell. Typical commands:

```powershell
C:\Users\yzhao\miniconda3\envs\sleep_scoring_dash3.0\python.exe -m pytest
C:\Users\yzhao\miniconda3\envs\sleep_scoring_dash3.0\python.exe -m compileall sleep_scoring_chatgpt
```

If `pytest` hits a `PermissionError` under `C:\Users\yzhao\AppData\Local\Temp\pytest-of-yzhao`, use a repo-local base temp:

```powershell
C:\Users\yzhao\miniconda3\envs\sleep_scoring_dash3.0\python.exe -m pytest --basetemp .pytest_tmp
```
