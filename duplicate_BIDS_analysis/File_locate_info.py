#!/usr/bin/env python3

class File_locate_info:
    """ All informatino needed to get to a file and then find out more about it, plus
          the two keys to sort on to figure out which duplicates to keep
    """
    def __init__(self, session_id, acquisition_id, file_index, acquisition_time, file_size):
        self.session_id       = session_id
        self.acquisition_id   = acquisition_id
        self.file_index       = file_index       # use: acquisition.files[file_index]
        self.acquisition_time = acquisition_time # Sort key: keep latest
        self.file_size        = file_size        # Sort key: keep largest

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
