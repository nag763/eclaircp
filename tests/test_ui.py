"""
Tests for the UI components module.
"""

import pytest
from eclaircp.ui import StreamingDisplay, ServerSelector, StatusDisplay


def test_streaming_display_initialization():
    """Test StreamingDisplay initialization."""
    display = StreamingDisplay()
    assert display is not None


def test_server_selector_initialization():
    """Test ServerSelector initialization."""
    selector = ServerSelector()
    assert selector is not None


def test_status_display_initialization():
    """Test StatusDisplay initialization."""
    status = StatusDisplay()
    assert status is not None


def test_stream_text_not_implemented():
    """Test that stream_text raises NotImplementedError."""
    display = StreamingDisplay()
    with pytest.raises(NotImplementedError):
        display.stream_text("test")