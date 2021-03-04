from functools import wraps
from xepmts.web_client.src.shared._db import get_db
import panel as pn

def login_required(state, requires_db=True):
    def decorator(view):
        @wraps(view)
        def wrapper():
            db = state.as_cached(state.curdoc.session_context.id, get_db)
            if requires_db:
                template = view(db)
            else:
                template = view()
            if db.logged_in:
                return template
            else:
                message = """
                ## Well, this awkward...

                <p style="text-align: center;">
                 You need to log in to use this app.
                </p>"""
                template.main[:] = [pn.pane.Alert(message)]
                template.sidebar[:] = []
                return template
        return wrapper
    return decorator