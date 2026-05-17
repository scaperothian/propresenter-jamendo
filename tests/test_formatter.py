import pytest
from propresenter_jamendo.formatter import format_lyrics, safe_filename


class TestFormatLyrics:
    def test_even_number_of_lines(self):
        lines = ["Line 1", "Line 2", "Line 3", "Line 4"]
        result = format_lyrics(lines)
        assert result == "Line 1\nLine 2\n\nLine 3\nLine 4\n"

    def test_odd_number_of_lines(self):
        lines = ["Line 1", "Line 2", "Line 3"]
        result = format_lyrics(lines)
        assert result == "Line 1\nLine 2\n\nLine 3\n"

    def test_single_line(self):
        lines = ["Only line"]
        result = format_lyrics(lines)
        assert result == "Only line\n"

    def test_empty_lines_stripped(self):
        lines = ["Line 1", "", "Line 2", "  ", "Line 3", "Line 4"]
        result = format_lyrics(lines)
        assert result == "Line 1\nLine 2\n\nLine 3\nLine 4\n"

    def test_lines_with_trailing_newlines(self):
        lines = ["Line 1\n", "Line 2\n"]
        result = format_lyrics(lines)
        assert result == "Line 1\nLine 2\n"

    def test_empty_input(self):
        assert format_lyrics([]) == "\n"

    def test_all_blank_lines(self):
        assert format_lyrics(["", "  ", "\t"]) == "\n"


class TestSafeFilename:
    def test_normal_title(self):
        assert safe_filename("Give Me the Same") == "Give Me the Same"

    def test_strips_forbidden_characters(self):
        assert safe_filename('Song: "A/B"') == "Song AB"

    def test_strips_leading_trailing_dots_and_spaces(self):
        assert safe_filename("  . song .  ") == "song"

    def test_empty_title_returns_untitled(self):
        assert safe_filename("") == "untitled"

    def test_title_only_forbidden_chars(self):
        assert safe_filename('/:*?"<>|\\') == "untitled"
