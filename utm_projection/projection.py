import rasterio
# import numpy as np
from pyproj import CRS, Transformer
from rasterio.warp import calculate_default_transform, Resampling,reproject
from pyproj.database import query_utm_crs_info
from pyproj.aoi import AreaOfInterest
import geopandas as gpd

def check_utm_epsg(epsg_code):
# def is_utm_epsg(epsg_code):
    try:
        crs = CRS.from_epsg(epsg_code)
        return crs.coordinate_operation.method_name == "Transverse Mercator"
    except Exception as e:
        return False


def utm_finder(src_crs,bbox=[]):
    try:
        """
        Find UTM epsg
        raster: input raster path
        Returns:
        UTM EPSG code of the input raster
        """
        # with rasterio.open(raster_file_path) as dataset:  
            # src_epsg=dataset.crs.to_epsg()
            # bbox  = dataset.bounds
        bbox_wgs84 = rasterio.warp.transform_bounds(src_crs,'EPSG:4326', bbox[0],bbox[1],bbox[2],bbox[3])
        utm_crs_list = query_utm_crs_info(     
            datum_name='WGS 84',
            area_of_interest= AreaOfInterest(
            west_lon_degree=bbox_wgs84[0],
            south_lat_degree=bbox_wgs84[1],
            east_lon_degree=bbox_wgs84[2],
            north_lat_degree=bbox_wgs84[3],),) 

        # utm_crs = '{}:{}'.format(utm_crs_list[0].auth_name,utm_crs_list[0].code)
        utm_epsg = utm_crs_list[0].code
        print(utm_epsg,"utm_epsg")
        return True,utm_epsg
    except Exception as e:
        return False, str(e)
    

def raster_projection(file_path, out_path):
    try:
        ds = rasterio.open(file_path)
        #check raster crs and reproject if necessary
        ds_crs_epsg=ds.crs.to_epsg()
        is_UTM_epsg=check_utm_epsg(ds_crs_epsg)

        print(ds_crs_epsg)
        print(is_UTM_epsg)

        if not is_UTM_epsg:
            bbox  = ds.bounds
            success,dst_utm_epsg=utm_finder(ds_crs_epsg,bbox)
            if not success:
                error=str(dst_utm_epsg)
            src_crs=CRS.from_epsg(ds_crs_epsg) 
            dst_crs = CRS.from_epsg(dst_utm_epsg) 
            transformer=Transformer.from_crs(src_crs,dst_crs)
            dst_transform, width, height = calculate_default_transform(
                src_crs.to_string(), dst_crs.to_string(), ds.width, ds.height, *ds.bounds
            )
            kwargs = ds.meta.copy()
            kwargs.update({
                        'crs': dst_crs.to_string(),
                        'transform': dst_transform,
                        'width': width,
                        'height': height})
            with rasterio.open(out_path, 'w', **kwargs) as dst:
                for i in range(1, ds.count + 1):
                    reproject(
                        source=rasterio.band(ds, i),
                        destination=rasterio.band(dst, i),
                        src_transform=ds.transform,
                        src_crs=src_crs.to_string(),
                        dst_transform=dst_transform,
                        dst_crs=dst_crs.to_string(),
                        resampling=Resampling.nearest)
            ds.close()
            dst.close()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def vector_projection(file_path, out_path):
    try:
        gdf = gpd.read_file(file_path)
        gdf.set_crs(epsg=4326, inplace=True)
        gdf_crs = gdf.crs.to_epsg()
        print(gdf_crs)
        is_UTM_epsg=check_utm_epsg(gdf_crs)
        print(is_UTM_epsg,"is_UTM_epsg")

        if not is_UTM_epsg:
            gdf_bbox  = gdf.total_bounds
            min_x, min_y, max_x, max_y = gdf_bbox
            bbox=[min_x, min_y, max_x, max_y]
            
            success,dst_utm_epsg=utm_finder(gdf_crs,bbox)
            # dst_utm_epsg=32635
            
            if not success:
                error=str(dst_utm_epsg)
                print(f"error in finding utm: {error}")
            
            target_crs = CRS.from_epsg(dst_utm_epsg).to_string()
            gdf = gdf.to_crs(target_crs)
            print(gdf.crs.to_epsg,"jnfjdb")
            
            gdf.to_file(out_path, driver='ESRI Shapefile')
        return True, "Success"
    except Exception as e:
        return False, str(e)