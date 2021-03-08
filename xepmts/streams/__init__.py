from .daq import LiveDAQStreamzViewer
import getpass


def get_live_rate_viewer(db, api_user=None, api_key=None, detectors=["tpc"]):
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