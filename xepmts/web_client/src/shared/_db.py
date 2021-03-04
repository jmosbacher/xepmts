import xepmts

def get_db():
    xepmts_client = xepmts.get_client("v2")
    xepmts_client.select_server("xenon_v2")
    # xepmts_client.set_server_url(gae2_v2="https://api2-dot-xenon-pmts.uc.r.appspot.com/v2")
    # xepmts_client.select_server("gae2_v2")
    return xepmts_client

