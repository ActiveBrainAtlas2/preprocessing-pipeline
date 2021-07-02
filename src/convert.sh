#!/bin/bash


width=1037
height=1126

#Now convert your percentages to pixels as variables, for example

#####xoff=$(convert xc: -format "%[fx:$width*5/100]" info:)
yoff=$(convert xc: -format "%[fx:$height*2/100]" info:)
ww=$(convert xc: -format "%[fx:$width*100/100]" info:)
hh=$(convert xc: -format "%[fx:$height*60/100]" info:)

xoff=0
#yoff=0
convert $1 -crop ${ww}x${hh}+${xoff}+${yoff} +repage  -depth 8 ../thumbnail_aligned/$1
