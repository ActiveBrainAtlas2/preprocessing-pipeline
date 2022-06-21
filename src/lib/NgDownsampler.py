import os
import sys
from cloudvolume import CloudVolume
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from abakit.lib.FileLocationManager import FileLocationManager
from abakit.lib.utilities_cvat_neuroglancer import calculate_chunks, calculate_factors
from abakit.lib.utilities_process import get_cpus


class NgDownsampler:
    def create_downsamples(self):
        """Downsamples the neuroglancer cloudvolume this step is needed to make the files viewable in neuroglancer"""
        chunks = self.get_chunk_size()
        mips = [0, 1, 2, 3, 4, 5, 6, 7]
        if self.downsample:
            mips = [0, 1, 2]
        OUTPUT_DIR = self.fileLocationManager.get_neuroglancer(
            self.downsample, self.channel, rechunck=True
        )
        if os.path.exists(OUTPUT_DIR):
            print(
                f"DIR {OUTPUT_DIR} already exists and not performing any downsampling."
            )
            return
        outpath = f"file://{OUTPUT_DIR}"
        INPUT_DIR = self.fileLocationManager.get_neuroglancer(
            self.downsample, self.channel
        )
        if not os.path.exists(INPUT_DIR):
            print(f"DIR {INPUT_DIR} does not exist, exiting.")
            sys.exit()
        cloudpath = f"file://{INPUT_DIR}"
        self.logevent(f"INPUT_DIR: {INPUT_DIR}")
        self.logevent(f"OUTPUT_DIR: {OUTPUT_DIR}")
        _, workers = get_cpus()
        tq = LocalTaskQueue(parallel=workers)
        tasks = tc.create_transfer_tasks(
            cloudpath,
            dest_layer_path=outpath,
            chunk_size=chunks,
            mip=0,
            skip_downsamples=True,
        )
        tq.insert(tasks)
        tq.execute()
        for mip in mips:
            cv = CloudVolume(outpath, mip)
            chunks = calculate_chunks(self.downsample, mip)
            factors = calculate_factors(self.downsample, mip)
            tasks = tc.create_downsampling_tasks(
                cv.layer_cloudpath,
                mip=mip,
                num_mips=1,
                factor=factors,
                preserve_chunk_size=False,
                compress=True,
                chunk_size=chunks,
            )
            tq.insert(tasks)
            tq.execute()
