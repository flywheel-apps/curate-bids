#!/usr/bin/env python3
"""Save BIDS mapping from acquisition names to BIDS paths and fieldmap IntendedFors as sorted csv files.

Note that you need to be logged in to a Flywheel instance using the CLI (fw login ...)
"""

import argparse
import csv
import pandas as pd
import os

import flywheel


def do_print(msg):

    if args.verbose > 0:
        print(msg)


def save_curation_csvs(fw, group_label, project_label):

    project = fw.projects.find_one(f"group={group_label},label={project_label}")

    all_intended_for_acquisition = dict()
    all_intended_for_dirs = dict()
    all_intended_fors = dict()

    all_df = pd.DataFrame(
        columns=(
            "Acquisition label (SeriesDescription)",
            "File name",
            "File type",
            "Curated BIDS path",
        )
    )

    for subject in project.subjects.iter_find():

        do_print(subject.label)

        intended_for_acquisition = dict()
        intended_for_dirs = dict()
        intended_fors = dict()

        nifti_df = pd.DataFrame(
            columns=(
                "Acquisition label (SeriesDescription)",
                "File name",
                "File type",
                "Curated BIDS path",
            )
        )

        ii = 0  # Current acquisition index

        for acquisition in fw.acquisitions.iter_find(f"subject={subject.id}"):

            do_print(f"{ii}  {acquisition.label}")
            for file in acquisition.reload().files:
                if "BIDS" in file.info:
                    if file.info["BIDS"] == "NA":
                        do_print(
                            f"{acquisition.label}, {file.name}, {file.type}, nonBids"
                        )
                        nifti_df.loc[ii] = [
                            acquisition.label,
                            file.name,
                            file.type,
                            f"nonBids",
                        ]
                    else:
                        if not file.info["BIDS"]["ignore"]:
                            do_print(
                                f"{acquisition.label}, "
                                f"{file.name}, "
                                f"{file.type}, "
                                f"{file.info['BIDS']['Folder']}/{file.info['BIDS']['Filename']}"
                            )
                            nifti_df.loc[ii] = [
                                acquisition.label,
                                file.name,
                                file.type,
                                f"{file.info['BIDS']['Folder']}/{file.info['BIDS']['Filename']}",
                            ]
                        else:
                            do_print(
                                f"{acquisition.label}, {file.name}, {file.type}, ignored"
                            )
                            nifti_df.loc[ii] = [
                                acquisition.label,
                                file.name,
                                file.type,
                                "ignored",
                            ]
                    if "IntendedFor" in file.info["BIDS"]:
                        intended_for_acquisition[file.name] = acquisition.label
                        intended_for_dirs[file.name] = file.info["BIDS"]["IntendedFor"]
                        intended_fors[file.name] = file.info["IntendedFor"]
                else:
                    do_print(
                        f"{acquisition.label}, {file.name}, {file.type}, Not_yet_BIDS_curated"
                    )
                    nifti_df.loc[ii] = [
                        acquisition.label,
                        file.name,
                        file.type,
                        f"Not_yet_BIDS_curated",
                    ]
                ii += 1

        nifti_df.sort_values(by=["Curated BIDS path"], inplace=True)

        all_df = all_df.append(nifti_df)

        all_intended_for_acquisition[subject.label] = intended_for_acquisition
        all_intended_for_dirs[subject.label] = intended_for_dirs
        all_intended_fors[subject.label] = intended_fors

    all_df.to_csv(f"{group_label}_{project_label}_niftis.csv", index=False)

    do_print("")

    with open(
        f"{group_label}_{project_label}_intendedfors.csv", mode="w"
    ) as intendedfors_file:
        intendedfors_writer = csv.writer(
            intendedfors_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
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
                do_print(f"{all_intended_for_acquisition[subj][k]}, {k}")
                intendedfors_writer.writerow([all_intended_for_acquisition[subj][k], k])
                for i in v:
                    do_print(f",{i['Folder']}")
                    intendedfors_writer.writerow(["", i["Folder"]])
                    all_intended_fors[subj][k].sort()
                    for j in all_intended_fors[subj][k]:
                        do_print(f",,{j}")
                        intendedfors_writer.writerow(["", "", j])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group_label", help="fw://group_label/project_label")
    parser.add_argument("project_label", help="fw://group_label/project_label")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    args = parser.parse_args()

    # This works if you are logged into a Flywheel instance on a Terminal:
    fw = flywheel.Client("", root=True)

    # Prints the instance you are logged into to make sure it is the right one.
    print(fw.get_config().site.api_url)

    save_curation_csvs(fw, args.group_label, args.project_label)

    os.sys.exit(0)
