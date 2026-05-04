"""Tests for reference-example prompt assembly."""

import json
import os
from pathlib import Path
import shutil

import numpy as np

from sleep_scoring_chatgpt.inference_chatgpt import (
    _TraceLogger,
    REFERENCE_EXAMPLE_DATA_FILENAME,
    REFERENCE_EXAMPLE_IMAGE_SPECS,
    _build_reference_examples_message,
    _build_zoom_section_request_input,
    _load_local_env_file,
    _request_structured_scoring,
    infer,
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


def test_load_local_env_file_reads_openai_api_key_without_overriding_shell_env(monkeypatch):
    """Local .env loading should set the key only when the shell has not set one."""
    temp_root = Path.cwd() / "_dotenv_test_tmp"
    shutil.rmtree(temp_root, ignore_errors=True)

    try:
        dotenv_path = temp_root / ".env"
        temp_root.mkdir(parents=True)
        dotenv_path.write_text(
            '# Local API key for testing\nOPENAI_API_KEY="dotenv-key"\n',
            encoding="utf-8",
        )

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        _load_local_env_file(dotenv_path)
        assert os.environ["OPENAI_API_KEY"] == "dotenv-key"

        monkeypatch.setenv("OPENAI_API_KEY", "shell-key")
        dotenv_path.write_text("OPENAI_API_KEY=updated-dotenv-key\n", encoding="utf-8")
        _load_local_env_file(dotenv_path)
        assert os.environ["OPENAI_API_KEY"] == "shell-key"
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def test_overview_only_fills_unlabeled_time_as_nrem(monkeypatch):
    """Overview-only inference should seed the full recording as NREM."""
    def _fake_capture_overview_snapshot(_figure, output_path):
        output_path = Path(output_path)
        output_path.write_bytes(b"png")
        return output_path

    monkeypatch.setattr(
        "sleep_scoring_chatgpt.inference_chatgpt._load_guidance_prompt",
        lambda _path: "guidance",
    )
    monkeypatch.setattr(
        "sleep_scoring_chatgpt.inference_chatgpt._build_model_figure",
        lambda **_kwargs: object(),
    )
    monkeypatch.setattr(
        "sleep_scoring_chatgpt.inference_chatgpt.capture_overview_snapshot",
        _fake_capture_overview_snapshot,
    )
    monkeypatch.setattr(
        "sleep_scoring_chatgpt.inference_chatgpt._image_path_to_data_url",
        lambda _image_path: "data:image/png;base64,abc",
    )
    monkeypatch.setattr(
        "sleep_scoring_chatgpt.inference_chatgpt._request_structured_scoring",
        lambda **_kwargs: {"segments": []},
    )

    mat = {
        "eeg": np.zeros(10, dtype=float),
        "eeg_frequency": 1.0,
    }

    temp_root = Path.cwd() / "_overview_infer_test_tmp"
    shutil.rmtree(temp_root, ignore_errors=True)

    try:
        predictions, confidence = infer(
            mat=mat,
            client=object(),
            snapshot_dir=temp_root,
            show_thoughts=False,
            inference_mode="overview_only",
            use_reference_examples=False,
        )

        assert np.all(predictions == 1)
        assert np.all(confidence == 1.0)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def test_request_structured_scoring_logs_elapsed_seconds(monkeypatch):
    """Thought traces should include per-request elapsed time without re-listing global settings."""

    class _FakeResponses:
        def create(self, **_kwargs):
            return object()

    class _FakeClient:
        responses = _FakeResponses()

    monkeypatch.setattr(
        "sleep_scoring_chatgpt.inference_chatgpt._extract_response_payload",
        lambda _response: {"segments": []},
    )
    monkeypatch.setattr(
        "sleep_scoring_chatgpt.inference_chatgpt._extract_response_usage",
        lambda _response: None,
    )
    monkeypatch.setattr(
        "sleep_scoring_chatgpt.inference_chatgpt._estimate_response_cost_usd",
        lambda _model_name, _usage: None,
    )
    perf_counter_values = iter([10.0, 11.234])
    monkeypatch.setattr(
        "sleep_scoring_chatgpt.inference_chatgpt.perf_counter",
        lambda: next(perf_counter_values),
    )

    temp_root = Path.cwd() / "_request_timing_test_tmp"
    shutil.rmtree(temp_root, ignore_errors=True)

    try:
        temp_root.mkdir(parents=True)
        trace_path = temp_root / "thoughts.txt"
        trace_logger = _TraceLogger(enabled=True, path=trace_path)

        payload = _request_structured_scoring(
            client=_FakeClient(),
            model_name="gpt-5.4",
            request_input=[],
            reasoning_effort="medium",
            trace_logger=trace_logger,
            trace_label="Overview Pass",
        )
        trace_logger.save()

        trace_text = trace_path.read_text(encoding="utf-8")
        assert payload == {"segments": []}
        assert "- elapsed_seconds: 1.23" in trace_text
        assert "- reasoning_effort:" not in trace_text
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
