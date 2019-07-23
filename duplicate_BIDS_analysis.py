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

import sys
import flywheel
import json
from pprint import pprint
import datetime


project_path = 'flywheel/bids_test4_dartmouth_phantoms'
project_path = 'flywheel/BIDS_Duplicate_Junk'
project_path = 'flywheel/BIDS_Duplicate_Test'


if len(sys.argv) == 2: # No arguments given
    project_path = sys.argv[1]+'/'+sys.argv[2]
# else: just use project_path as is


do_make_changes           = True
do_use_latest_not_largest = True


Verbose = 1
# 0: only print duplicates
# 1: list all files and BIDS status, 
# 2: print a lot, user must press return to continue

# Seperate from the above, these are used to show specific things:
show_file_info       = False # print ALL informaiton if present
show_BIDS_info       = True  # print BIDS informaiton if present
show_BIDS_error      = True
show_file_origin     = False
show_acquisitioin_id = True
show_file_id         = True
show_job_info        = False   # must be admin for this to work!

#-------------------------------------------------------------------------------
# See https://en.wikipedia.org/wiki/ANSI_escape_code
def print_in_color(f, b, t, e):
    if f > -1:
        print('\x1b[38;5;'+str(f)+'m', end='')   # set Foreground
    if b > -1:
        print('\x1b[48;5;'+str(b)+'m', end='')   # set Background
    print(t+'\u001b[0m', end=e)                  # Reset

#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------

# Read in api key from secrets file
with open("api-keys", 'r') as f:
    api_keys = json.load(f)
api_key = api_keys['ss.ce']

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

num_duplicates = 0
# Check all full paths for included BIDs files to find duplicates
for ss, session in enumerate(project.sessions()):

    # Development hack:
    #if num_duplicates > 5:
    #    break

    ses_info = f'{ss} {session.container_type} {session.label} {session.timestamp}'
    if Verbose > 0:
        print()
        print_in_color(13, -1, ses_info, '\n')  # magenta
    if Verbose > 1:
        show_all(session, True)

    for aa, acquisition in enumerate(session.acquisitions()):
        acquisition = fw.get(acquisition.id) # Kaleb's suggestion brings in fully populated info!
        acq_info = f'{aa} {acquisition.container_type} {acquisition.label} {acquisition.timestamp}'
        if Verbose > 0:
            print_in_color(14, -1, acq_info, '\n')  # cyan
            if show_acquisitioin_id:
                print('acquisition.id', acquisition.id)
        if Verbose > 1:
            show_all(acquisition, True)

        for ff, afile in enumerate(acquisition.files):
            fil_info = f'{ff} {afile.container_type} {afile.name}'
            if Verbose > 0:
                print_in_color(2, -1, fil_info, '\n')  # green
                if show_file_id:
                    print('file.id',afile.id)

            if afile.id in project_ids:
                msg='ERROR: fild.id {afile.id} was already seen!'
                print_in_color(231,196,' '+msg+' ','\n') # white on red
                sys.exit(-1)
            else:
                project_ids.append(afile.id)

            if len(afile.info) > 0:

                if 'BIDS' in afile.info and isinstance(afile.info['BIDS'], dict):

                    if show_file_origin:
                        print('Origin:')
                        print(repr(afile.origin))
                        #print('classification:')
                        #print(repr(afile.classification))

                    if show_job_info:
                        if afile.origin.type == 'user':
                            print(f"file uploaded by {afile.origin['id']}")
                        elif afile.origin.type == 'job':
                            job = fw.get_job(afile.origin.id)
                            #pprint(job)
                            print("job['gear_info']['name']",job['gear_info']['name'])
                            print("job['inputs']")
                            pprint(job['inputs'])
                        else:
                            print(f'What is origin type "{afile.origin.type}"?')
                            sys.exit(-1)

                    if show_file_info:
                        print('Info:')
                        pprint(afile.info)

                    if show_BIDS_info:
                        print('BIDS Info:')
                        pprint(afile.info['BIDS'])

                    if show_BIDS_error:
                        if 'error_message' in afile.info['BIDS']:
                            print('Error message: "'+afile.info['BIDS']['error_message']+'"')

                    # Here's the main stuff.  If printing, the full BIDS path and name will be 
                    # shown in          if
                    #   black on cyan   BIDS ignore is true
                    #   normal text     this is the first time seeing this path/name
                    #   black on yellow this path/name is a duplicate
                    if afile.info['BIDS']['ignore']:
                        if Verbose > 0:
                            print_in_color(0, 6, 'Ignoring: ' + afile.name, '\n')  # black on cyan

                    elif afile.info['BIDS']['Filename']:

                        # assemble the full BIDS path and name
                        fp = afile.info['BIDS']['Path'] + '/' + afile.info['BIDS']['Filename']

                        fli = File_locate_info(session.id, acquisition.id,
                                               ff, # ff= index to file
                                               acquisition.timestamp.timestamp(),
                                               afile.size)

                        if fp not in file_locate_info:  # then this is the first sighting
                            if Verbose > 0:
                                print(fp)
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

                            if Verbose > 0:
                                print_in_color(3, 0, f'DUP {len(duplicates[fp]) - 1}:', '')
                                print_in_color(0, 3, ' ' + fp + ' ', '\n')  # black on yellow

                    else:
                        if Verbose > 0:
                            print('BIDS but no BIDS Filename')
                else:
                    if Verbose > 0:
                        print('BIDS not found in file.info')
            else: # len(afile.info) = 0
                if Verbose > 0:
                    print('info is empty')

            if Verbose > 1:
                show_all(afile, True)

# At this point:
#   duplicates[full_path_file_name] = [list of (class) File_locate_info]
#   where File_locate_info = session_id, acquisition_id, file_index, acquisition_time, file_size

if True:
    print('\nDuplicates:')
    if len(duplicates) == 0:
        print('(none)')
    for bids_fp, file_locate_info_list in duplicates.items():
        print(f'{bids_fp}') # full BIDS path and name

        # Sort the list of duplicates
        if do_use_latest_not_largest:
            # sort by acquisition time
            sorted_list = sorted(file_locate_info_list, key=lambda dupl: dupl.acquisition_time)
        else:
            # sort by file size
            sorted_list = sorted(file_locate_info_list, key=lambda dupl: dupl.file_size)

        common_dicom_name = ''
        all_same_dicom = True
        dicom_archives = []
        for fli in sorted_list: # for each duplicate found

            acquisition = fw.get(fli.acquisition_id)
            afile = acquisition.files[fli.file_index]

            # now that the file and acquisiiton are known, gather information to
            # decide what to do about this duplicate

            # see if it is a nifti file with a corresponding dicom archive
            if afile.origin.type == 'user':
                my_dicom_archive = '(none, uploaded by user)'
                all_same_dicom = False # this IS the dicom archive so mark as "__dup<number>" not just number
            elif afile.origin.type == 'job':
                my_dicom_archive = '(none, not found)'
                # if this is a NIfTI file, it will have an origin job of dcm2niix so find the job
                # the input to that job will be the DICOM archive

                # fw.jobs.find(f'id={afile.origin.id}') did not work
                # this provides fully populated info, but user must be a site_admin to use:
                # job = fw.get_job(afile.origin.id)
                # this works too but provides less information:
                job_output = fw.get_session_jobs(fli.session_id)
                for job in job_output['jobs']:
                    if job.id == afile.origin.id:
                        #print(repr(job))
                        dcm2niix_info = job['inputs']['dcm2niix_input']
                        if dcm2niix_info['id'] == acquisition.id: # same acquisition as file
                            my_dicom_archive = dcm2niix_info['name']
                            # print(f'Found my DICOM archive: {my_dicom_archive}')
                            if common_dicom_name == '': # first time, save name
                                common_dicom_name = str(acquisition.timestamp)+my_dicom_archive
                            elif str(acquisition.timestamp)+common_dicom_name != my_dicom_archive:
                                all_same_dicom = False # they don't all have the same dicom archive

                if my_dicom_archive == '(none, not found)':
                    msg = 'ERROR: job not found'
                    print_in_color(231,196,' '+msg+' ','\n') # white on red
            else:
                print('HMMMM, origin.job is not "user" or "jobs".  I do not know what to do, I am sad')
                my_dicom_archive = f'(none, origin.job={afile.origin.type})'
            dicom_archives.append(my_dicom_archive)

            # The file acquisition time doesn't seem to be always set
            try:
                acquisition_time = afile.info["AcquisitionDateTime"]
            except KeyError:
                acquisition_time = ''

            print(f'  acquisition label     : {acquisition.label} ')
            #print(f'  acquisition id        : {acquisition.id} ')
            print(f'  acquisition timestamp : {str(acquisition.timestamp)} ') 
            #print(f'  file id               : {afile.id}')
            print(f'  file index            : {fli.file_index}')
            print(f'  file acquisition time : {acquisition_time}')
            print(f'  file size             : {afile.size}')
            print(f'  DICOM archive         : {my_dicom_archive}')
            print()
            #pprint(afile.info)

            # end for fli in sorted_list: # for each duplicate found

        num_changes = 0
        print('Making changes:')
        # Now loop through duplicates and make changes to names, etc. as needed
        ii = 0
        numFound = len(sorted_list)
        for fli in sorted_list: # for each duplicate found

            acquisition = fw.get(fli.acquisition_id)
            afile = acquisition.files[fli.file_index]

            go = False
            if dicom_archives[ii][:5] != '(none': # then the file is NIfTI with a DICOM archive 
                go = True
            elif dicom_archives[ii] == '(none, uploaded by user)': # then is is the file a DICOM archive 
                go = True
            else:
                print(f'what the heck is {dicom_archives[ii]}?')
                sys.exit(-1)

            if go:

                msg = f'  for acquisition timestamp : {str(acquisition.timestamp)}:'
                print(msg)
                # since this list of duplicates is sorted, the last one is the one to keep
                if ii < (numFound - 1): # then not the last one

                    # Separate extension from name so adding "diff" will be before the extension
                    file_name = afile.info['BIDS']['Filename']
                    file_ext = ''

                    if file_name[-7:] == '.nii.gz':
                      file_ext  = '.nii.gz'
                      file_name = file_name[:-7]

                    elif file_name[-10:] == '.dicom.zip':
                      file_ext  = '.dicom.zip'
                      file_name = file_name[:-10]

                    # set BIDS error message for duplicates
                    error_message = f"duplicate of {file_name}"
                    if 'error_message' in afile.info['BIDS']:
                        # append to existing error message
                        if afile.info['BIDS']['error_message'] != '':
                            error_message = afile.info['BIDS']['error_message'] + ' ; ' + error_message

                    if all_same_dicom: # then rename by adding ”_<index_number>”
                        new_file_name = f"{file_name}_{ii+1:02d}{file_ext}"
                        print(msg)
                        if do_make_changes:
                            afile.info['BIDS']['Filename'] = new_file_name
                            afile.info['BIDS']['error_message'] = error_message
                            afile.info['BIDS']['valid'] = False
                            afile.update_info(afile.info)
                            # doing the same thing this way removes all other BIDS info:
                            #afile.update_info({"BIDS":{"Filename": new_file_name}})
                            doing = 'actually changing: '
                        else:
                            doing = 'NOT changing: '
                        msg = f"    {doing} {file_name}{file_ext} --> {new_file_name}"
                        print(msg)
                        msg = f'    {doing} Adding Error message: "{error_message}"'
                        print(msg)
                        msg = f'    {doing} Setting file.info["BIDS"]["valid"] to False'
                        print(msg)

                    else: # rename by adding “__dup<number>” and set BIDS ignore to True

                        # Don't change acquisition label!
                        #msg = f"    {acquisition.label} --> "+\
                        #      f"{acquisition.label}__dup{ii+1:02d}"
                        #print(msg)

                        new_file_name = f"{file_name}__dup{ii+1:02d}{file_ext}"
                        if do_make_changes:
                            afile.info['BIDS']['Filename'] = new_file_name
                            afile.info['BIDS']['ignore'] = True
                            afile.info['BIDS']['error_message'] = error_message
                            afile.info['BIDS']['valid'] = False
                            afile.update_info(afile.info)
                            # doing the same thing this way removes all other BIDS info:
                            #afile.update_info({"BIDS":{"ignore": True, "Filename": new_file_name}})
                            doing = 'actually changing: '
                        else:
                            doing = 'NOT changing: '
                        msg = f"    {doing} {file_name}{file_ext} --> {new_file_name}"
                        print(msg)
                        msg = f"    {doing} setting afile.info['BIDS']['ignore'] = True"
                        print(msg)
                        msg = f'    {doing} Adding Error message: "{error_message}"'
                        print(msg)
                        msg = f'    {doing} Setting file.info["BIDS"]["valid"] to False'
                        print(msg)

                else:
                    msg = f"    {afile.info['BIDS']['Filename']} stays as is"
                    print(msg)

                num_changes += 1
                print()

            ii += 1
            # end for fli in sorted_list: # for each duplicate found
        if num_changes == 0:
            print('  (none)')
        else:
            print(f'\n{num_changes} names were changed')
        print()


# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
