import api

def test_api_app_exists():
    assert hasattr(api, 'app')
    assert hasattr(api.app, 'routes') 