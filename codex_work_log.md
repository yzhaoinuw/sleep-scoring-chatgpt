# Codex Work Log

Prepend new session notes to the top of this file.

## 2026-05-03

### Done Today

- Clarified the direct-run parameter block comments in `run_inference_chatgpt.py` so they read as local overrides rather than silently implying lockstep sync with `config.py`.
- Updated the README intro to point back to the source `sleep_scoring` repository branch used for the extraction.
- Added project-local `.env` loading for `OPENAI_API_KEY` so the backend now honors the documented local-key workflow without requiring the parent shell to preload the variable.
- Made `overview_only` inference seed the full recording as `NREM` before overlaying model-returned `Wake`/`REM` bouts, bringing its baseline behavior in line with `fixed_windows`.
- Added runtime environment notes to this repo's `AGENTS.md`, including the known-good conda interpreter path and a pytest temp-directory workaround for this machine.
- Reworked the newer inference tests to use explicit repo-local temp folders instead of pytest's default temp fixture, avoiding local Windows permission issues during cleanup.
- Removed the leftover app-style `assets/` nesting from the packaged reference examples.
- Moved the bundled reference-example pack to `sleep_scoring_chatgpt/sleep_scoring_examples/`.
- Simplified inference configuration to two explicit modes:
  - `overview_only`
  - `fixed_windows`
- Replaced equal-quarter refinement with fixed one-hour zoom windows so target window scale stays aligned with the bundled examples while using a simpler clock-based duration.
- Matched reference-example packaging to the active inference mode:
  - overview mode sends only the overview example,
  - fixed-window mode sends only the zoom-window examples.
- Removed the temporary compatibility wrapper modules at:
  - `sleep_scoring_chatgpt/chatgpt_inference.py`
  - `sleep_scoring_chatgpt/chatgpt_preview.py`
  - `sleep_scoring_chatgpt/make_figure_dev.py`
- Converted `groundtruth_reasons_model_friendly.txt` into structured `groundtruth_reasons.json`.
- Updated the inference loader to read structured reference-example JSON and format the model-facing calibration prompt from it.
- Generated the missing bundled reference PNGs from `35_app13_groundtruth.mat`:
  - overview image,
  - refinement-window images aligned with the current fixed-window example layout.
- Added ignore-rule exceptions so the committed reference JSON/PNG files are tracked even though generic `*.json` and `*.png` outputs stay ignored.
- Added a regression test for reference-example prompt assembly in `tests/test_inference_chatgpt.py`.

### Verification

- Ran `C:\Users\yzhao\miniconda3\envs\sleep_scoring_dash3.0\python.exe -m pytest tests\test_inference_chatgpt.py` and confirmed all focused inference tests pass after the temp-folder rewrite.
- Ran `C:\Users\yzhao\miniconda3\envs\sleep_scoring_dash3.0\python.exe -m pytest tests\test_chatgpt_tools.py tests\test_inference_chatgpt.py` and confirmed all tests pass.
- Ran `C:\Users\yzhao\miniconda3\envs\sleep_scoring_dash3.0\python.exe -m compileall sleep_scoring_chatgpt`.

### Notes

- The large `.mat` recordings under `user_test_files/` remain intentionally uncommitted local data.

## 2026-05-02

### Done Today

- Created a standalone repository `sleep-scoring-chatgpt` from the `codex/chatgpt` branch of the parent `sleep_scoring` project.
- Extracted the backend-only ChatGPT inference workflow into this repo:
  - copied the CLI preview entrypoint,
  - copied the ChatGPT inference backend,
  - copied the helper utilities,
  - copied the figure and spectrogram helpers,
  - copied the scoring guidance prompt,
  - copied the bundled reference-example assets,
  - copied the focused backend tests and fixtures.
- Added standalone repository metadata:
  - `pyproject.toml`
  - `README.md`
  - `LICENSE`
  - `.gitignore`
  - `.python-version`
- Renamed selected modules to support future multi-backend expansion while keeping ChatGPT-specific backend names explicit:
  - `chatgpt_preview.py` -> `run_inference_chatgpt.py`
  - `chatgpt_inference.py` -> `inference_chatgpt.py`
  - `make_figure_dev.py` -> `make_figure.py`
- Added project memory docs for future agents:
  - `project_overview.md`
  - `codex_work_log.md`

### Verification

- Ran `C:\Users\yzhao\miniconda3\envs\sleep_scoring_dash3.0\python.exe -m py_compile` on the extracted modules.
- Ran `C:\Users\yzhao\miniconda3\envs\sleep_scoring_dash3.0\python.exe -m pytest tests\test_chatgpt_tools.py` and confirmed all copied tests pass.
- Ran `C:\Users\yzhao\miniconda3\envs\sleep_scoring_dash3.0\python.exe -m sleep_scoring_chatgpt.run_inference_chatgpt --help` and confirmed the CLI help renders.

### Next Steps

- Run one or more real OpenAI inference calls from this standalone repo to confirm the extracted API path works end to end outside the parent app.
- Decide whether `chatgpt_tools.py` should remain ChatGPT-specific or be generalized into a shared tools layer once a second backend exists.
- If another model backend is added later, mirror the existing naming pattern with sibling modules rather than overloading the current ChatGPT-specific files.
