#!/usr/bin/env python3
"""
    duplicate_BIDS_analysis.py - looks for duplicate BIDS files in the given project,

    This proceeds in two passes.  The first steps through each file in the project
    and saves the full BIDS path and name, along with information necessary to 
    locate that file (see File_locate_info).  This pass finds duplicates.
    This pass can optionally print out a lot of information about the session, acquisition,
    and files as they are encountered.

    The second pass goes through each duplicate and decides how to re-name them to
    indicate that they are duplicates.

    The "proper" files (non-duplicates) to keep as is, are determined by either:

        acquisition.timestamp (the last/most recent is kept)
    or
        file.size (the largest is kept)

    Others are marked as duplicates.
    
    Renaming depends on:

       If the duplicate NIfTI files come from seperate DICOM archives:
         - DO NOT append “__dup<number>” to the acquisition.label (don't touch acquisition label)
         - append “__dup<number>”  to the file.info['BIDS']['Filename']
         - Set file.info.['BIDS']['ignore'] to true

       elif the duplicate NIfTI files are from the same DICOM archive/acquisition:
         - append ”_<index_number>”  (oldest to newest) to the 
           file.info['BIDS']['Filename']

       DICOM archives are renamed similarly.


    (c) Copyright 2019 Flywheel All rights reserved.
"""

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
