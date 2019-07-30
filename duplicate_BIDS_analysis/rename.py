#!/usr/bin/env python3

import logging

from .File_locate_info import *

# At this point:
#   duplicates[full_path_file_name] = [list of (class) File_locate_info]
#   where File_locate_info = session_id, acquisition_id, file_index, acquisition_time, file_size

def rename_duplicates(fw, duplicates, do_make_changes, do_use_latest_not_largest):

    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    log.info('\nDuplicates:')
    if len(duplicates) == 0:
        log.info('(none)')
    for bids_fp, file_locate_info_list in duplicates.items():
        log.info(f'{bids_fp}') # full BIDS path and name

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
                    log.error(msg)
            else:
                log.warning('HMMMM, origin.job is not "user" or "jobs".  I do not know what to do, I am sad')
                my_dicom_archive = f'(none, origin.job={afile.origin.type})'
            dicom_archives.append(my_dicom_archive)

            # The file acquisition time doesn't seem to be always set
            try:
                acquisition_time = afile.info["AcquisitionDateTime"]
            except KeyError:
                acquisition_time = ''

            log.info(f'  acquisition label     : {acquisition.label} ')
            #print(f'  acquisition id        : {acquisition.id} ')
            log.info(f'  acquisition timestamp : {str(acquisition.timestamp)} ') 
            #print(f'  file id               : {afile.id}')
            log.info(f'  file index            : {fli.file_index}')
            log.info(f'  file acquisition time : {acquisition_time}')
            log.info(f'  file size             : {afile.size}')
            log.info(f'  DICOM archive         : {my_dicom_archive}')
            log.info('')
            #pprint(afile.info)

            # end for fli in sorted_list: # for each duplicate found

        num_changes = 0
        log.info('Making changes:')
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
                log.info(f'what the heck is {dicom_archives[ii]}?')
                sys.exit(-1)

            if go:

                msg = f'  for acquisition timestamp : {str(acquisition.timestamp)}:'
                log.info(msg)
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
                        log.info(msg)
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
                        log.info(msg)
                        msg = f'    {doing} Adding Error message: "{error_message}"'
                        log.info(msg)
                        msg = f'    {doing} Setting file.info["BIDS"]["valid"] to False'
                        log.info(msg)

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
                        log.info(msg)
                        msg = f"    {doing} setting afile.info['BIDS']['ignore'] = True"
                        log.info(msg)
                        msg = f'    {doing} Adding Error message: "{error_message}"'
                        log.info(msg)
                        msg = f'    {doing} Setting file.info["BIDS"]["valid"] to False'
                        log.info(msg)

                else:
                    msg = f"    {afile.info['BIDS']['Filename']} stays as is"
                    log.info(msg)

                num_changes += 1
                log.info('')

            ii += 1
            # end for fli in sorted_list: # for each duplicate found
        if num_changes == 0:
            log.info('  (none)')
        else:
            log.info(f'\n{num_changes} names were changed')
        log.info('')

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
