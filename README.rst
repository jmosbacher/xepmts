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

Basic Usage
-----------

.. code-block:: python

    import xepmts

    # If you are using a notebook:
    xepmts.notebook()

    # v1 client
    db = xepmts.get_client("v1")
    db.login(token='YOUR-API-TOKEN')

    # v2 client
    db = xepmts.get_client("v2")
    db.login()

    # set the number of items to pull per page
    db.tpc.installs.items_per_page = 25
    
    # get the next page 
    page = db.tpc.installs.next_page()

    # iterate over pages:
    for page in db.tpc.installs.pages():
        df = page.df
        # do something with data

    # select only top array
    top_array = db.tpc.installs.filter(array="top")

    # iterate over top array pages
    for page in top_array.pages():
        df = page.df
        # do something with data

    query = dict(pmt_index=4)
    # get the first page of results for this query as a list of dictionaries
    docs = db.tpc.installs.find(query, max_results=25, page_number=1)

    # same as find, but returns a dataframe 
    df = db.tpc.installs.find_df(query)


    # insert documents into the database
    docs = [{"pmt_index": 1, "position_x": 0, "position_y": 0}]
    db.tpc.installs.insert_documents(docs)
    
* Free software: MIT
* Documentation: https://xepmts.readthedocs.io/


Features
--------

* TODO

Credits
-------

This package was created with Cookiecutter_ and the `briggySmalls/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`briggySmalls/cookiecutter-pypackage`: https://github.com/briggySmalls/cookiecutter-pypackage
