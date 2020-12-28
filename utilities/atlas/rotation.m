p0 = [569.79 1051.91 227.88];
p1 = [496.41 649.5 224.22];
% calculate cross and dot products
C = cross(p0, p1) ; 
D = dot(p0, p1) ;
NP0 = norm(p0) ; % used for scaling
if ~all(C==0) % check for colinearity    
    Z = [0 -C(3) C(2); C(3) 0 -C(1); -C(2) C(1) 0] ; 
    R = (eye(3) + Z + Z^2 * (1-D)/(norm(C)^2)) / NP0^2 ; % rotation matrix
else
    R = sign(D) * (norm(p1) / NP0) ; % orientation and scaling
end
% R is the rotation matrix from p0 to p1, so that (except for round-off errors) ...
R * p0      % ... equals p1 
inv(R) * p1 % ... equals p0
