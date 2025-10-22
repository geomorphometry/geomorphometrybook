% Download DEM (Copernicus DEM) for specified extent in lat/lon 
ext = [8.50   9.65   41.32   43.05];
DEM = readopentopo("extent",ext,"demtype","COP90");

% Clip the DEM to values that are positive. Non-positive values are 
% set to missing values (nan)
DEM = clip(DEM,DEM>0);
% Reproject to utm
DEM = reproject2utm(DEM,90);
% Interpolate missing values surrounded by valid values
% using laplacian interpolation
DEM = inpaintnans(DEM);

% Calculate flow directions
FD  = FLOWobj(DEM);
% Calculate flow accumulation
A   = flowacc(FD);

% Get stream network with a minimum upstream area of 1000 pixels
S   = STREAMobj(FD,'minarea',1000);

% The following code finds the main divide and generates the plots
% shown in the chapter

% Identify northern- and southernmost tip
I = ~isnan(DEM);
I.Z = bwareaopen(I.Z,1e5);
DEM = clip(DEM,I);
[r,c]    = find(DEM);

[~,ixx] = min(r);
I.Z(1:r(ixx),c(ixx)) = true;

[~,ixx] = max(r);
I.Z(r(ixx):end,c(ixx)) = true;

RightBasins = imdilate(imclearborder(~I.Z,8,"Borders","left"),ones(3));
LeftBasins = imdilate(imclearborder(~I.Z,8,"Borders","right"),ones(3));

DRight = drainagebasins(FD,find(~isnan(DEM) & RightBasins));
DLeft = drainagebasins(FD,find(~isnan(DEM) & LeftBasins));

DIV   = dilate(DRight>0,ones(3)) & dilate(DLeft>0,ones(3));


%% Plot
subplot(1,3,[1 2])
A = flowacc(FD);
mn = mnoptimvar(S,DEM,A,"distbins",50,"a0",1);
yl = ylim;
ylim([-10 yl(2)])

c = chitransform(S,flowacc(FD),"mn",mn,'a0',1);

subplot(1,3,3)
imageschs(DEM,clip(dilate(DIV,ones(5)),~isnan(DEM)),'truecolor','k','colorbar',false);
hold on
plotc(S,c);
colormap("turbo")
niceticks
h = colorbar;
h.Label.String = '\chi [m]';