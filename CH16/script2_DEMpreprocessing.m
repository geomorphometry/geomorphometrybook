% Load DEM
DEM = GRIDobj('srtm_bigtujunga30m_utm11.tif');
% Compute flow directions using FLOWobj
FD  = FLOWobj(DEM);
% Quantile carving
DEMc = quantcarve(FD,DEM,0.3);

% The remaining code generates the plots in the chapter
ix = [366233  325759];
[X,Y] = getcoordinates(DEM,'mat');
MASK  = X>=min(X(ix)) & X<=max(X(ix)) & ...
        Y>=min(Y(ix)) & Y<=max(Y(ix));
MASK  = GRIDobj(DEM,MASK);

S = STREAMobj(FD,minarea = 1000);
S = klargestconncomps(S);
S = trunk(S);

S = subgraph(S,getnal(S,MASK));

%%
subplot(2,2,1)
imageschs(crop(DEM,ix),'colormap','landcolor','colorbarylabel','Elevation [m]')
mapshow(GRIDobj2polygon(crop((fillsinks(DEM)-DEM)>0,ix)),'FaceColor','none')
hold on
plot(S,'k','LineWidth',1.5)
hold off
niceticks

subplot(2,2,2)
imageschs(crop(DEMc,ix),crop(DEMc-DEM,ix),'colormap',ttscm('vik'),'clim',[-20 20],...
    'colorbarylabel','Elevation changed [m]')
mapshow(GRIDobj2polygon(crop((fillsinks(DEM)-DEM)>0,ix)),'FaceColor','none')
hold on
plot(S,'k','LineWidth',1.5)
niceticks

z = getnal(S,DEM);
zc = getnal(S,DEMc);
subplot(2,2,[3 4])
hold on
plotdzshaded(S,[max(zc,z) z],'FaceColor','r');
plotdzshaded(S,[min(zc,z) z],'FaceColor','b');
plotdz(S,DEM,'color',[.5 .5 .5])
plotdz(S,DEMc,'color','k')
hold off
box on
legend('Filled pixels','Carved pixels','Original profile','Quantile carving',...
    'Location','southeast','EdgeColor','none')

spl = subplotlabel(gcf,'A');
