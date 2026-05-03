"""Tests for reference-example prompt assembly."""

import json
from pathlib import Path
import shutil

from sleep_scoring_chatgpt.inference_chatgpt import (
    REFERENCE_EXAMPLE_DATA_FILENAME,
    REFERENCE_EXAMPLE_IMAGE_SPECS,
    _build_reference_examples_message,
    _build_zoom_section_request_input,
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
                "0-3600 s": [
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


def test_build_reference_examples_message_can_skip_overview_image():
    """Zoom-only mode should be able to omit the overview example cleanly."""
    temp_root = Path.cwd() / "_reference_examples_test_tmp"
    shutil.rmtree(temp_root, ignore_errors=True)

    try:
        reference_dir = temp_root / "sleep_scoring_examples"
        reference_dir.mkdir(parents=True)

        reference_payload = {
            "summary": "Ground-truth references for a calibration recording.",
            "conventions": ["Assume all unlabeled time is `NREM`."],
            "sections": {
                "0-3600 s": [
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

        message = _build_reference_examples_message(reference_dir, include_overview=False)

        assert message is not None
        assert len(message["content"]) == 3
        assert "Reference example pack:" in message["content"][0]["text"]
        assert "35_app13 reference zoom 0-3600 s." in message["content"][1]["text"]
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def test_build_zoom_section_request_input_includes_reference_examples_message():
    """Zoom-only inference should be able to prepend a zoom-only reference pack."""
    reference_examples_message = {
        "role": "user",
        "content": [{"type": "input_text", "text": "Reference example pack"}],
    }

    request_input = _build_zoom_section_request_input(
        guidance_prompt="guidance",
        image_data_url="data:image/png;base64,abc",
        interval_start_s=0,
        interval_end_s=10,
        section_reason="fixed 3600-second refinement window 1",
        reference_examples_message=reference_examples_message,
    )

    assert len(request_input) == 3
    assert request_input[0]["role"] == "system"
    assert request_input[1] == reference_examples_message
    assert request_input[2]["role"] == "user"
