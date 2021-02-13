import os
if os.getenv("GAE_ENV", None):
    
    from google.cloud import secretmanager_v1 as secretmanager
    client = secretmanager.SecretManagerServiceClient()

    # name = client.secret_version_path('xepmts', 'api_mongo_pass', '2')
    response = client.access_secret_version(name="projects/972333563849/secrets/api_mongo_pass/versions/2")
    MONGO_PASSWORD = response.payload.data.decode('UTF-8')

    # name = client.secret_version_path('xepmts', 'api_root_token', '1')
    response = client.access_secret_version(name="projects/972333563849/secrets/api_root_token/versions/1")
    ROOT_TOKEN = response.payload.data.decode('UTF-8')
    
else:
    MONGO_PASSWORD = os.getenv("XEPMTS_MONGO_PASS", "")
    ROOT_TOKEN = os.getenv("XEPMTS_ROOT_TOKEN", None)

GLOBAL_READ_TOKEN = os.getenv("XEPMTS_GLOBAL_READ_TOKEN", None)