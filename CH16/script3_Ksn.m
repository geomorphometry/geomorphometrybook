% Download DEM (Copernicus DEM) for specified extent in lat/lon
ext = [82.35   86.1   27.2   29.9];
DEM = readopentopo("extent",ext,"demtype","COP90");
% Reproject to UTM
DEM = reproject2utm(DEM,90);
% Extract the largest inscribed grid that has no missing data
DEM = largestinscribedgrid(DEM);

% Calculate FLOW directions
FD = FLOWobj(DEM);
% Delineate the stream network with a minimum upstream area of 
% 1000 pixels
S = STREAMobj(FD,'minarea',1000);
% Extract the largest drainage basin
S = klargestconncomps(S,1);

% Calculate flow accumulation
A = flowacc(FD);
% Calculate Ksn using theta = 0.45 and smoothing parameter K = 1000
k = ksn(S,DEM,A,0.45,1000);

% The remaining code generates the plots as shown in the chapter
ax = subplot(1,2,1);
imageschs(DEM,'colormap',[1 1 1],'colorbar',false)
hold on
plotc(S,k,'linewidth',2); 
clim([0 1500])
colormap("turbo")
h = colorbar;
h.Label.String = 'k_{sn} [m^{0.9}]';

xlabel('Easting [m]')
ylabel('Northing [m]')
setextent(S,gca);
padextent([10 10 0 10]*1000,gca);
niceticks

% Create SWATHobj
xsw = [268695 195715] + 75000;
ysw = [3233745 3035565];
SW  = SWATHobj(DEM,xsw,ysw,'width',75000,'dx',100,'dy',100);
SW2 = mapswath(SW,S,k);

plot(SW,"legend",false)

ax = subplot(1,2,2);
plotdz(SW)
ylabel('Elevation [m]')
yyaxis right

h = gca;
clr = h.YAxis(2).Color;

plotdz(SW2,"meancolor",clr)
xlabel('N-S distance [m]')
ylabel('k_{sn} [m]')
ylim([0 1000])

xlim([0 max(SW.distx)])
