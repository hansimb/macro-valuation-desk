from pathlib import Path

from src.lib.runtime_env import load_env_file


def test_load_env_file_sets_missing_values_and_preserves_existing(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# comment",
                "FRED_API_KEY=test-key",
                "DATABASE_URL=postgresql://loaded/from-file",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://already/set")

    load_env_file(env_file)

    assert "test-key" == __import__("os").environ["FRED_API_KEY"]
    assert "postgresql://already/set" == __import__("os").environ["DATABASE_URL"]


def test_load_env_file_is_noop_for_missing_file(tmp_path):
    missing_file = tmp_path / ".env"

    load_env_file(missing_file)

    assert not Path(missing_file).exists()
