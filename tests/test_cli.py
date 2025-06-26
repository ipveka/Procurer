import cli

def test_cli_entrypoint_exists():
    assert hasattr(cli, 'cli') 