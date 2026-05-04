# Sleep Scoring ChatGPT Project Overview

## What This Repo Is

This repository is a standalone extraction of the ChatGPT-based sleep-scoring backend that was originally prototyped inside the larger `sleep_scoring` desktop application.

The goal of this repo is to preserve and extend the backend-only experimental inference workflow without carrying the Dash app, pywebview shell, video features, or non-ChatGPT scoring paths.

## Current Purpose

The repo is meant to:

- run ChatGPT-based sleep scoring on a single MATLAB recording from the command line,
- render model-facing EEG/NE snapshot images,
- send those images plus scoring guidance to the OpenAI Responses API,
- parse structured Wake/REM intervals,
- write preview artifacts for review and presentation,
- serve as a clean starting point for future agent-model backends.

## Main Runtime Path

### 1. CLI entrypoint

`sleep_scoring_chatgpt/run_inference_chatgpt.py`

- loads one `.mat` recording,
- calls the ChatGPT inference backend,
- writes model input/output artifacts to an output directory,
- writes a JSON manifest of the run.

### 2. ChatGPT inference backend

`sleep_scoring_chatgpt/inference_chatgpt.py`

- validates backend readiness,
- loads the guidance prompt,
- optionally loads a structured reference-example pack,
- builds model-facing figures,
- runs either one overview call or fixed one-hour zoom-window calls,
- parses structured Responses API output,
- overlays accepted Wake/REM segments onto the score array,
- records per-call artifacts and optional thought traces, with top-level run settings plus per-call timing, token usage, cost estimate, and proposed segments.

### 3. ChatGPT helper layer

`sleep_scoring_chatgpt/chatgpt_tools.py`

- provides interval feature extraction,
- provides score slicing and score writeback helpers,
- provides snapshot capture helpers,
- holds helper contracts that may later be generalized for other agent-model backends.

### 4. Figure and spectral helpers

`sleep_scoring_chatgpt/make_figure.py`
- shared figure utilities and the fuller app-like export figure.

`sleep_scoring_chatgpt/make_figure_chatgpt.py`
- focused model-facing figure with spectrogram plus NE only.

`sleep_scoring_chatgpt/get_fft_plots.py`
- spectrogram and theta/delta helper used by the figure builders.

`sleep_scoring_chatgpt/config.py`
- current default model, reasoning effort, inference mode, internal refinement-window duration, and plotting settings.

### 5. Reference example pack

`sleep_scoring_chatgpt/sleep_scoring_examples/`

- stores the bundled reference-example JSON metadata,
- stores the model-facing overview and refinement PNGs used for calibration examples,
- intentionally avoids the older app-specific `assets/` nesting from the parent project.

## Current Naming Direction

The repo intentionally keeps `ChatGPT` in model-specific entrypoints such as `run_inference_chatgpt.py` and `inference_chatgpt.py`.

That naming is meant to leave room for future backends built around other agent models without forcing those future backends into ChatGPT-shaped module names.

## Output Artifacts

A typical run writes:

- input snapshot PNGs sent to the model,
- prediction-overlay PNGs,
- `model_output.json`,
- an optional thought trace markdown/text file with streamlined run-level settings and per-call request summaries.

The bundled reference example pack also ships with:

- `groundtruth_reasons.json`
- one overview PNG for `overview_only`
- three one-hour refinement PNGs for `fixed_windows`

## Input Expectations

Required `.mat` fields:

- `eeg`
- `eeg_frequency`
- `emg`

Optional fields:

- `ne`
- `ne_frequency`
- `sleep_scores`
- `start_time`
- `num_class`

## Tests

The current copied test coverage is focused on helper and figure behavior in:

- `tests/test_chatgpt_tools.py`
- `tests/test_inference_chatgpt.py`

These tests are useful smoke coverage for extraction regressions, renaming regressions, and reference-pack formatting behavior.

## Important Notes For Future Agents

- This repo was extracted from the `codex/chatgpt` branch of the parent `sleep_scoring` project.
- Keep behavior close to the original experiment unless a change is intentionally part of a new experiment.
- If you add another model backend later, prefer adding sibling modules such as `inference_<model>.py` and `run_inference_<model>.py` rather than erasing the ChatGPT-specific path.
- Avoid reintroducing Dash or pywebview dependencies unless the repo purpose changes.
