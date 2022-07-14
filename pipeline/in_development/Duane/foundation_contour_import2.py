"""
IMPORT FOUNDATION BRAIN IMAGES' VERTICIES INTO DB (WITH ALIGNMENT AND SCALING)

CREATED: 17-MAR-2022
LAST EDIT: 18-MAR-2022
AUTHORS: ZHONGKAI AND DUANE

READ FOUNDATION BRAIN IMAGE ANNOTATIONS, ALIGN POINTS, INSERT INTO DB

"""

import os
import sys
import binascii

# from django.urls import register_converter
# import plotly.graph_objects as go

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
    # animals = ['MD585', 'MD589', 'MD594'] #FOUNDATIONAL BRAIN prep_id
    animals = ["MD594"]
    FK_owner_id = "4"  # ALL OWNED BY USER 'dk'
    FK_input_id = "1"  # ALL MANUAL
    active = "1"

    # SINGLE QRY TO GET STRUCTURE DATA
    structure_data = get_structure_table_correspondance()

    for animal in animals:
        section_offsets = get_offsets(animal)
        transform_per_section = load_transform(animal)

        # CAPTURE X,Y ANNOTATION POINTS PER STRUCTURE, PER SECTION
        aligner = FoundationContourAligner(animal, atlas="atlasV8")
        aligner.load_contours_for_Foundation_brains()

        output = ""
        for (
            structure_name,
            dict_section_x_y_pairs,
        ) in aligner.contour_per_structure_per_section.items():
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

            FK_structure_id = structure_data.get(structure_name)[
                0
            ]  # LOOKUP STRUCTURE ID
            aligned_points = []
            # LOOP THROUGH EACH SET OF X,Y PAIRS PER SECTION
            for sectioni, contour_points_sectioni in dict_section_x_y_pairs.items():

                # FILTER PROBLEMATIC SETS *WILL ADD LATER
                if (
                    animal == "MD594"
                    and str(structure_name) == "VLL_R"
                    and (str(sectioni) == "300" or str(sectioni) == "308")
                ):
                    continue
                if (
                    animal == "MD594"
                    and str(structure_name) == "VLL_L"
                    and str(sectioni) == "150"
                ):
                    continue
                if (
                    animal == "MD594"
                    and str(structure_name) == "VCP_R"
                    and (str(sectioni) == "332" or str(sectioni) == "336")
                ):
                    continue
                if (
                    animal == "MD589"
                    and str(structure_name) == "RtTg_S"
                    and (
                        str(sectioni) == "220"
                        or str(sectioni) == "222"
                        or str(sectioni) == "223"
                        or str(sectioni) == "240"
                    )
                ):
                    continue
                if (
                    animal == "MD589"
                    and str(structure_name) == "Sp5I_R"
                    and (str(sectioni) == "337")
                ):
                    continue
                if (
                    animal == "MD589"
                    and str(structure_name) == "VLL_L"
                    and (str(sectioni) == "155")
                ):
                    continue

                # VARIABLE DATA (transform_per_section) EXAMPLE:
                # contour_points_sectioni = ... dictionary key=section, value=array of x,y
                # print(sectioni, contour_points_sectioni)

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
                    # if label=='VCP_R' and (z == 6680 or z ==6700 or z ==6740 or z == 6760 or z ==	6780 or z ==	6800 or z ==	6840 or z ==	6860 or z ==	6880 or z ==	6900 or z ==	6920 or z ==	6940 or z ==	6960 or z ==	6980 or z ==	7000 or z ==	7020 or z ==	7040 or z ==	7060 or z ==	7080 or z ==	7100 or z ==	7120 or z ==	7140 or z ==	7160):
                    FK_structure_id = 54  # polygon
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
