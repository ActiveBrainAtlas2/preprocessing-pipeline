import os
import pandas as pd
from timeit import default_timer as timer
import glob
import wget
from timeit import default_timer as timer
import glob
import sqlite3


prep_id = "DK55"
#in_filename = f'{prep_id}-load_test_target_transfer_list.xlsx'
in_filename = f'{prep_id}-load_test_target_transfer_list.tsv.gz'
#out_filename = f'{prep_id}-load_test_results.xlsx'
out_filename = f'{prep_id}-load_test_results.tsv.gz'
#base_url = f'https://activebrainatlas.ucsd.edu/data/{prep_id}/neuroglancer_data/C1/325_325_20000/'
base_url = f'https://imageserv.dk.ucsd.edu/data/{prep_id}/neuroglancer_data/C1/325_325_20000/'


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def speed_test(url):
    local_file = 'tmp.del'
    start_time = timer()
    wget.download(url, local_file)
    end_time = timer()
    elapsed_time = round(end_time - start_time, 2)

    #CLEANUP
    fileList = glob.glob('*.del')
    for filePath in fileList:
        try:
            os.remove(filePath)
        except:
            print("Error while deleting file : ", filePath)

    return elapsed_time


#filtered_df_files_size_array = pd.read_excel(in_filename, engine='openpyxl')
filtered_df_files_size_array = pd.read_csv(in_filename, sep="\t", compression="gzip")
selected_files = filtered_df_files_size_array.loc[filtered_df_files_size_array['selected'] == "1"]
print(f"DATA PULLED FROM FILE: {in_filename}")


    
total_files = selected_files.shape[0]
print(f"TOTAL RECORDS: {total_files}")

macro_start_time = timer()
for index, row in selected_files.iterrows():
    filename = row['fname']
    url = base_url + filename
    elapsed_time = speed_test(url)
    print(index, url)
    print(f"TRANSFER TIME: {elapsed_time}s")
    print(f"PCT_COMPLETE: {round(index/total_files,1)}%")

    #UPDATE DATAFRAME WITH NEW TRANSFER DATE
    filtered_df_files_size_array.loc[filtered_df_files_size_array['fname'] == filename, 'transfer_time'] = elapsed_time

macro_end_time = timer()
macro_elapsed_time = round(macro_end_time - macro_start_time, 2)
#filtered_df_files_size_array.to_excel(out_filename)
filtered_df_files_size_array.to_csv(out_filename, sep="\t", compression="gzip")
print(f"MACRO ELAPSED TIME: {macro_elapsed_time}")