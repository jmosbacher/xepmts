
from eve.auth import BasicAuth, TokenAuth
from flask import current_app
from xepmts.api.secrets import ROOT_TOKEN, GLOBAL_READ_TOKEN
import os
from functools import lru_cache
import requests
import logging
import sys

logger = logging.getLogger(__name__)

@lru_cache(maxsize=100)
def get_roles(token):
    roles = []
    accounts = current_app.data.driver.db['accounts']
    account = accounts.find_one({'token': token})
    if account:
        roles = account.get("roles", [])
    else:
        try:
            resp = requests.get(f'https://{os.getenv("DOMAIN", "localhost:8000")}/db_api/roles/{token}', timeout=5)
            if resp.ok:
                data = resp.json()
                roles = data["roles"]
                if roles:
                    accounts.insert_one({
                        "username": data["user"]+"_"+data["token"],
                        "token": data["token"],
                        "roles": roles,
                    })
                
            # print(f"got roles from website: {roles}", file=sys.stderr)
        except Exception as e:
            print(e)

            # print(f"got roles from mongo account: {roles}", file=sys.stderr)
    # if not roles:
        # print("Found no matching roles")
    return set(roles)


class XenonBasicAuth(BasicAuth):
    def check_auth(self, username, password, allowed_roles, resource,
            method):
        return username == os.getenv("API_USER", "xenon") and password == os.getenv("API_PASS", "secretxenon")

class XenonTokenAuth(TokenAuth):
    # def __init__(self, ):
        # from redis import StrictRedis, ConnectionPool
        # self.redis = StrictRedis()
        # self.redis.connection_pool = ConnectionPool.from_url(os.environ.get(
        #     'REDIS_URL',
        #     'redis://localhost:6379'))
        
    def check_auth(self, token, allowed_roles, resource, method):
        if not token:
            return False
        if ROOT_TOKEN and token == ROOT_TOKEN:
            return True
        if all([GLOBAL_READ_TOKEN, token == GLOBAL_READ_TOKEN, method in ["GET", "HEAD"]]):
            return True
        # print(f"Checking roles for token {token}", file=sys.stderr)
        roles = get_roles(token)
        return bool(roles.intersection(allowed_roles))
