# sleep-scoring-chatgpt

Standalone backend-only extraction of the ChatGPT sleep-scoring preview workflow from the larger [`sleep_scoring` project (`codex/chatgpt` branch)](https://github.com/yzhaoinuw/sleep_scoring/tree/codex/chatgpt).

## Overview

This repository runs the experimental ChatGPT sleep-scoring pipeline on a single MATLAB recording without launching the Dash desktop app.

The current workflow:

- loads a `.mat` file containing EEG, EMG, and optional NE data,
- renders model-facing snapshot images,
- sends the scoring guidance plus images to the OpenAI Responses API,
- parses structured Wake and REM intervals from the model response,
- writes preview artifacts for inspection and presentation use.

The inference flow is intentionally limited to two modes:

- `overview_only`: score one full-recording overview image
- `fixed_windows`: score a sequence of fixed one-hour zoom windows

The scoring logic assumes the recording defaults to NREM and asks the model to identify only Wake and REM segments.

## Installation

```powershell
pip install -e .
pip install -e .[test]
```

Set your API key before running. The backend will honor either a shell environment variable or a project-local `.env` file:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
```

```env
OPENAI_API_KEY=your-api-key
```

## Usage

Run the backend on one recording:

```powershell
python -m sleep_scoring_chatgpt.run_inference_chatgpt .\path\to\recording.mat .\chatgpt_preview_outputs\recording --reasoning-effort medium --inference-mode fixed_windows
```

Or use the installed script:

```powershell
sleep-scoring-chatgpt .\path\to\recording.mat .\chatgpt_preview_outputs\recording
```

## Output

A typical run writes:

- model-facing input snapshot PNGs,
- prediction-overlay PNGs,
- `model_output.json` with model-call metadata,
- an optional thought trace file when thoughts are enabled.

## CLI parameters

- `mat_path`: input MATLAB file.
- `output_dir`: artifact output directory.
- `--model`: OpenAI model name. Default is `gpt-5.4`.
- `--reasoning-effort`: one of `none`, `minimal`, `low`, `medium`, `high`, `xhigh`.
- `--confidence-threshold`: minimum accepted segment confidence in `[0, 1]`.
- `--inference-mode`: `overview_only` or `fixed_windows`.
- `--vision-figure-mode`: `focused` or `full`.
- `--use-reference-examples`: attach the bundled reference example pack.
- `--no-thoughts`: disable the saved thought trace file.

The fixed zoom-window duration used by `fixed_windows` is an internal setting and is currently one hour.

## Input expectations

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

## Notes

- This repo preserves the original experimental module structure to keep behavior close to the source branch.
- It intentionally excludes the Dash UI, pywebview desktop shell, video features, and the learned-model inference paths from the full app.
