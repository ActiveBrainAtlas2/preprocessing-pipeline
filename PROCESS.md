### New Brain
## Post TIF Creation Process
1. To install the software prerequisites, [look here](README.md)
1. Create thumbnails on all channels- Litao's new script
1. Create cleaned images and masks on CH1 
1. Run masks against CH2 and CH3 
1. Look at images and determine what kind of rotation is necessary.
1. Rotate all channels
1. Run alignment on thumbnail CH1 
1. Use alignment results from CH1 to align thumbnail CH2 and CH3
1. Run neuroglancer on all aligned thumbnail dirs
1. Test viewing with neuroglancer
1. Run alignment on all big images on all 3 channels
1. Run neuroglancer on all 3 big aligned directories
1. View finished product in neuroglancer

### Actual scripts run on DK43 for 3 channels for Neuroglancer

1. python create-masks.py 
1. Visually inspect files in the: /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps/cleaned
to determine which way to rotate and/or flip. Also get the maximum width and height with:
for i in *.tif; do identify $i; done | awk '{print $4}' | sort -n
1. python clean_with_mask.py --animal DK43 --channel 1 --rotation 1 --flip flop
1. python clean_with_mask.py --animal DK43 --channel 2 --rotation 1 --flip flop
1. python clean_with_mask.py --animal DK43 --channel 3 --rotation 1 --flip flop
1. python alignment.py --animal DK43 --njobs 10 --channel 1
1. python alignment.py --animal DK43 --njobs 10 --channel 2
1. python alignment.py --animal DK43 --njobs 10 --channel 3
1. python precompute_images_local.py --animal DK43 --channel 1 --resolution thumb
1. python precompute_images_local.py --animal DK43 --channel 2 --resolution thumb
1. python precompute_images_local.py --animal DK43 --channel 3 --resolution thumb
