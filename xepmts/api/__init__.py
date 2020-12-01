# """Retain v1 as api default"""
# from .v1 import app, utils, settings, client, domain
# from . import v2
# from six import iteritems

# _SUBMODULES = {
#     "app": app,
#     "utils": utils,
#     "settings": settings,
#     "client": client,
#     "domain": domain,
#     "v2": v2,
# }

# import sys

# for module_name, module in iteritems(_SUBMODULES):
#     sys.modules["xepmts.api.%s" % module_name] = module