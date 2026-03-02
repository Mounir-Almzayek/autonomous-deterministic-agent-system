"""
Phase 1: Intent Parser unit tests.
"""
import pytest

from app.core.intent_parser import parse
from app.models import ActionType, IntentParserResult, ParsedIntent


def test_parse_valid_json():
    raw = '{"action_type":"execute","params":{"ticker":"AAPL","qty":100},"summary":"Buy 100 AAPL"}'
    result = parse(raw)
    assert result.success is True
    assert result.intent is not None
    assert result.intent.action_type == ActionType.EXECUTE
    assert result.intent.params == {"ticker": "AAPL", "qty": 100}
    assert "Buy" in result.intent.summary


def test_parse_valid_with_code_block():
    raw = '```json\n{"action_type":"query","params":{},"summary":"test"}\n```'
    result = parse(raw)
    assert result.success is True
    assert result.intent is not None
    assert result.intent.action_type == ActionType.QUERY


def test_parse_empty_fails():
    result = parse("")
    assert result.success is False
    assert result.error is not None
    assert result.error.error_code == "EMPTY_INPUT"


def test_parse_whitespace_only_fails():
    result = parse("   \n\t  ")
    assert result.success is False
    assert result.error is not None


def test_parse_invalid_json_fails():
    result = parse("not json at all")
    assert result.success is False
    assert result.error is not None
    assert "JSON" in result.error.error_code or "json" in result.error.message.lower()


def test_parse_root_not_object_fails():
    result = parse("[1,2,3]")
    assert result.success is False
    assert result.error is not None
    assert "object" in result.error.message.lower() or "ROOT" in result.error.error_code


def test_parse_missing_action_type_fails():
    result = parse('{"params":{},"summary":"x"}')
    assert result.success is False
    assert result.error is not None
    assert "action_type" in result.error.error_code or "action_type" in result.error.message


def test_parse_action_type_normalized():
    result = parse('{"action_type":"EXECUTE","params":{},"summary":""}')
    assert result.success is True
    assert result.intent.action_type == ActionType.EXECUTE


def test_parse_trade_alias_maps_to_execute():
    result = parse('{"action_type":"trade","params":{},"summary":""}')
    assert result.success is True
    assert result.intent.action_type == ActionType.EXECUTE


def test_parse_correlation_id_passed():
    result = parse('{"action_type":"query","params":{},"summary":""}', correlation_id="trace-99")
    assert result.success is True
    assert result.intent is not None
    assert result.intent.correlation_id == "trace-99"


def test_parse_invalid_input_type_fails():
    result = parse(123)  # type: ignore
    assert result.success is False
    assert result.error is not None
    assert "string" in result.error.message.lower() or "type" in result.error.message.lower()


def test_parse_params_must_be_object():
    result = parse('{"action_type":"query","params":"not-dict","summary":""}')
    assert result.success is False
    assert result.error is not None
