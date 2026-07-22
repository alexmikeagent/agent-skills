from pathlib import Path

from uipath_tooling.line_endings import detect, detect_bytes, normalize


def test_detects_mixed_line_endings() -> None:
    assert detect_bytes(b"one\r\ntwo\n") == "mixed"
    assert detect_bytes(b"one\r\ntwo\r\n") == "crlf"


def test_normalization_is_check_only_until_write(valid_project: Path) -> None:
    path = valid_project / "Main.xaml"
    original = path.read_bytes()
    changes = normalize(valid_project, [path], write=False)
    assert path.read_bytes() == original
    if changes:
        normalize(valid_project, [path], write=True)
        assert detect(path) in {"lf", "crlf"}
