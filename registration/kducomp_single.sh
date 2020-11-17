filename=$1
output_dir=$2


outfile=$(echo $filename | sed 's/\.tif/\.jp2/g')
# outfile=${outfile/"$filename"/}
echo "Saving $filename in KDU to $outfile"
kdu_compress -i $filename -o "$output_dir/${outfile}" -rate 1 Creversible=yes Clevels=7 Clayers=8 Stiles=\{1024,1024\} Corder=RPCL Cuse_sop=yes ORGgen_plt=yes ORGtparts=R Cblk=\{32,32\} -num_threads 1
echo " "
#rm -vf $filename
