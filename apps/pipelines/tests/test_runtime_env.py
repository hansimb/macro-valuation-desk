from pathlib import Path

from src.lib.runtime_env import load_env_file, load_project_env


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


def test_load_project_env_looks_in_repo_root(monkeypatch):
    loaded_paths: list[Path] = []

    monkeypatch.setattr(
        "src.lib.runtime_env.load_env_file",
        lambda path: loaded_paths.append(path),
    )

    load_project_env()

    assert loaded_paths[0].name == ".env"
    assert loaded_paths[0].parent.name == "macro-valuation-desk"
    assert loaded_paths[1].as_posix().endswith("macro-valuation-desk/infra/compose/.env")
