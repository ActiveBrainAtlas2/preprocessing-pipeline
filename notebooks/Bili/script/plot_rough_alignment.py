#!/usr/bin/env python
from argparse import ArgumentParser
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parent.parent

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('brain')
    parser.add_argument('--workdir', type=Path)
    parser.add_argument('--zstep', type=int, default=10)
    args = parser.parse_args()

    data_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data')
    work_dir = ROOT / 'data/rough-alignment' / args.brain
    work_dir.mkdir(parents=True, exist_ok=True)

    img_wrp = np.load(work_dir / f'img-wrp.npy')
    img_fix = np.load(work_dir / f'img-fix.npy')
    img_diff = img_wrp - img_fix
    
    with PdfPages(work_dir / f'diagnostic.pdf') as pdf:
        sz = img_fix.shape[-1]
        for z in range(0, sz, args.zstep):
            print(f'{z}/{sz}')
            px = 1 / plt.rcParams['figure.dpi']
            fig, ax = plt.subplots(1, 3, dpi=250, figsize=(8, 6))
            kwargs = {
                'aspect':'equal',
                'cmap': 'gray',
            }
            ax[0].imshow(img_wrp[:,:,z], **kwargs)
            ax[0].set_title('DK52 transformed')
            ax[0].set_axis_off()
            ax[1].imshow(img_fix[:,:,z], **kwargs)
            ax[1].set_title(f'{args.brain} fixed')
            ax[1].set_axis_off()
            kwargs['cmap'] = 'coolwarm'
            kwargs['vmin'] = -1
            kwargs['vmax'] = 1
            ax[2].imshow(img_diff[:,:,z], **kwargs)
            ax[2].set_title(f'DK52 (red) - {args.brain} (blue)')
            ax[2].set_axis_off()
            fig.suptitle(f'z = {z}')
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close()

    with PdfPages(work_dir / f'diagnostic-alt.pdf') as pdf:
        sz = img_fix.shape[-1]
        for z in range(0, sz, args.zstep):
            print(f'{z}/{sz}')
            kwargs = {
                'aspect':'equal',
                'cmap': 'gray',
            }

            fig, ax = plt.subplots(1, 1, dpi=200, figsize=(8, 6))
            ax.imshow(img_wrp[:,:,z].T, **kwargs)
            ax.set_title(f'DK52 transformed\nz = {z}')
            ax.set_axis_off()
            pdf.savefig(fig)
            plt.close()

            fig, ax = plt.subplots(1, 1, dpi=200, figsize=(8, 6))
            ax.imshow(img_fix[:,:,z].T, **kwargs)
            ax.set_title(f'{args.brain} fixed\nz = {z}')
            ax.set_axis_off()
            pdf.savefig(fig)
            plt.close()
