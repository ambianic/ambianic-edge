"""Test configuration functions."""
import logging
import logging.handlers
import os

from ambianic.util import jsonify

log = logging.getLogger(__name__)

_dir = os.path.dirname(os.path.abspath(__file__))


def setup_module(module):
    """setup any state specific to the execution of the given module."""


def test_jsonify_none():
    """Coverage for bug report: https://github.com/ambianic/ambianic-ui/issues/774"""
    val = {"a": None}
    json_str = jsonify(val)
    assert "None" not in json_str
    assert json_str == '{"a": null}'
