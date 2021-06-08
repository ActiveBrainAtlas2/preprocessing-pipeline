## Time to process for various scripts in the pipeline
1. (pipeline) eodonnell@ratto:pipeline_utility$ time python create_alignment.py --animal DK60 --channel 3 --downsample false
Working on 440 files with 6 cpus
Create aligned files took 13896.714581931941 seconds
real 232m14.334s
1. (pipeline) eodonnell@basalis:pipeline_utility$ time python create_neuroglancer_image.py --animal DK60 --channel 1 --downsample false
Volume shape: (74500, 39500, 440)
Working on 440 files with 6 cpus
Create volume method took 17064.037934793858 seconds
real 285m28.613s
1. (pipeline) eodonnell@ratto:pipeline_utility$ time python create_neuroglancer_image.py --animal DK60 --channel 3 --downsample false
Volume shape: (74500, 39500, 440)
Working on 440 files with 6 cpus
Create volume method took 24231.095115016215 seconds
real 405m19.874s
1. (pipeline) eodonnell@muralis:pipeline_utility$ time python create_neuroglancer_image.py --animal DK60 --channel 2 --downsample false
Volume shape: (74500, 39500, 440)
Working on 440 files with 16 cpus
Create volume method took 42443.63566428702 seconds
real 708m26.091s
1. (pipeline) eodonnell@basalis:pipeline_utility$ time python create_downsampling.py --animal DK60 --channel 1 --downsample false
real 496m49.939s
1. eodonnell@ratto:pipeline_utility$ time python create_downsampling.py --animal DK60 --channel 3 --downsample false
real 565m11.085s
1. eodonnell@muralis:pipeline_utility$ time python create_downsampling.py --animal DK60 --channel 2 --downsample false
real 293m31.508s
1. eodonnell@ratto:pipeline_utility$ time python cni_test.py --animal DK60 --channel 1 --downsample false
Volume shape: (74500, 39500, 10)
Working on 10 files with 6 cpus with 84 chunks
Create volume method took 2575.7160490667447 seconds
real 43m24.024s
1. eodonnell@ratto:pipeline_utility$ time python cni_test.py --animal DK60 --channel 1 --downsample false
Volume shape: (74500, 39500, 10)
Working on 10 files with 6 cpus with 168 chunks
Create volume method took 2610.950981949456 seconds
real 44m13.559s
1. eodonnell@ratto:pipeline_utility$ time python cni_test.py --animal DK60 --channel 1 --downsample false
Volume shape: (74500, 39500, 10)
Working on 10 files with 6 cpus with 42 chunks
Create volume method took 2544.0301611665636 seconds
real 43m3.560s
1. eodonnell@ratto:pipeline_utility$ time python cni_test.py --animal DK60 --channel 1 --downsample false
Volume shape: (74500, 39500, 10)
Working on 10 files with 6 cpus with 6 chunks
Create volume method took 1576.1295652501285 seconds
real 26m52.905s
1. eodonnell@ratto:pipeline_utility$ time python cni_test.py --animal DK60 --channel 1 --downsample false
Volume shape: (74500, 39500, 10)
Working on 10 files with 6 cpus with 1 chunks
Create volume method took 585.9061946049333 seconds
real 10m24.262s
1. eodonnell@ratto:pipeline_utility$ time python cni_test.py --animal DK60 --channel 1 --downsample false
Volume shape: (74500, 39500, 20)
Working on 20 files with 10 cpus with 1 chunks
Create volume method took 735.674988662824 seconds
real 12m51.897s
1. eodonnell@ratto:pipeline_utility$ time python create_clean.py --animal DK60 --channel 3 --downsample false
Working on 440 files with 4 cpus
Create cleaned files took 14100.766661887057 seconds total	 32.04719695883422 per file
real 235m23.764s
1. eodonnell@ratto:pipeline_utility$ time python create_clean.py --animal DK39 --channel 3 --downsample false
Working on 469 files with 4 cpus
Create cleaned files took 7216.117151866667 seconds total	 15.386177296090974 per file
real	122m37.656s








