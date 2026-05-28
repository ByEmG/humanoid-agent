"""Tests for AgentBrain — only the parsing/deterministic parts (no live API calls)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from agent.actions import ActionType
from agent.brain import AgentBrain


def make_brain(tmp_path):
    return AgentBrain(model="claude-test", api_key="sk-test",
                      log_file=str(tmp_path / "test_log.txt"))


def test_parse_well_formed_response(tmp_path):
    brain = make_brain(tmp_path)
    text = (
        "REASONING: I can see the goal to the east, I should move forward.\n"
        "ACTION: MOVE_FORWARD\n"
        "CONFIDENCE: HIGH"
    )
    reasoning, action, confidence = brain._parse_response(text)
    assert "east" in reasoning.lower()
    assert action == ActionType.MOVE_FORWARD
    assert confidence == "HIGH"


def test_parse_action_case_insensitive(tmp_path):
    brain = make_brain(tmp_path)
    text = "REASONING: ok\nACTION: turn_left\nCONFIDENCE: medium"
    _, action, confidence = brain._parse_response(text)
    assert action == ActionType.TURN_LEFT
    assert confidence == "MEDIUM"


def test_parse_alias_action(tmp_path):
    brain = make_brain(tmp_path)
    text = "REASONING: need key\nACTION: PICK\nCONFIDENCE: HIGH"
    _, action, _ = brain._parse_response(text)
    assert action == ActionType.PICK_UP


def test_parse_unknown_action_falls_back_to_wait(tmp_path):
    brain = make_brain(tmp_path)
    text = "REASONING: unclear\nACTION: FLY\nCONFIDENCE: LOW"
    _, action, _ = brain._parse_response(text)
    assert action == ActionType.WAIT


def test_parse_missing_fields_fall_back(tmp_path):
    brain = make_brain(tmp_path)
    text = "I have no idea what to do."
    reasoning, action, confidence = brain._parse_response(text)
    assert action == ActionType.WAIT
    assert confidence == "LOW"


def test_record_action_result(tmp_path):
    brain = make_brain(tmp_path)
    brain.record_action_result(ActionType.MOVE_FORWARD, "Moved to (3,3)")
    assert len(brain.memory) == 1
    assert "MOVE_FORWARD" in brain.memory[0]


def test_memory_capped_at_20(tmp_path):
    brain = make_brain(tmp_path)
    for i in range(25):
        brain.record_action_result(ActionType.WAIT, f"step {i}")
    assert len(brain.memory) == 20


def test_log_file_created(tmp_path):
    brain = make_brain(tmp_path)
    log = tmp_path / "test_log.txt"
    assert log.exists()
    assert "Session Log" in log.read_text()
