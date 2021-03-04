import panel as pn
import holoviews as hv

from src.shared.templates import ListTemplate
from src.shared import config, get_db
from src.shared._menu import session_menu
from src.apps.gains_viewer.gains_viewer import GainsViewer

db = pn.state.as_cached(pn.state.curdoc.session_context.id, get_db)


def view():
    menu = session_menu(pn.state.curdoc.session_context.id)
    template = ListTemplate(
        title="Gain viewer",
        sidebar_footer=menu,

    )
    pn.state.curdoc.theme = template.theme.bokeh_theme
    if db.logged_in:
        gv = GainsViewer(client=db)
        gv._logged_in = db.logged_in 
        pn.state.add_periodic_callback(gv._update_login_status)
        hv.renderer('bokeh').theme = pn.state.curdoc.theme #template.theme.bokeh_theme
        # token_input = 
        template.main[:] = gv.panels()
        # template.header[:] = [token_input]+template.header[:]
        template.sidebar[:] = [gv.settings_view(), pn.Spacer(height=25)]
    else:
        template.main[:] = [pn.pane.Alert("# You need to log in to use this app.")]
    return template


if __name__.startswith("bokeh"):
    view().servable()
