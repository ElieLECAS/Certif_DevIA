def test_app_title():
    from app import app
    assert app.title == "Chatbot SAV"

def test_cors_middleware_configured():
    from app import app
    from fastapi.middleware.cors import CORSMiddleware
    assert any(m.cls is CORSMiddleware for m in app.user_middleware)

def test_static_files_mounted():
    from app import app
    from fastapi.staticfiles import StaticFiles
    assert any(isinstance(r.app, StaticFiles) and r.path == "/static" for r in app.routes)
