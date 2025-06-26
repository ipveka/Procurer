import cli

def test_cli_entrypoint_exists():
    """
    Test that the CLI entrypoint exists in the cli module.
    Ensures the CLI interface is exposed for command-line use.
    """
    assert hasattr(cli, 'cli') 