function transform_fast_marmo(img_path, recon_path, output_dir)

    imglist = dir(strcat(img_path, '*.tif'));
    % geometry_name = strcat(csv_path, '/geometry.csv');
    % meta_data = readtable(geometry_name, 'ReadRowNames',true);
    dx = [1,1] * 0.35;
    [count, a] = size(imglist);
    disp('Files to work on:')
    disp(count);


    for i = 1 : count

        txtfile = strcat(recon_path, imglist(i).name(1:end-4), '_small_to_input_matrix.txt');

        if exist(txtfile, 'file') == 2
                disp(strcat('transforming', {' '}, imglist(i).name(1:end-4)));
                J = imread(strcat(imglist(i).folder, '/', imglist(i).name));
                J = double(J)/65535.0;


                % build the location of each pixel, it is zero centered
                xJ = (1 : size(J,2))*dx(1); xJ = xJ - mean(xJ);
                yJ = (1 : size(J,1))*dx(2); yJ = yJ - mean(yJ);

                %%
                % build a correction for the 3D affine
                % first rename variables to be consistent with apply_deformation
                % x=xJ; %padding size needed here bigtif
                % y=yJ;



                x = (1:36000) * dx(1); x = x - mean(x);
                y = (1:56000) * dx(2); y = y - mean(y);

                % %%%%
                % x = (1 : size(J,2))*dx(1); x = x - mean(x);
                % y = (1 : size(J,1))*dx(2); y = y - mean(y);
                % %%%%%%%%%


                % zJ = z;
                [X,Y] = meshgrid(x,y);
                % f = geometry_ind;


                    A2dtot = dlmread(txtfile);
                    AJphiJAxyX = A2dtot(1,1)*X + A2dtot(1,2)*Y + A2dtot(1,3);
                    AJphiJAxyY = A2dtot(2,1)*X + A2dtot(2,2)*Y + A2dtot(2,3);
                    % now deform J with this                                                                                                                               
                    Jrecon = zeros(56000,36000);
                    %%%%%%%%%%%%%%%%%%%%%%%%%
                    % Jrecon = zeros(size(J));
                    F = griddedInterpolant({yJ,xJ},double(J(:,:)),'nearest','none');
                    Jrecon(:,:) = F(AJphiJAxyY,AJphiJAxyX);

                    Jrecon(isnan(Jrecon)) = 0;
                    Jrecon = Jrecon * 65535.0;
                    Jrecon = uint16(Jrecon);
                    imwrite(Jrecon, strcat(output_dir, imglist(i).name(1:end-4),'.tif'),'Compression', 'none')%end-13

                    % [oldy, oldx, ch] = size(J);
                    % padding_on_left = (28000 - oldx)/2;
                    % padding_on_top = (22000 - oldy)/2;
                    % nx = 28000;
                    % ny=22000;
                    % nz = 1;
                    % ddx = 0.92;
                    % ddy = 0.92;
                    % ddz = 20;
                    % x0 = meta_data([imglist(i).name(1:end-4),'.tif'],7).Variables;
                    % y0 = meta_data([imglist(i).name(1:end-4),'.tif'],8).Variables;
                    % x0 = x0 - padding_on_left*ddx;
                    % y0 = y0 - padding_on_top*ddy;
                    % z0 = meta_data([imglist(i).name(1:end-4),'.tif'],9).Variables;
                    % fid = fopen(strcat(output_dir, imglist(i).name(1:end-4),'.csv'), 'wt');
                    % fprintf(fid, 'filename, nx, ny, nz, dx, dy, dz, x0, y0, z0 \n');
                    % fprintf(fid, '%s, %f, %f, %f, %f,%f, %f, %f, %f, %f', [imglist(i).name(1:end-4),'.jp2'], nx, ny, nz, ddx, ddy, ddz, x0, y0, z0);
                    % fclose(fid);

                end
    end


