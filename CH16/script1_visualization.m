% Read DEM using readopentopo
DEM = readopentopo("extent",[2 5 42 44],"demtype",'GEBCOIceTopo');
% Reproject to UTM
DEM = reproject2utm(DEM,500);
% Extract the largest inscribed grid that has no missing data
DEM = largestinscribedgrid(DEM);

% Plot a 3D surface plot
surf(DEM,'block',true,'sea',true)
% Adjust colormap
colormap(ttcmap(DEM,'cmap','france'))

% Add a light source, material properties and labels to the plot
ax = gca;
exaggerate(ax,5)
camlight
material dull
niceticks('rotateylabel',false)

ax.LineWidth = 2;
grid(ax,"off")

xlabel('Easting [m]')
ylabel('Northing [m]')
zlabel('Elevation [m]')


