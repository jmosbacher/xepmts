import time
import getpass

from .daq import LiveDAQStreamzViewer



def get_live_rate_viewer(db=None, api_user=None, api_key=None, detectors=["tpc"]):
    if db is None:
        import xepmts
        db = xepmts.get_client("v2")
        if not db.logged_in:
            db.login()
            db.session.auth.authorize()
        while not db.logged_in:
            time.sleep(0.5)
            
    if api_user is None:
        api_user = input("DAQ API user: ")
    if api_key is None:
        api_key = getpass.getpass("DAQ API key: ")

    viewer = LiveDAQStreamzViewer(
        api_user=api_user,
        api_key=api_key,
        client=db,
    )

    for d in detectors:
        viewer.add_stream(d)
    return viewer