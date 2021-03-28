import time
import getpass
import os 

from .daq import LiveDAQStreamzViewer



def get_live_rate_viewer(db=None, api_user=None, api_key=None, detector="tpc"):
    if db is None:
        import xepmts
        db = xepmts.get_client("v2")
        if not db.logged_in:
            db.login()
            db.session.auth.authorize()
        while not db.logged_in:
            time.sleep(0.5)

    if not api_user:
        api_user = os.getenv("DAQ_API_USER", None)

    if not api_user:
        api_user = input("DAQ API user: ")

    if not api_key:
        api_key = os.getenv("DAQ_API_KEY", None)
    if api_key is None:
        api_key = getpass.getpass("DAQ API key: ")

    viewer = LiveDAQStreamzViewer(
        api_user=api_user,
        api_key=api_key,
        client=db,
    )

    viewer.add_stream(detector)
    return viewer.daq_streams[detector]