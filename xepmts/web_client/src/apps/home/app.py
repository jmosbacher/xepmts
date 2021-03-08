"""## The Landing Page of the site"""
import pathlib

import panel as pn
from panel.pane import Markdown
from awesome_panel_extensions.frameworks.fast.fast_menu import to_menu

from xepmts.web_client.src.shared.templates import ListTemplate
from xepmts.web_client.src.shared import config, get_db
from xepmts.web_client.src.shared._menu import session_menu
from xepmts.web_client.src.shared.models import CenterColumn
from copy import deepcopy

HOME_PATH = pathlib.Path(__file__).parent / "home.md"
HOME_CONTENT = HOME_PATH.read_text()
AINT_NOONE_GOT_TIME = str(HOME_PATH.parent / "aint.gif")

WELCOME = """
### Welcome to the XENON PMT archive, home to all things PMT related.
Please send requests for additional content to [Yossi Mosbacher](mailto:joe.mosbacher@gmail.com)



"""
def view():
    """Returns the landing page of the site"""
    pn.config.sizing_mode = "stretch_width"
    db = pn.state.as_cached(pn.state.curdoc.session_context.id, get_db)
    db.session.auth.token_file = ""
    aint_noone = CenterColumn("# Writing a python script just to check the PMT gain evolution?", 
                               pn.pane.GIF(AINT_NOONE_GOT_TIME),
                               "# Thats what the web client is for.")
    sections = [
        pn.pane.Markdown(WELCOME),
        pn.Card(db.session.panel(), header="## Authentication"),
        pn.pane.Markdown(HOME_CONTENT),
        aint_noone,
    ]
    
    menu = session_menu(pn.state.curdoc.session_context.id)
    return ListTemplate(title="Home", main=sections, main_max_width="900px", sidebar_footer=menu)


if __name__.startswith("bokeh"):
    # Run the development server
    # python -m panel serve 'src/apps/home/home.py' --dev --show
    view().servable()
if __name__ == "__main__":
    # Run the server. Useful for integrated debugging in your Editor or IDE.
    # python 'src/apps/home/home.py'
    view().show(port=5007)
