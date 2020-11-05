=====
Usage
=====

To use xepmts::

    import xepmts

    # If you are using a notebook:
    xepmts.notebook()

    db = xepmts.default_client().db
    db.set_token('YOUR-API-TOKEN')

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
