# sleep-scoring-chatgpt

Standalone backend-only extraction of the ChatGPT sleep-scoring preview workflow from the `sleep_scoring` project.

## What it does

This package runs the experimental ChatGPT inference flow on a single MATLAB recording without launching the Dash desktop app. It:

- loads a `.mat` file containing EEG, EMG, and optional NE data,
- renders model-facing Plotly snapshot images,
- sends the guidance prompt plus images to the OpenAI Responses API,
- parses structured Wake and REM segments,
- writes preview artifacts including input images, prediction-overlay images, a JSON call log, and an optional thought trace.

The workflow assumes the recording defaults to NREM and asks the model to mark only Wake and REM intervals.

## Installation

```powershell
pip install -e .
pip install -e .[test]
```

Set your API key before running:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
```

## Usage

```powershell
python -m sleep_scoring_chatgpt.run_inference_chatgpt .\path\to\recording.mat .\chatgpt_preview_outputs\recording --reasoning-effort medium --refinement-mode fixed_sections --fixed-section-count 4
```

Or use the installed script:

```powershell
sleep-scoring-chatgpt .\path\to\recording.mat .\chatgpt_preview_outputs\recording
```

## CLI parameters

- `mat_path`: input MATLAB file.
- `output_dir`: artifact output directory.
- `--model`: OpenAI model name. Default is `gpt-5.4`.
- `--reasoning-effort`: one of `none`, `minimal`, `low`, `medium`, `high`, `xhigh`.
- `--confidence-threshold`: minimum accepted segment confidence in `[0, 1]`.
- `--refinement-mode`: `none`, `adaptive`, or `fixed_sections`.
- `--fixed-section-count`: number of fixed zoom sections when using `fixed_sections`.
- `--vision-figure-mode`: `focused` or `full`.
- `--use-overview-pass`: add a full-recording overview pass before zoomed scoring.
- `--use-reference-examples`: attach the bundled reference example pack.
- `--no-thoughts`: disable the saved thought trace file.

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
