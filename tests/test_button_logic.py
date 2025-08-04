"""Test button click logic patterns."""

import pytest
from unittest.mock import Mock


class TestButtonLogic:
    """Test suite for button click logic patterns."""

    def test_button_value_none(self):
        """Test button with None value."""
        button = Mock()
        button.value = None

        # Should not trigger
        assert not (button and button.value)

    def test_button_value_zero(self):
        """Test button with zero value (not clicked)."""
        button = Mock()
        button.value = 0

        # Should not trigger
        assert not (button and button.value)

    def test_button_value_positive(self):
        """Test button with positive value (clicked)."""
        button = Mock()
        button.value = 1

        # Should trigger
        assert button and button.value

    def test_button_is_none(self):
        """Test when button itself is None."""
        button = None

        # Should not trigger and not raise error
        assert not (button and button.value)

    def test_old_pattern_fails_with_none(self):
        """Test that old pattern raises TypeError with None."""
        button = Mock()
        button.value = None

        # Old pattern would raise TypeError
        with pytest.raises(TypeError):
            _ = button.value > 0

    def test_new_pattern_safe_with_none(self):
        """Test that new pattern is safe with None."""
        button = Mock()
        button.value = None

        # New pattern is safe
        result = button and button.value
        assert not result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
