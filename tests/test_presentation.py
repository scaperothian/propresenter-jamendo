from pathlib import Path
from propresenter_jamendo.presentation import pair_lines_with_timing, build_presentation

RAW_LINES = [
    {"start": 0.0, "end": 2.0, "text": "Line one\n"},
    {"start": 2.5, "end": 4.0, "text": "Line two\n"},
    {"start": 5.0, "end": 7.0, "text": "Line three\n"},
    {"start": 8.0, "end": 10.0, "text": "Line four\n"},
]


class TestPairLinesWithTiming:
    def test_groups_into_pairs(self):
        assert len(pair_lines_with_timing(RAW_LINES)) == 2

    def test_pair_text(self):
        pairs = pair_lines_with_timing(RAW_LINES)
        assert pairs[0]["text"] == "Line one\nLine two"
        assert pairs[1]["text"] == "Line three\nLine four"

    def test_start_time_from_first_line(self):
        pairs = pair_lines_with_timing(RAW_LINES)
        assert pairs[0]["start_time"] == 0.0
        assert pairs[1]["start_time"] == 5.0

    def test_stop_time_chains_to_next_start(self):
        pairs = pair_lines_with_timing(RAW_LINES)
        assert pairs[0]["stop_time"] == pairs[1]["start_time"]

    def test_last_stop_time_is_last_line_end(self):
        pairs = pair_lines_with_timing(RAW_LINES)
        assert pairs[-1]["stop_time"] == 10.0

    def test_skips_blank_lines(self):
        lines = [
            {"start": 0.0, "end": 1.0, "text": "Real\n"},
            {"start": 1.0, "end": 1.0, "text": "\n"},
            {"start": 2.0, "end": 3.0, "text": "Line\n"},
        ]
        pairs = pair_lines_with_timing(lines)
        assert len(pairs) == 1
        assert pairs[0]["text"] == "Real\nLine"

    def test_odd_number_of_lines(self):
        pairs = pair_lines_with_timing(RAW_LINES[:3])
        assert len(pairs) == 2
        assert pairs[-1]["text"] == "Line three"

    def test_empty_input(self):
        assert pair_lines_with_timing([]) == []


class TestBuildPresentation:
    SONG = {"title": "My Song", "lines": RAW_LINES}
    WAV = Path("/out/My Song.wav")

    def test_top_level_key(self):
        pres = build_presentation(self.SONG, self.WAV, index=0)
        assert "presentation" in pres

    def test_id_fields(self):
        pres = build_presentation(self.SONG, self.WAV, index=3)
        pid = pres["presentation"]["id"]
        assert pid["name"] == "My Song"
        assert pid["index"] == 3
        assert pid["audio"] == "/out/My Song.wav"
        assert len(pid["uuid"]) == 36

    def test_uuid_is_uppercase(self):
        pid = build_presentation(self.SONG, self.WAV, index=0)["presentation"]["id"]
        assert pid["uuid"] == pid["uuid"].upper()

    def test_slide_count(self):
        slides = build_presentation(self.SONG, self.WAV, index=0)["presentation"]["groups"][0]["slides"]
        assert len(slides) == 2

    def test_slide_structure(self):
        slide = build_presentation(self.SONG, self.WAV, index=0)["presentation"]["groups"][0]["slides"][0]
        assert slide["enabled"] is True
        assert slide["notes"] == ""
        assert slide["label"] == ""
        assert slide["size"] == {"width": 1920, "height": 1080}
        assert "start time" in slide
        assert "stop time" in slide

    def test_slide_timing(self):
        slides = build_presentation(self.SONG, self.WAV, index=0)["presentation"]["groups"][0]["slides"]
        assert slides[0]["start time"] == 0.0
        assert slides[0]["stop time"] == slides[1]["start time"]

    def test_has_timeline_and_destination(self):
        p = build_presentation(self.SONG, self.WAV, index=0)["presentation"]
        assert p["has_timeline"] is False
        assert p["destination"] == "presentation"

    def test_group_defaults(self):
        group = build_presentation(self.SONG, self.WAV, index=0)["presentation"]["groups"][0]
        assert group["name"] == ""
        assert group["color"] is None
