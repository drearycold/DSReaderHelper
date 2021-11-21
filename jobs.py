#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__ = 'GPL v3'
__copyright__ = '2021 by Drearycold <drearycold at icloud.com>'
__docformat__ = 'restructuredtext en'

import os, traceback, time

def grsync_update_reading_progress(goodreads_id, percent, profile_name):
    results = {}
    from calibre_plugins.goodreads_sync.core import HttpHelper
    grhttp = HttpHelper()
    print("GRSYNC %s" % str(grhttp))
    client = grhttp.create_oauth_client(profile_name)
    results[goodreads_id] = ['grsync_update_reading_progress', grhttp.update_status(client, goodreads_id, percent), 0]
    
    return results

def grsync_add_remove_book_to_shelf(goodreads_id, profile_name, shelf_name, action):
    results = {}
    from calibre_plugins.goodreads_sync.core import HttpHelper
    grhttp = HttpHelper()
    print("GRSYNC %s" % str(grhttp))
    client = grhttp.create_oauth_client(profile_name)
    results[goodreads_id] = ['grsync_add_remove_book_to_shelf', grhttp.add_remove_book_to_shelf(client, shelf_name, goodreads_id, action), 0]

    return results
