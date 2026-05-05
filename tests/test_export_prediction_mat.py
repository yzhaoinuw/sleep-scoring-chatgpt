"""Tests for rebuilding MATLAB files from model_output.json."""

import json
import shutil
from pathlib import Path

import numpy as np
from scipy.io import loadmat, savemat

from sleep_scoring_chatgpt.export_prediction_mat import (
    export_prediction_mat,
    reconstruct_scores_from_model_output,
)


def test_reconstruct_scores_from_model_output_uses_nrem_baseline_and_segments():
    model_output = {
        "model_calls": [
            {
                "normalized_segments": [
                    {
                        "start_s": 2,
                        "end_s": 4,
                        "state": "Wake",
                        "confidence": 0.7,
                    },
                    {
                        "start_s": 6,
                        "end_s": 8,
                        "state": "REM",
                        "confidence": 0.9,
                    },
                ]
            }
        ]
    }
    source_mat = {
        "eeg": np.zeros(10, dtype=float),
        "eeg_frequency": 1.0,
    }

    predictions, confidence = reconstruct_scores_from_model_output(model_output, source_mat)

    np.testing.assert_array_equal(predictions, np.array([1, 1, 0, 0, 1, 1, 2, 2, 1]))
    np.testing.assert_array_equal(confidence, np.array([1.0, 1.0, 0.7, 0.7, 1.0, 1.0, 0.9, 0.9, 1.0]))


def test_export_prediction_mat_writes_sleep_scores_and_confidence():
    temp_root = Path.cwd() / "_export_prediction_mat_tmp"
    shutil.rmtree(temp_root, ignore_errors=True)

    try:
        temp_root.mkdir(parents=True)
        source_mat_path = temp_root / "source.mat"
        output_mat_path = temp_root / "prediction.mat"
        model_output_path = temp_root / "model_output.json"

        savemat(
            source_mat_path,
            {
                "eeg": np.zeros((1, 10), dtype=float),
                "emg": np.zeros((1, 10), dtype=float),
                "eeg_frequency": np.array([[1.0]]),
            },
        )
        model_output_path.write_text(
            json.dumps(
                {
                    "mat_path": str(source_mat_path),
                    "model_calls": [
                        {
                            "payload": {
                                "segments": [
                                    {
                                        "start_s": 0,
                                        "end_s": 2,
                                        "state": "Wake",
                                        "confidence": 0.55,
                                    },
                                    {
                                        "start_s": 4,
                                        "end_s": 6,
                                        "state": "REM",
                                        "confidence": 0.95,
                                    },
                                ]
                            }
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        export_prediction_mat(model_output_path, output_mat_path, confidence_threshold=0.6)
        written_mat = loadmat(output_mat_path, squeeze_me=True)

        np.testing.assert_array_equal(written_mat["sleep_scores"], np.array([1, 1, 1, 1, 2, 2, 1, 1, 1]))
        np.testing.assert_array_equal(written_mat["confidence"], np.array([1.0, 1.0, 1.0, 1.0, 0.95, 0.95, 1.0, 1.0, 1.0]))
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
