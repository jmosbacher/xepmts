"""Provides

- config: An instance of SiteConfig holding the current Site configuration
"""

import pathlib
from typing import Union
import panel as pn
import xepmts

import toml

from xepmts.web_client.src.shared.models import Application, Person, SiteConfig
from xepmts.web_client import __file__ as src_file

ROOT_PATH = pathlib.Path(src_file).parent

def _create_site_config(config_root: Union[str, pathlib.Path]) -> SiteConfig:
    if isinstance(config_root, str):
        config_root = pathlib.Path(config_root)
    persons_toml = config_root / "persons.toml"
    persons = Person.create_from_toml(persons_toml)

    applications = config_root / "applications.toml"
    applications = Application.create_from_toml(applications, persons=persons)
    # print(applications)
    # for app in applications:
    #     app.code_url = ROOT_PATH / app.code_url
    
    site_toml = config_root / "site.toml"
    site = toml.load(site_toml)
    if "static_dirs" in site:
        for k,v in site["static_dirs"].items():
            apath = pathlib.Path(v)
            if not apath.is_absolute():
                apath = ROOT_PATH / apath
            site["static_dirs"][k] = str(apath)
    
    # def save_token(auth):
    #     pn.state.
    
    # xepmts_client.session.auth.post_login_hooks.append()
    return SiteConfig(**site, persons=persons, applications=applications)
