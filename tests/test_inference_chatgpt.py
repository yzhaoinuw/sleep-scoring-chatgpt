"""Tests for reference-example prompt assembly."""

import json
from pathlib import Path
import shutil

from sleep_scoring_chatgpt.inference_chatgpt import (
    REFERENCE_EXAMPLE_DATA_FILENAME,
    REFERENCE_EXAMPLE_IMAGE_SPECS,
    _build_reference_examples_message,
)


def test_build_reference_examples_message_reads_structured_json():
    """Reference examples should load from JSON and format notes per image window."""
    temp_root = Path.cwd() / "_reference_examples_test_tmp"
    shutil.rmtree(temp_root, ignore_errors=True)

    try:
        reference_dir = temp_root / "sleep_scoring_examples"
        reference_dir.mkdir(parents=True)

        reference_payload = {
            "summary": "Ground-truth references for a calibration recording.",
            "conventions": [
                "Assume all unlabeled time is `NREM`.",
                "Entries are listed in time order.",
            ],
            "sections": {
                "0-2575 s": [
                    {
                        "index": "01",
                        "state": "Wake",
                        "timing": "approx 300 s",
                        "reason": "brief wake interruption.",
                    }
                ]
            },
        }
        (reference_dir / REFERENCE_EXAMPLE_DATA_FILENAME).write_text(
            json.dumps(reference_payload, indent=2) + "\n",
            encoding="utf-8",
        )

        for filename, _label, _description in REFERENCE_EXAMPLE_IMAGE_SPECS[:2]:
            (reference_dir / filename).write_bytes(b"not-a-real-png")

        message = _build_reference_examples_message(reference_dir)

        assert message is not None
        assert message["role"] == "user"
        assert len(message["content"]) == 5
        assert "Reference example pack:" in message["content"][0]["text"]
        assert "Conventions" in message["content"][0]["text"]
        assert "- Assume all unlabeled time is `NREM`." in message["content"][0]["text"]
        assert "35_app13 reference overview." in message["content"][1]["text"]
        assert "Matching labeled bouts and reasons:" in message["content"][3]["text"]
        assert "[01] `Wake` | approx 300 s | brief wake interruption." in message["content"][3]["text"]
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
