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
    for acquisition in fw.acquisitions.iter_find(f"project={project.id}"):

        do_print(f"{ii}  {acquisition.label}")
        for file in acquisition.reload().files:
            if "BIDS" in file.info:
                if file.info["BIDS"] == "NA":
                    print(f"{acquisition.label}, {file.name}, {file.type}, nonBids")
                    nifti_df.loc[ii] = [
                        acquisition.label,
                        file.name,
                        file.type,
                        f"nonBids",
                    ]
                else:
                    if not file.info["BIDS"]["ignore"]:
                        print(
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
                        print(f"{acquisition.label}, {file.name}, {file.type}, Ignored")
                        nifti_df.loc[ii] = [
                            acquisition.label,
                            file.name,
                            file.type,
                            "Ignored",
                        ]
                if "IntendedFor" in file.info["BIDS"]:
                    intended_for_acquisition[file.name] = acquisition.label
                    intended_for_dirs[file.name] = file.info["BIDS"]["IntendedFor"]
                    intended_fors[file.name] = file.info["IntendedFor"]
            else:
                print(f"{acquisition.label}, {file.name}, {file.type}, Not_yet_BIDS_curated")
                nifti_df.loc[ii] = [
                    acquisition.label,
                    file.name,
                    file.type,
                    f"Not_yet_BIDS_curated",
                ]
            ii += 1

    nifti_df.sort_values(by=["Curated BIDS path"], inplace=True)

    nifti_df.to_csv(f"{group_label}_{project_label}_niftis.csv", index=False)

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

        for k, v in intended_for_dirs.items():
            do_print(f"{intended_for_acquisition[k]}, {k}")
            intendedfors_writer.writerow([intended_for_acquisition[k], k])
            for i in v:
                do_print(f",{i['Folder']}")
                intendedfors_writer.writerow(["", i["Folder"]])
                intended_fors[k].sort()
                for j in intended_fors[k]:
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
