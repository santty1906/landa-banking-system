from app.main import create_app


def test_create_app_loads_core_metadata():
    app = create_app()

    assert app.title == "Landa Backend API"
    assert app.version == "0.1.0"
