"""Integration tests for Typer CLI commands."""

from typer.testing import CliRunner
from betteragy import __version__
from betteragy.cli import app

runner = CliRunner()


def test_cli_help():
    res = runner.invoke(app, ["--help"])
    assert res.exit_code == 0
    assert "Rich CLI Switchboard & AI Token Analytics" in res.stdout
    assert "quota" in res.stdout
    assert "usage" in res.stdout
    assert "account" in res.stdout


def test_cli_account_help():
    res = runner.invoke(app, ["account", "--help"])
    assert res.exit_code == 0
    assert "list" in res.stdout
    assert "switch" in res.stdout
    assert "rotate" in res.stdout


def test_cli_usage_help():
    res = runner.invoke(app, ["usage", "--help"])
    assert res.exit_code == 0
    assert "models" in res.stdout


def test_cli_quota_help():
    res = runner.invoke(app, ["quota", "--help"])
    assert res.exit_code == 0
    assert "--all" in res.stdout
    assert "--watch" in res.stdout


def test_cli_shell():
    res = runner.invoke(app, ["shell"])
    assert res.exit_code == 0
    assert "agy()" in res.stdout
    assert "agycool()" in res.stdout


def test_cli_version_flag():
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert f"betteragy version {__version__}" in res.stdout


def test_cli_version_command():
    res = runner.invoke(app, ["version"])
    assert res.exit_code == 0
    assert f"betteragy version {__version__}" in res.stdout


def test_cli_setup_help():
    res = runner.invoke(app, ["setup", "--help"])
    assert res.exit_code == 0
    assert "onboarding wizard" in res.stdout

