import panel as pn
# pn.extension()
import xepmts
import eve_panel
import pathlib
xepmts.extension()

# pn.state.location.reload = False

SOURCEDIR = pathlib.Path(__file__).parent
FAVICON = SOURCEDIR / "favicon.png"
xepmts.settings(GUI_HEIGHT=1000, GUI_WIDTH=1200, SHOW_INDICATOR=False)

db = xepmts.default_client().db

token = pn.state.session_args.get("api-token", [b""])[0].decode()
db.set_token(token)
resources = db.collect_resource_tree()
resources.pop("accounts", None)

# web_client = eve_panel.EveWebClient(resources=resources, location=pn.state.location)
# tmpl = web_client.template(
#     title="Xenon PMT Database",
#     favicon=str(FAVICON.absolute()),
#     header_background="#34949e"
# )

tmpl = pn.template.MaterialTemplate(title="Xenon PMT Database",
                                    favicon=str(FAVICON.absolute()),
                                    header_background="#34949e")

menu = eve_panel.Menu(resources=resources, width=250)
tmpl.main.width=1200
tmpl.main[:] = [pn.panel(menu.selected_view, max_width=1200, scrollable=True,
 width_policy='max', sizing_mode='stretch_width')]
tmpl.sidebar[:] = [menu.menu_view]
tmpl.header.append(pn.panel(db._http_client.auth.credentials_view))


tmpl.servable()

if __name__ == "__main__":
    import os
    import platform

    address = os.getenv("BOKEH_ADDRESS", "localhost")
    APP_ROUTES = {
        "/": tmpl.servable(),
    }

    if platform.system() == "Windows":
        pn.serve(APP_ROUTES, port=8080, dev=False, title="XEPMTS", address=address)
    else:
        pn.serve(
            APP_ROUTES, port=8080, dev=False, title="XEPMTS", address=address, num_procs=1, allow_websocket_origin=["*"],
            # oauth_provider="github",oauth_key="", oauth_secret="",
        )