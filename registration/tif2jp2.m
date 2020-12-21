function tif2jp2(INPUT, OUTPUT)
    parpool('local',6);
    pctRunOnAll maxNumCompThreads(1);
    imglist = dir(strcat(INPUT, '*.tif'));
    [count, a] = size(imglist);

    parfor i = 1 : count
        maxNumCompThreads();
        imgpath = (strcat(imglist(i).folder, '/', imglist(i).name));
        [sPath, sFilename, sExt] = fileparts( imgpath );
        jp2path = (strcat(OUTPUT, '/', sFilename, '.jp2'));
        if ~exist(jp2path, 'file')
            tif = imread(imgpath);
            disp(strcat('Working on ', jp2path));
            imwrite(tif, jp2path)
        end

    end
end
