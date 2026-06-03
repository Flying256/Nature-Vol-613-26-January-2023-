import os
import subprocess
import sys


def test_train_entrypoint_refuses_to_train_without_explicit_confirmation():
    env = os.environ.copy()
    env.pop("NATURE613_ALLOW_TRAINING", None)

    result = subprocess.run(
        [sys.executable, "scripts/train_entrypoint.py", "--dry-run"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "NATURE613_ALLOW_TRAINING=1" in result.stderr


def test_train_entrypoint_dry_run_passes_when_confirmation_is_set():
    env = os.environ.copy()
    env["NATURE613_ALLOW_TRAINING"] = "1"

    result = subprocess.run(
        [sys.executable, "scripts/train_entrypoint.py", "--dry-run"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "dry run" in result.stdout.lower()
