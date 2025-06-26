import api

def test_api_app_exists():
    """
    Test that the FastAPI app object exists and has routes defined.
    Ensures the API module exposes the expected app for serving.
    """
    assert hasattr(api, 'app')
    assert hasattr(api.app, 'routes') 