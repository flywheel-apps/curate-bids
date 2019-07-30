#!/usr/bin/env python3

import logging

import flywheel

from .find import find_duplicates
from .rename import rename_duplicates

def run(api_key, project_path, do_make_changes, do_use_latest_not_largest, verbose):

    # Initialize flywheel client
    fw = flywheel.Client(api_key)

    project = fw.lookup(project_path) # another way: project = fw.get(project.id)
    # pprint(project.permissions)

    # Main variables:
    file_locate_info = dict() # This keeps track of all full BIDS path+names that have been seen.
                              #  use: file_locate_info[full BIDS path and name] = (class) File_locate_info
    duplicates       = dict() # duplicates[full BIDS path] = list of (class) File_locate_info
    project_ids      = []     # A list of all file ids for the whole project to make sure they are no
                              #  duplicates

    find_duplicates(fw, project, file_locate_info, duplicates, project_ids, verbose)

    rename_duplicates(fw, duplicates, do_make_changes, do_use_latest_not_largest)

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
