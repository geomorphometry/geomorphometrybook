% Read Ponui Island DEM
DEM = GRIDobj("DEMs\ponui_island_dtm.tif");
% Clip the DEM to values that are positive. Non-positive values are 
% set to missing values (nan)
DEM = clip(DEM,DEM>0);
DEM.Z(~bwareaopen(DEM.Z,1e6)) = nan;

% Calculate flow directions
FD  = FLOWobj(DEM);

% Get stream network with a minimum upstream area of 1000 pixels
S   = STREAMobj(FD,'minarea',1e4,'unit','map');

%% Plot
subplot(1,3,[1 2])
A = flowacc(FD);
mn = mnoptimvar(S,DEM,A,"distbins",50,"a0",1);
yl = ylim;
ylim([-10 yl(2)])

c = chitransform(S,A,"mn",mn,'a0',1);

subplot(1,3,3)
imageschs(DEM,'colormap',[1 1 1],'truecolor','k','colorbar',false);
hold on
plotc(S,c);
colormap("turbo")
niceticks
h = colorbar;
h.Label.String = '\chi [m]';