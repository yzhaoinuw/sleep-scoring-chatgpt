"""Rebuild a MATLAB file with ChatGPT sleep scores from model_output.json."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import loadmat, savemat

from sleep_scoring_chatgpt.chatgpt_tools import SLEEP_STAGE_TO_SCORE


DEFAULT_CONFIDENCE_THRESHOLD = 0.0
DEFAULT_NREM_CONFIDENCE = 1.0
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _scalar_value(value: Any, default: float = 0.0) -> float:
    """Return a float for MATLAB-loaded scalar values or a default."""
    if value is None:
        return float(default)

    array = np.asarray(value)
    if array.size == 0:
        return float(default)

    return float(array.reshape(-1)[0])


def _get_recording_window(mat: dict[str, Any]) -> tuple[float, int]:
    """Return the recording start time and integer duration in seconds."""
    eeg = np.asarray(mat.get("eeg"))
    eeg_frequency = _scalar_value(mat.get("eeg_frequency"))
    if eeg.size == 0:
        raise ValueError("Source MAT must contain non-empty `eeg` data.")
    if eeg_frequency <= 0:
        raise ValueError("Source MAT must contain a positive `eeg_frequency`.")

    start_s = _scalar_value(mat.get("start_time"), default=0.0)
    duration_s = math.ceil((eeg.size - 1) / eeg_frequency)
    return start_s, duration_s


def _normalize_interval_indices(
    start_s: Any,
    end_s: Any,
    *,
    recording_start_s: float,
    duration_s: int,
) -> tuple[int, int]:
    """Convert absolute-second bounds into clamped array indices."""
    start_idx = max(0, int(math.floor(float(start_s) - recording_start_s)))
    end_idx = min(duration_s, int(math.ceil(float(end_s) - recording_start_s)))

    if end_idx <= start_idx:
        raise ValueError("Interval must span at least one second within the recording.")

    return start_idx, end_idx


def _iter_segments(model_output: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all saved segments from a model_output payload."""
    collected_segments: list[dict[str, Any]] = []

    for model_call in model_output.get("model_calls", []):
        segments = model_call.get("normalized_segments")
        if not isinstance(segments, list):
            payload = model_call.get("payload", {})
            segments = payload.get("segments", []) if isinstance(payload, dict) else []

        for segment in segments:
            if isinstance(segment, dict):
                collected_segments.append(segment)

    collected_segments.sort(
        key=lambda segment: (
            float(segment.get("start_s", 0)),
            float(segment.get("end_s", 0)),
        )
    )
    return collected_segments


def reconstruct_scores_from_model_output(
    model_output: dict[str, Any],
    source_mat: dict[str, Any],
    *,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> tuple[np.ndarray, np.ndarray]:
    """Rebuild per-second sleep scores and confidence arrays from model output."""
    threshold = float(confidence_threshold)
    if not np.isfinite(threshold):
        raise ValueError("confidence_threshold must be finite.")

    recording_start_s, duration_s = _get_recording_window(source_mat)
    predictions = np.full(duration_s, SLEEP_STAGE_TO_SCORE["NREM"], dtype=float)
    confidence = np.full(duration_s, DEFAULT_NREM_CONFIDENCE, dtype=float)

    for segment in _iter_segments(model_output):
        state = segment.get("state")
        if state not in SLEEP_STAGE_TO_SCORE:
            raise ValueError(f"Unsupported sleep state in model output: {state!r}.")

        segment_confidence = float(segment.get("confidence", np.nan))
        if not np.isfinite(segment_confidence):
            raise ValueError("Segment confidence must be finite.")
        if segment_confidence < threshold:
            continue

        start_idx, end_idx = _normalize_interval_indices(
            segment["start_s"],
            segment["end_s"],
            recording_start_s=recording_start_s,
            duration_s=duration_s,
        )
        predictions[start_idx:end_idx] = SLEEP_STAGE_TO_SCORE[state]
        confidence[start_idx:end_idx] = segment_confidence

    return predictions, confidence


def _sanitize_mat_payload(source_mat: dict[str, Any]) -> dict[str, Any]:
    """Drop loadmat bookkeeping keys before writing a new MAT file."""
    return {
        key: value
        for key, value in source_mat.items()
        if not (key.startswith("__") or key.startswith("_"))
    }


def export_prediction_mat(
    model_output_json_path: str | Path,
    output_mat_path: str | Path,
    *,
    source_mat_path: str | Path | None = None,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> dict[str, Any]:
    """Write a MATLAB file that includes reconstructed ChatGPT sleep scores."""
    model_output_json_path = Path(model_output_json_path).expanduser().resolve()
    output_mat_path = Path(output_mat_path).expanduser().resolve()

    model_output = json.loads(model_output_json_path.read_text(encoding="utf-8"))
    json_mat_path = model_output.get("mat_path")
    if source_mat_path is None:
        if not json_mat_path:
            raise ValueError("model_output.json does not contain `mat_path`.")
        source_mat_path = json_mat_path

    source_mat_path = Path(source_mat_path).expanduser().resolve()
    source_mat = loadmat(source_mat_path, squeeze_me=True)
    predictions, confidence = reconstruct_scores_from_model_output(
        model_output,
        source_mat,
        confidence_threshold=confidence_threshold,
    )

    export_payload = _sanitize_mat_payload(loadmat(source_mat_path))
    export_payload["sleep_scores"] = predictions.reshape(-1, 1)
    export_payload["confidence"] = confidence.reshape(-1, 1)

    output_mat_path.parent.mkdir(parents=True, exist_ok=True)
    savemat(output_mat_path, export_payload)

    return {
        "model_output_json_path": str(model_output_json_path),
        "source_mat_path": str(source_mat_path),
        "output_mat_path": str(output_mat_path),
        "num_scores": int(predictions.size),
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a MAT file with ChatGPT sleep scores rebuilt from model_output.json."
    )
    parser.add_argument("model_output_json_path", help="Path to model_output.json.")
    parser.add_argument("output_mat_path", help="Path where the rebuilt MAT file will be written.")
    parser.add_argument(
        "--mat-path",
        default=None,
        help="Optional override for the source MAT path. Defaults to `mat_path` in model_output.json.",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=DEFAULT_CONFIDENCE_THRESHOLD,
        help="Minimum segment confidence to apply when rebuilding sleep scores.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    result = export_prediction_mat(
        args.model_output_json_path,
        args.output_mat_path,
        source_mat_path=args.mat_path,
        confidence_threshold=args.confidence_threshold,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raise SystemExit(main())

    # Spyder-friendly direct-run settings. Edit these local overrides, then press Run.
    output_dir = PROJECT_ROOT / "chatgpt_preview_outputs" / "COM5_bin1_gpt5.5_medium"
    model_output_json_path = output_dir / "model_output.json"
    output_mat_path = output_dir / "prediction_scores.mat"

    # Optional source MAT override. Set to ``None`` to use ``mat_path`` from model_output.json.
    source_mat_path = None

    # Minimum accepted segment confidence in [0, 1] for this direct-run export.
    confidence_threshold = 0.0

    result = export_prediction_mat(
        model_output_json_path=model_output_json_path,
        output_mat_path=output_mat_path,
        source_mat_path=source_mat_path,
        confidence_threshold=confidence_threshold,
    )
    print("Prediction MAT export complete.")
    print(f"Model output JSON: {result['model_output_json_path']}")
    print(f"Source MAT: {result['source_mat_path']}")
    print(f"Output MAT: {result['output_mat_path']}")
    print(f"Scores written: {result['num_scores']}")
