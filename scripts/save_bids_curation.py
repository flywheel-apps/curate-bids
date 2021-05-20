#!/usr/bin/env python3
"""Save BIDS mapping from acquisition names to BIDS paths and fieldmap IntendedFors as sorted csv files.

Note that you need to be logged in to a Flywheel instance using the CLI (fw login ...)

INTENDED_FOR is a space separated pair of regular expressions, the first one matches the fieldmap file name and the
second of each pair matches the BIDS filename.

Example with --intended-for parameter:
   save_bids_curation.py  Group Project -i '.*fmap(_|-)SE(_|-).*' '_run-1' '.*gre.+_e[12]\.' '_run-2' '.*gre.+_ph' '_run-2'
"""

import argparse
import csv
import pandas as pd
import os
import re
from pathlib import Path
import pickle

import flywheel


PICKLE_FILE_NAME = "./bids_data.pickle"

COLUMNS = (
    "Subject",
    "Session",
    "SeriesNumber",
    "Acquisition label (SeriesDescription)",
    "File name",
    "File type",
    "Curated BIDS path",
    "Unique?",
)


def make_file_name_safe(input_basename, replace_str=""):
    """Remove non-safe characters from a filename and return a filename with
        these characters replaced with replace_str.

    :param input_basename: the input basename of the file to be replaced
    :type input_basename: str
    :param replace_str: the string with which to replace the unsafe characters
    :type   replace_str: str
    :return: output_basename, a safe
    :rtype: str
    """

    safe_patt = re.compile(r"[^A-Za-z0-9_\-.]+")
    # if the replacement is not a string or not safe, set replace_str to x
    if not isinstance(replace_str, str) or safe_patt.match(replace_str):
        print("{} is not a safe string, removing instead".format(replace_str))
        replace_str = ""

    # Replace non-alphanumeric (or underscore) characters with replace_str
    safe_output_basename = re.sub(safe_patt, replace_str, input_basename)

    if safe_output_basename.startswith("."):
        safe_output_basename = safe_output_basename[1:]

    print('"' + input_basename + '" -> "' + safe_output_basename + '"')

    return safe_output_basename


def do_print(msg):

    if args.verbose > 0:
        print(msg)


def get_bids_info():
    """Get BIDS mapping from acquisition file names to BIDS paths and fieldmap IntendedFors.

    Information is gathered here and saved into global variables.

    Returns:
            num_subjects (int): number of subjects found
            num_sessions (int): number of sessions found
            num_duplicates (int): number of duplicates detected
    """
    global all_df

    num_subjects = 0
    num_sessions = 0
    num_duplicates = 0

    # Look through all acquisition files in the project and get their BIDS path
    for subject in project.subjects.iter_find():

        num_subjects += 1

        do_print(subject.label)

        # The number of times an acquisition with a given name is found for each subject
        subjects_have[
            subject.label
        ] = dict()  # subjects_have[subject.label][acquisition.label] = count

        # Gather IntendedFor information here to be saved into a .csv file later
        intended_for_acq_label = dict()
        intended_for_acq_id = dict()
        intended_for_dirs = dict()
        intended_fors = dict()

        # Gather file information here for saving into a .csv file later
        nifti_df = pd.DataFrame(columns=COLUMNS)

        ii = 0  # Current acquisition index

        seen_paths = (
            dict()
        )  # seen_paths[bids_path] = count (# of times this path has been found)

        for session in subject.sessions():
            num_sessions += 1
            for acquisition in session.acquisitions():

                do_print(f"{ii}  {acquisition.label}")

                if acquisition.label in acquisition_labels:
                    acquisition_labels[acquisition.label] += 1
                else:
                    acquisition_labels[acquisition.label] = 1

                if acquisition.label in subjects_have[subject.label]:
                    subjects_have[subject.label][acquisition.label] += 1
                else:
                    subjects_have[subject.label][acquisition.label] = 1

                for file in acquisition.reload().files:

                    # determine full BIDS path
                    if "BIDS" in file.info:
                        if file.info["BIDS"] == "NA":
                            bids_path = "nonBids"
                        else:
                            bids_path = ""
                            # check for craziness that should never happen
                            expected = ["ignore", "Folder", "Filename"]
                            for key in expected:
                                if key not in file.info["BIDS"]:
                                    bids_path += f"missing_{key} "
                            if bids_path == "":
                                if file.info["BIDS"]["ignore"]:
                                    bids_path = "ignored"
                                else:  # get the actual path
                                    bids_path = (
                                        f"{file.info['BIDS']['Folder']}/"
                                        + f"{file.info['BIDS']['Filename']}"
                                    )

                        if (
                            "IntendedFor" in file.info
                            and len(file.info["IntendedFor"]) > 0
                        ):
                            intended_fors[file.name] = file.info["IntendedFor"]
                            intended_for_acq_label[file.name] = acquisition.label
                            intended_for_acq_id[file.name] = acquisition.id
                            if "IntendedFor" in file.info["BIDS"]:
                                intended_for_dirs[file.name] = file.info["BIDS"][
                                    "IntendedFor"
                                ]
                            else:
                                # This only happens when a previous curation run had folder(s) here
                                # but this one does not.
                                intended_for_dirs[file.name] = [
                                    {"Folder": "folder is missing"}
                                ]
                    else:
                        bids_path = "Not_yet_BIDS_curated"

                    if "SeriesNumber" in file.info:
                        series_number = file.info["SeriesNumber"]
                    else:
                        series_number = "?"

                    # Detect Duplicates
                    if bids_path in ["ignored", "nonBids", "Not_yet_BIDS_curated"]:
                        unique = ""
                    elif bids_path in seen_paths:
                        seen_paths[bids_path] += 1
                        unique = f"duplicate {seen_paths[bids_path]}"
                        num_duplicates += 1
                    else:
                        seen_paths[bids_path] = 0
                        unique = "unique"

                    do_print(
                        f"{series_number}, {subject.label}, {session.label}, "
                        f"{acquisition.label}, {file.name}, {file.type}, "
                        f"{bids_path}, {unique}"
                    )

                    nifti_df.loc[ii] = [
                        subject.label,
                        session.label,
                        series_number,
                        acquisition.label,
                        file.name,
                        file.type,
                        bids_path,
                        unique,
                    ]
                    ii += 1

        nifti_df.sort_values(by=["Curated BIDS path"], inplace=True)

        all_df = all_df.append(nifti_df)

        all_intended_for_acq_label[subject.label] = intended_for_acq_label
        all_intended_for_acq_id[subject.label] = intended_for_acq_id
        all_intended_for_dirs[subject.label] = intended_for_dirs
        all_intended_fors[subject.label] = intended_fors

        all_seen_paths[subject.label] = seen_paths

    return num_subjects, num_sessions, num_duplicates


def save_niftis():
    """Save acquisition/file name -> bids path mapping. """

    all_df.to_csv(f"{safe_group_label}_{safe_project_label}_niftis.csv", index=False)

    do_print("")


def save_intendedfors():
    """save field map IntendedFor lists.

    If args.intended_for has been provided (a list of regex pairs), this method will only keep the ones that match
    """

    with open(
        f"{safe_group_label}_{safe_project_label}_intendedfors.csv", mode="w"
    ) as intendedfors_file:
        intendedfors_writer = csv.writer(
            intendedfors_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )

        if args.verbose > 0:
            intendedfors_writer.writerow(["Initial values (before correction)"])
            intendedfors_writer.writerow(
                [
                    "acquisition label",
                    "file name and folder",
                    "IntendedFor List of BIDS paths",
                ]
            )

            for subj in all_intended_for_dirs:

                for k, v in all_intended_for_dirs[subj].items():
                    do_print(f"{all_intended_for_acq_label[subj][k]}, {k}")
                    intendedfors_writer.writerow(
                        [all_intended_for_acq_label[subj][k], k]
                    )
                    for i in v:
                        do_print(f",{i['Folder']}")
                        intendedfors_writer.writerow(["", i["Folder"]])
                        all_intended_fors[subj][k].sort()
                        for j in all_intended_fors[subj][k]:
                            do_print(f",,{j}")
                            intendedfors_writer.writerow(["", "", j])

        # Keep only proper file paths if they match fieldmaps as per provided regexes
        if args.intended_for:

            string_pairs = zip(args.intended_for[::2], args.intended_for[1::2])
            # for pair in string_pairs:
            #    print(f"fmap regex \"{pair[0]}\" will correct file \"{pair[1]}\"")

            regex_pairs = list()
            for s_p in string_pairs:
                regex_pairs.append([re.compile(s_p[0]), re.compile(s_p[1])])

            new_intended_fors = dict()

            for subj in all_intended_for_dirs:

                new_intended_fors[subj] = dict()

                for file_name in all_intended_for_dirs[subj]:
                    print(f"{file_name}")
                    for regex in regex_pairs:
                        if regex[0].search(file_name):
                            new_intended_fors[subj][file_name] = list()
                            for i_f in all_intended_fors[subj][file_name]:
                                if regex[1].search(i_f):
                                    new_intended_fors[subj][file_name].append(i_f)
                                    print(f"found {i_f}")
                            fw.modify_acquisition_file_info(
                                all_intended_for_acq_id[subj][file_name],
                                file_name,
                                {
                                    "set": {
                                        "IntendedFor": new_intended_fors[subj][
                                            file_name
                                        ]
                                    }
                                },
                            )
        else:
            new_intended_fors = all_intended_fors

        if args.verbose > 0:
            intendedfors_writer.writerow(["Final values (after correction)"])

        # write out final values of IntendedFor lists
        intendedfors_writer.writerow(
            [
                "",
                "",
                "",
            ]
        )
        intendedfors_writer.writerow(
            [
                "acquisition label",
                "file name and folder",
                "IntendedFor List of BIDS paths",
            ]
        )

        for subj in all_intended_for_dirs:

            for k, v in all_intended_for_dirs[subj].items():
                do_print(f"{all_intended_for_acq_label[subj][k]}, {k}")
                intendedfors_writer.writerow([all_intended_for_acq_label[subj][k], k])
                for i in v:
                    do_print(f",{i['Folder']}")
                    intendedfors_writer.writerow(["", i["Folder"]])
                    # new_intended_fors[subj][k].sort()
                    for j in new_intended_fors[subj][k]:
                        do_print(f",,{j}")
                        intendedfors_writer.writerow(["", "", j])


def save_acquisition_details(num_subjects, num_sessions):
    """Save acquisition labels count list."""

    with open(
        f"{safe_group_label}_{safe_project_label}_acquisitions_details.csv", mode="w"
    ) as acquisition_file:
        acquisition_writer = csv.writer(
            acquisition_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )

        acquisition_writer.writerow(["Number of subjects", num_subjects])
        acquisition_writer.writerow(["Number of sessions", num_sessions])
        acquisition_writer.writerow([])

        acquisition_writer.writerow(["Unique acquisition label", "total number found"])
        for label, count in acquisition_labels.items():
            acquisition_writer.writerow([label, count])

        # for each acquisition label find the number of times it appears for most subjects
        # subjects_have[subject.label][acquisition.label] = count
        # most_subjects_have_count[acquisition.label][count] will be a count histogram
        # there has to be a better way of doing this
        most_subjects_have_count = dict()

        # go through all subjects
        for subj_label in subjects_have:

            # and all acquisition labels found in any subject
            for acq_label in acquisition_labels:

                # create the "histogram"
                if acq_label not in most_subjects_have_count:
                    most_subjects_have_count[acq_label] = dict()

                if acq_label in subjects_have[subj_label]:

                    count = subjects_have[subj_label][acq_label]

                    if count in most_subjects_have_count[acq_label]:
                        most_subjects_have_count[acq_label][count] += 1
                    else:
                        most_subjects_have_count[acq_label][count] = 1

                else:  # label not seen for subject so count # of times it was missing
                    if 0 in most_subjects_have_count[acq_label]:
                        most_subjects_have_count[acq_label][0] += 1
                    else:
                        most_subjects_have_count[acq_label][0] = 1

        acquisition_writer.writerow([])
        acquisition_writer.writerow(["Acquisition label", "Usual count"])

        # the max of the counts for an acquisition label is what most subjects have
        for acq_label in acquisition_labels:
            max_count = 0
            max_index = 0
            for count, num_count in most_subjects_have_count[acq_label].items():
                if num_count > max_count:
                    max_count = num_count
                    max_index = count
            most_subjects_have[acq_label] = max_index
            acquisition_writer.writerow([acq_label, max_index])

        acquisition_writer.writerow([])
        acquisition_writer.writerow(
            ["Subject", "Acquisition", "Count != to", "Usual count"]
        )
        for subj_label in subjects_have:
            found_problem = False
            acquisition_writer.writerow([subj_label])
            for acq_label in acquisition_labels:
                if acq_label in subjects_have[subj_label]:
                    if (
                        subjects_have[subj_label][acq_label]
                        != most_subjects_have[acq_label]
                    ):
                        found_problem = True
                        acquisition_writer.writerow(
                            [
                                "",
                                acq_label,
                                subjects_have[subj_label][acq_label],
                                most_subjects_have[acq_label],
                            ]
                        )
                else:
                    if most_subjects_have[acq_label] != 0:
                        found_problem = True
                        acquisition_writer.writerow(
                            [
                                "",
                                acq_label,
                                0,
                                most_subjects_have[acq_label],
                            ]
                        )
            if not found_problem:
                acquisition_writer.writerow(
                    [
                        "",
                        "Subject has all of the usual acquisitions, no  more, no less!",
                    ]
                )


def save_acquisitions():
    """Save typical acquisitions and lists of good/bad subjects."""

    with open(
        f"{safe_group_label}_{safe_project_label}_acquisitions.csv", mode="w"
    ) as acquisition_file:
        acquisition_writer = csv.writer(
            acquisition_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )

        acquisition_writer.writerow(["Typical Acquisitions"])
        acquisition_writer.writerow(["Acquisition Label", "Usual Count"])
        for acq_label, usual_count in most_subjects_have.items():
            if usual_count > 0:
                acquisition_writer.writerow([acq_label, usual_count])

        acquisition_writer.writerow([])
        acquisition_writer.writerow(
            ["Subjects that have all of the Typical Acquisitions"]
        )
        troubled_subjects = dict()
        for subj_label in subjects_have:
            no_errors = True
            warnings = False
            troubled_subjects[subj_label] = list()
            for acq_label, usual_count in most_subjects_have.items():
                if acq_label not in subjects_have[subj_label]:
                    if usual_count > 0:
                        no_errors = False
                        troubled_subjects[subj_label].append(
                            f"ERROR: missing {acq_label}"
                        )
                else:
                    subj_has = subjects_have[subj_label][acq_label]
                    most_have = most_subjects_have[acq_label]
                    if subj_has < most_have:
                        no_errors = False
                        troubled_subjects[subj_label].append(
                            f"ERROR: not enough {acq_label} acquisitions.  Found {subj_has}, most have {most_have}"
                        )
                    elif subj_has > most_have:
                        warnings = True
                        if usual_count > 0:
                            troubled_subjects[subj_label].append(
                                f"WARNING: too many {acq_label} acquisitions?  Found {subj_has}, most have {most_have}"
                            )
                        else:
                            troubled_subjects[subj_label].append(
                                f"WARNING: extra {acq_label} acquisition(s)?  Found {subj_has}, most subjects don't have this."
                            )
            if no_errors:
                acquisition_writer.writerow([subj_label])
                if warnings:
                    for warning in troubled_subjects[subj_label]:
                        acquisition_writer.writerow(["", warning])
                else:
                    acquisition_writer.writerow(
                        [
                            "",
                            "This subject has all of the typical acquisitions, no more, no less.",
                        ]
                    )

        acquisition_writer.writerow([])
        acquisition_writer.writerow(["Subjects that don't have Typical Acquisitions"])
        for subj_label, bad_news in troubled_subjects.items():
            acquisition_writer.writerow([subj_label])
            for news in bad_news:
                acquisition_writer.writerow(["", news])


def main():
    global all_df, acquisition_labels, subjects_have, all_intended_for_acq_label, all_intended_for_acq_id, all_intended_for_dirs, all_intended_fors, all_seen_paths

    if args.pickle and Path(PICKLE_FILE_NAME).exists():

        with open(PICKLE_FILE_NAME, "rb") as f:
            data = pickle.load(f)

        all_df = data["all_df"]
        acquisition_labels = data["acquisition_labels"]
        subjects_have = data["subjects_have "]
        all_intended_for_acq_label = data["all_intended_for_acq_label"]
        all_intended_for_acq_id = data["all_intended_for_acq_id"]
        all_intended_for_dirs = data["all_intended_for_dirs"]
        all_intended_fors = data["all_intended_fors"]
        all_seen_paths = data["all_seen_paths"]
        num_subjects = data["num_subjects"]
        num_sessions = data["num_sessions"]
        num_duplicates = data["num_duplicates"]

    else:
        num_subjects, num_sessions, num_duplicates = get_bids_info()

        if (
            args.pickle
        ):  # save all data to a file so it can be just loaded next time (saves time while debugging)
            data = dict()
            data["all_df"] = all_df
            data["acquisition_labels"] = acquisition_labels
            data["subjects_have "] = subjects_have
            data["all_intended_for_acq_label"] = all_intended_for_acq_label
            data["all_intended_for_acq_id"] = all_intended_for_acq_id
            data["all_intended_for_dirs"] = all_intended_for_dirs
            data["all_intended_fors"] = all_intended_fors
            data["all_seen_paths"] = all_seen_paths
            data["num_subjects"] = num_subjects
            data["num_sessions"] = num_sessions
            data["num_duplicates"] = num_duplicates

            with open(PICKLE_FILE_NAME, "wb") as f:
                pickle.dump(data, f)

    save_niftis()

    save_intendedfors()

    save_acquisition_details(num_subjects, num_sessions)

    save_acquisitions()

    if num_duplicates > 0:
        print("ERROR: the following BIDS paths appear more than once:")
        for subject in project.subjects.iter_find():
            for path in all_seen_paths[subject.label]:
                if all_seen_paths[subject.label][path] > 0:
                    print(f"  {path}")
    else:
        print("No duplicates were found.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("group_label", help="fw://group_label/project_label")
    parser.add_argument("project_label", help="fw://group_label/project_label")
    parser.add_argument(
        "-a",
        "--api-key",
        action="store",
        type=str,
        help="api-key (default is to use currently logged in instance",
    )
    parser.add_argument(
        "-i",
        "--intended-for",
        action="store",
        nargs="*",
        type=str,
        help="pairs of regex's specifying field map file name to BIDS Filename",
    )
    parser.add_argument(
        "-p",
        "--pickle",
        action="store_true",
        help="Save/use pickled data instead of getting it multiple times (for debugging)",
    )

    parser.add_argument("-v", "--verbose", action="count", default=0)

    args = parser.parse_args()

    # This works if you are logged into a Flywheel instance on a Terminal:
    if args.api_key:
        fw = flywheel.Client(api_key=args.api_key)
    else:
        fw = flywheel.Client("")

    group_label = args.group_label
    safe_group_label = make_file_name_safe(group_label, replace_str="_")

    project_label = args.project_label
    safe_project_label = make_file_name_safe(project_label, replace_str="_")

    project = fw.projects.find_one(f"group={group_label},label={project_label}")

    # Counts of particular acquisitions
    acquisition_labels = (
        dict()
    )  # acquisition_labels[acquisition.label] = count over entire project
    subjects_have = (
        dict()
    )  # subjects_have[subject.label][acquisition.label] = count for this subject

    all_intended_for_acq_label = dict()
    all_intended_for_acq_id = dict()
    all_intended_for_dirs = dict()
    all_intended_fors = dict()

    all_seen_paths = dict()

    most_subjects_have = dict()

    all_df = pd.DataFrame(columns=COLUMNS)

    # Prints the instance you are logged into to make sure it is the right one.
    print(fw.get_config().site.api_url)

    os.sys.exit(main())
