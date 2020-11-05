entry_points={
    'console_scripts': ['xepmts = xepmts.cli:main'],
    'xepmts.apps': 'db = xepmts.api.app:make_local_app'}