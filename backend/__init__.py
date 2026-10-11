"""StarIntel Auto Dig backend package."""

__all__ = ["app"]

def __getattr__(name):
    # Importing the document validation helper must not initialize the web
    # application or require its optional FastAPI dependencies.
    if name == "app":
        from .app import app
        globals()[name] = app
        return app
    raise AttributeError(name)
