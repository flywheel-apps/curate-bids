#!/usr/bin/env python3

import logging

from pprint import pformat
from pprint import pprint

from .File_locate_info import *

def show_all(obj, wait):
    print('dir(obj):')
    pprint(dir(obj), width=80, compact=True)
    try:
        if len(obj.tags) > 0:
            print('Tags:')
            pprint(obj.tags)
    except AttributeError:
        pass
    try:
        if len(obj.notes) > 0:
            print('Notes:')
            pprint(obj.notes)
    except AttributeError:
        pass
    try:
        if len(obj.info) > 0:
            print('Info:')
            pprint(obj.info)
    except AttributeError:
        pass
    if wait:
        ans = input('Press return ')
    print()

# Seperate from the above, these are used to show specific things:
show_file_info       = False # print ALL informaiton if present
show_BIDS_info       = True  # print BIDS informaiton if present
show_BIDS_error      = True
show_file_origin     = False
show_acquisitioin_id = True
show_file_id         = True
show_job_info        = False   # must be admin for this to work!

def find_duplicates(fw, project, file_locate_info, duplicates, project_ids, verbose):

    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    # verbose:
    # 0: only print duplicates
    # 1: list all files and BIDS status, 
    # 2: print a lot, user must press return to continue

    num_duplicates = 0
    # Check all full paths for included BIDs files to find duplicates
    for ss, session in enumerate(project.sessions()):

        # Development hack:
        #if num_duplicates > 5:
        #    break

        ses_info = f'{ss} {session.container_type} {session.label} {session.timestamp}'
        if verbose > 0:
            log.debug(ses_info)
        if verbose > 1:
            show_all(session, True)

        for aa, acquisition in enumerate(session.acquisitions()):
            acquisition = fw.get(acquisition.id) # Kaleb's suggestion brings in fully populated info!
            acq_info = f'{aa} {acquisition.container_type} {acquisition.label} {acquisition.timestamp}'
            if verbose > 0:
                log.debug(acq_info)
                if show_acquisitioin_id:
                    log.debug('acquisition.id '+acquisition.id)
            if verbose > 1:
                show_all(acquisition, True)

            for ff, afile in enumerate(acquisition.files):
                fil_info = f'{ff} {afile.container_type} {afile.name}'
                if verbose > 0:
                    log.debug(fil_info)
                    if show_file_id:
                        log.debug('file.id '+afile.id)

                if afile.id in project_ids:
                    msg='ERROR: fild.id {afile.id} was already seen!'
                    log.error(msg)
                    raise Exception(msg)
                else:
                    project_ids.append(afile.id)

                if len(afile.info) > 0:

                    if 'BIDS' in afile.info and isinstance(afile.info['BIDS'], dict):

                        if show_file_origin:
                            log.debug('Origin:')
                            log.debug(repr(afile.origin))

                        if show_job_info:
                            if afile.origin.type == 'user':
                                log.debug(f"file uploaded by {afile.origin['id']}")
                            elif afile.origin.type == 'job':
                                job = fw.get_job(afile.origin.id)
                                log.debug("job['gear_info']['name'] "+job['gear_info']['name'])
                                log.debug("job['inputs']")
                                log.debug(pformat(job['inputs']))
                            else:
                                log.debug(f'What is origin type "{afile.origin.type}"?')
                                raise Exception(msg)

                        if show_file_info:
                            log.debug('Info:')
                            log.debug(pformat(afile.info))

                        if show_BIDS_info:
                            log.debug('BIDS Info:')
                            log.debug(pformat(afile.info['BIDS']))

                        if show_BIDS_error:
                            if 'error_message' in afile.info['BIDS']:
                                log.debug('Error message: "'+afile.info['BIDS']['error_message']+'"')

                        # Here's the main stuff.  If printing, the full BIDS path and name will be 
                        # shown in          if
                        #   black on cyan   BIDS ignore is true
                        #   normal text     this is the first time seeing this path/name
                        #   black on yellow this path/name is a duplicate
                        if afile.info['BIDS']['ignore']:
                            if verbose > 0:
                                log.debug('Ignoring: ' + afile.name)

                        elif afile.info['BIDS']['Filename']:

                            # assemble the full BIDS path and name
                            fp = afile.info['BIDS']['Path'] + '/' + afile.info['BIDS']['Filename']

                            fli = File_locate_info(session.id, acquisition.id,
                                                   ff, # ff= index to file
                                                   acquisition.timestamp.timestamp(),
                                                   afile.size)

                            if fp not in file_locate_info:  # then this is the first sighting
                                if verbose > 0:
                                    log.debug(fp)
                                file_locate_info[fp] = fli

                            else:  # this file is a duplicate, how very exciting
                                num_duplicates += 1

                                #print(afile.id)
                                if fp in duplicates:  # then already have a list of duplicates
                                  dupl = duplicates[fp]
                                  #print('found repeated dup: ',dupl)
                                  dupl.append(fli)
                                  #print('   now: ',dupl)
                                  duplicates[fp] = dupl
                                else:  # first time so add both first file info and newly found duplicate info
                                  duplicates[fp] = [file_locate_info[fp], fli]
                                  #print('found first dup:', duplicates[fp])

                                if verbose > 0:
                                    log.debug(f'DUP {len(duplicates[fp]) - 1}:')
                                    log.debug(fp)

                        else:
                            if verbose > 0:
                                log.debug('BIDS but no BIDS Filename')
                    else:
                        if verbose > 0:
                            log.debug('BIDS not found in file.info')
                else: # len(afile.info) = 0
                    if verbose > 0:
                        log.debug('info is empty')

                if verbose > 1:
                    show_all(afile, True)

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
