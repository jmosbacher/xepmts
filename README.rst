======
xepmts
======


.. image:: https://img.shields.io/pypi/v/xepmts.svg
        :target: https://pypi.python.org/pypi/xepmts

.. image:: https://img.shields.io/travis/jmosbacher/xepmts.svg
        :target: https://travis-ci.com/jmosbacher/xepmts

.. image:: https://readthedocs.org/projects/xepmts/badge/?version=latest
        :target: https://xepmts.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

Basic usage::
        import xepmts
        xepmts.notebook()


        db = xepmts.get_client().db
        db.set_token('YOUR-API-TOKEN')

        db.tpc.installs.next_page()


* Free software: MIT
* Documentation: https://jmosbacher.github.io/xepmts


Features
--------

* TODO

Credits
-------

This package was created with Cookiecutter_ and the `briggySmalls/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`briggySmalls/cookiecutter-pypackage`: https://github.com/briggySmalls/cookiecutter-pypackage
