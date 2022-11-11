"""
IMPORT FOUNDATION BRAIN IMAGES' VERTICIES INTO DB (WITH ALIGNMENT AND SCALING)

CREATED: 18-MAR-2022
LAST EDIT: 18-MAR-2022
AUTHORS: DUANE RINEHART

SECONDARY IMPORT OF ANNOTATIONS (REVIEWED), ALIGN POINTS, INSERT INTO DB

"""

import os
import re
import sys
import binascii  # unique segment id (contour) ref: https://github.com/google/neuroglancer/blob/master/python/neuroglancer/random_token.py
import pandas as pd

from django.urls import register_converter
import plotly.graph_objects as go

# WORKAROUND FOR PYTHONPATH (BEFORE OTHER IMPORTS)
src = "/net/birdstore/common_programming/pipeline_utility/src"
sys.path.append(src)

from tqdm import tqdm
from pipeline.utilities.utilities_alignment import transform_points, create_downsampled_transforms
from pipeline.utilities.utilities_create_alignment import parse_elastix
import numpy as np
from pipeline.utilities.utilities_process import get_image_size
from atlas.FoundationContourAligner import FoundationContourAligner
from pipeline.lib.sql_setup import session
from model.structure import Structure
from Brain import Brain

dest_db_schema = "dev2_test"
out_path = "/net/birdstore/drinehart/img_compare/"
src_contours = os.path.join(out_path, "compare_v2.xlsx")


def load_contours():
    """LOAD IN DUPLICATED (POTENTIALY) SETS OF CONTOURS (POINTS)"""
    in_contours = pd.read_excel(
        os.path.join(src_contours),
        engine="openpyxl",
    )
    return in_contours[["MOUSE", "SECTION", "STRUCTURE", "STRUCTURE_ID", "GOOD"]]


def load_transform(animal):
    transforms = parse_elastix(animal)
    downsampled_transforms = create_downsampled_transforms(
        animal, transforms, downsample=False
    )
    downsampled_transforms = sorted(downsampled_transforms.items())
    transform_per_section = {}
    for section, transform in downsampled_transforms:
        section_num = int(section.split(".")[0])
        transform = np.linalg.inv(transform)
        transform_per_section[section_num] = transform
    return transform_per_section


def get_structure_table_correspondance():
    rows = session.query(Structure).all()
    results = {}
    for row in rows:
        results[row.abbreviation] = [row.id, row.description]
    return results


def insert_into_db(
    prep_id,
    FK_structure_id,
    FK_owner_id,
    FK_input_id,
    label,
    x,
    y,
    z,
    active,
    segment_id,
    ordering_int,
):

    sql_statement = f"INSERT INTO {dest_db_schema}.annotations_points (prep_id, FK_structure_id, FK_owner_id, FK_input_id, label, x, y, z, active, segment_id, ordering) VALUES ('{prep_id}','{FK_structure_id}', '{FK_owner_id}', '{FK_input_id}', '{label}',  '{x}', '{y}', '{z}', '{active}', '{segment_id}', '{ordering_int}')"
    session.execute(sql_statement)
    session.commit()


def get_offsets(animal):
    braini = Brain(animal)
    section_size = np.array(
        (braini.sqlController.scan_run.width, braini.sqlController.scan_run.height)
    )
    downsampled_section_size = np.round(section_size).astype(int)
    INPUT = os.path.join(braini.path.prep, "CH1", "full")
    files = sorted(os.listdir(INPUT))
    section_offsets = {}
    for file in tqdm(files):
        filepath = os.path.join(INPUT, file)
        width, height = get_image_size(filepath)
        width, height = int(width), int(height)
        downsampled_shape = np.array((width, height))
        section = int(file.split(".")[0])
        section_offsets[section] = (downsampled_section_size - downsampled_shape) / 2
    return section_offsets


def main():
    # DEFAULTS
    FK_owner_id = "4"  # ALL OWNED BY USER 'dk'
    FK_input_id = "1"  # ALL MANUAL
    active = "1"

    # SINGLE QRY TO GET STRUCTURE DATA
    structure_data = get_structure_table_correspondance()

    contours = load_contours()

    print("LOG:")

    print("PROGRESS", "MOUSE", "SECTION", "STRUCTURE", "GOOD", sep=" : ")
    for index, row in contours.iterrows():
        animal = row["MOUSE"]
        section_offsets = get_offsets(animal)
        transform_per_section = load_transform(animal)

        # ***PARSE X,Y VALUES (VERTICES)***
        # REMOVE BRACKETS FROM STRING
        lstcontour_points1 = re.sub(r"[\([{})\]]", "", row["GOOD"]).split("\n")

        # CAPTURE X,Y ANNOTATION POINTS PER STRUCTURE, PER SECTION
        # aligner = FoundationContourAligner(animal, atlas='atlasV8')

        # aligner.load_contours_for_Foundation_brains()

        lstpairs1 = []
        # LIST OF TUPLES - EACH TUPLE HAS X,Y POINTS
        for pairs in lstcontour_points1:
            lstpair = list(
                filter(str.strip, pairs.split(" "))
            )  # REMOVE STRINGS ELEMENTS THAT ONLY CONTAIN WHITESPACE (NULL) FROM LIST
            pair = (float(lstpair[0]), float(lstpair[1]))
            lstpairs1.append(pair)

        label = row["STRUCTURE"].strip()

        ordering_int = 0
        # 20-byte (40 character) random hex string
        segment_id = binascii.hexlify(os.urandom(20)).decode()
        z = row["SECTION"]

        contour_per_structure_per_section = {}
        contour_per_structure_per_section[label] = {z: lstpairs1}

        output = ""
        for (
            structure_name,
            dict_section_x_y_pairs,
        ) in contour_per_structure_per_section.items():
            output += (
                f"DEBUG - [{animal}] (structure/brain region):"
                + str(structure_name)
                + "; QTY:"
                + str(len(dict_section_x_y_pairs))
                + "\n"
            )
            print(
                f"DEBUG - ANIMAL: {animal}, (structure/brain region):",
                structure_name,
                "; QTY:",
                len(dict_section_x_y_pairs),
            )

            if structure_name == "RtTg_S":
                structure_name = "RtTg"
            FK_structure_id = structure_data.get(structure_name)[
                0
            ]  # LOOKUP STRUCTURE ID
            aligned_points = []
            # LOOP THROUGH EACH SET OF X,Y PAIRS PER SECTION
            for sectioni, contour_points_sectioni in dict_section_x_y_pairs.items():

                # VARIABLE DATA (transform_per_section) EXAMPLE:
                # contour_points_sectioni = ... dictionary key=section, value=array of x,y
                print(
                    sectioni, len(contour_points_sectioni)
                )  # , contour_points_sectioni)

                # ALIGN POINTS (MUST SEND IN X,Y PAIR FOR TRANSFORMATION)

                md585_fixes = {
                    161: 100,
                    182: 60,
                    223: 60,
                    231: 80,
                    229: 76,
                    253: 8,
                    253: 60,
                }
                offset = section_offsets[sectioni]
                if animal == "MD585" and sectioni in md585_fixes.keys():
                    offset = offset - np.array([0, md585_fixes[sectioni]])
                if animal == "MD589" and sectioni == 297:
                    offset = offset + np.array([0, 35])
                if animal == "MD589" and sectioni == 295:
                    offset = offset + np.array([7, 11])
                contour_points_sectioni = np.array(contour_points_sectioni) + offset
                aligned_contour_points_sectioni = transform_points(
                    np.array(contour_points_sectioni), transform_per_section[sectioni]
                )
                # aligned_contour_points_sectioni = aligned_contour_points_sectioni*32

                ordering_int = 0
                segment_id = binascii.hexlify(
                    os.urandom(20)
                ).decode()  # 20-byte (40 character) random hex string

                np_scaled_x_y_pairs = (
                    np.array(aligned_contour_points_sectioni) * 0.452
                )  # APPLY SCALING FACTOR (x *.452, y * .452)
                z = np.uint32(sectioni).item() * 20  # APPLY SCALING FACTOR (z * 20)

                for row in np_scaled_x_y_pairs:
                    x = row[0]
                    y = row[1]
                    label = structure_name

                    FK_structureid = 54  # SET STRUCTUREID TO 'polygon' SO NEUROGLANCER WILL DRAW CONTOURS (LABEL NOT AFFECTED)

                    # INSERT INTO DB

                    if label == "VCP_R" and animal == "MD594" and z == 6720:
                        FK_structure_id = 54
                        print(
                            animal,
                            FK_structure_id,
                            FK_owner_id,
                            FK_input_id,
                            label,
                            x,
                            y,
                            z,
                            active,
                            segment_id,
                            ordering_int,
                        )
                        insert_into_db(
                            animal,
                            FK_structure_id,
                            FK_owner_id,
                            FK_input_id,
                            label,
                            x,
                            y,
                            z,
                            active,
                            segment_id,
                            ordering_int,
                        )

                    ordering_int += 1


if __name__ == "__main__":
    main()
