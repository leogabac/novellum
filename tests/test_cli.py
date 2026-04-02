from pathlib import Path
import io
from contextlib import redirect_stdout

from novellum.cli import main


def test_init_command_creates_workspace(tmp_path: Path) -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["init", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / ".novellum" / "config.toml").exists()


def test_new_and_list_commands_work_in_workspace(tmp_path: Path) -> None:
    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    new_output = io.StringIO()
    list_output = io.StringIO()
    with redirect_stdout(new_output):
        new_exit_code = main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])
    with redirect_stdout(list_output):
        list_exit_code = main(["list", "--cwd", str(tmp_path)])

    assert new_exit_code == 0
    assert list_exit_code == 0
    assert "spectral-gap" in list_output.getvalue()

