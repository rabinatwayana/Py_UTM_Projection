import rasterio
from pyproj import CRS, Transformer
from rasterio.warp import calculate_default_transform, Resampling,reproject
from pyproj.database import query_utm_crs_info
from pyproj.aoi import AreaOfInterest
import geopandas as gpd
from shapely.geometry import box

def bbox_from_utm_epsg(epsg_code):
    """
    Get the bounding box for a given UTM EPSG code.
    
    Parameters:
    - epsg_code: The UTM EPSG code.
    
    Returns:
    - bbox: A tuple representing the bounding box (min_x, min_y, max_x, max_y) in WGS84 coordinates.
    """
    try:
        if not (32601 <= int(epsg_code) <= 32660 or 32701 <= int(epsg_code) <= 32760):
            raise ValueError("EPSG code must be in the range 32601-32660 (northern hemisphere) or 32701-32760 (southern hemisphere).")
        zone_number = int(str(epsg_code)[-2:])
        northern_hemisphere = int(epsg_code) < 32700

        min_lon = (zone_number - 1) * 6 - 180
        max_lon = zone_number * 6 - 180
        min_lat = 0 if northern_hemisphere else -80
        max_lat = 84 if northern_hemisphere else 0
        bbox=(min_lon, min_lat, max_lon, max_lat)
        return bbox
    except Exception as e:
        return f"Error in  bbox_from_utm_epsg {str(e)}"

def intersected_area(bbox1, bbox2):

    """
    Calculate the intersected area of two bounding boxes.
    
    Parameters:
    - bbox1: A tuple representing the first bounding box (min_x, min_y, max_x, max_y).
    - bbox2: A tuple representing the second bounding box (min_x, min_y, max_x, max_y).
    
    Returns:
    - area: The intersected area of the two bounding boxes.
    """
    try:
        # Create shapely box objects from the bounding boxes
        box1 = box(*bbox1)
        box2 = box(*bbox2)
        
        # Calculate the intersection of the two boxes
        intersection = box1.intersection(box2)
        
        # Return the area of the intersection
        return intersection.area
    except Exception as e:
        return f"Error in  intersected_area {str(e)}"


def check_utm_epsg(epsg_code):
    """
    Check if the given EPSG code corresponds to a UTM CRS.
    """
    try:
        crs = CRS.from_epsg(epsg_code)
        return crs.coordinate_operation.method_name == "Transverse Mercator"
    except Exception as e:
        return False


def utm_epsg_finder(src_crs,bbox):
    """
    Find the UTM EPSG code for the given CRS and bounding box.
    """
    try:
        """
        Find UTM epsg
        raster: input raster path
        Returns:
        UTM EPSG code of the input raster
        """
        bbox_wgs84 = rasterio.warp.transform_bounds(src_crs,'EPSG:4326', *bbox)
        utm_crs_list = query_utm_crs_info(     
            datum_name='WGS 84',
            area_of_interest= AreaOfInterest(
            west_lon_degree=bbox_wgs84[0],
            south_lat_degree=bbox_wgs84[1],
            east_lon_degree=bbox_wgs84[2],
            north_lat_degree=bbox_wgs84[3],),) 

        utm_epsg_list=[]
        largest_intersection_area = 0
        best_epsg = None
        
        for utm_crs in utm_crs_list:
            epsg_bbox=bbox_from_utm_epsg(utm_crs.code)
            intersection_area = intersected_area(epsg_bbox,(bbox_wgs84[0],bbox_wgs84[1],bbox_wgs84[2],bbox_wgs84[3]))
            utm_epsg_list.append({"code":utm_crs.code,'name':utm_crs.name.replace("/",""), 'intersected_area':intersection_area})
            
            if intersection_area > largest_intersection_area:
                largest_intersection_area = intersection_area
                best_epsg = utm_crs.code
        
        return True,best_epsg,utm_epsg_list
    except Exception as e:
        return False, str(e), None
    

def utm_epsg_finder_from_file(file_path):
    """
    Find the UTM EPSG code for the given CRS and bounding box.
    """
    try:
        """
        Find UTM epsg
        raster: input raster path
        Returns:
        UTM EPSG code of the input raster
        """
        try:
           
            gdf = gpd.read_file(file_path)
            ds_crs_epsg = gdf.crs.to_epsg()
        except Exception as e:
            try:
                ds = rasterio.open(file_path)
                ds_crs_epsg=ds.crs.to_epsg()
            except Exception as e:
                return False, "Could not read the file", None
        
        is_UTM_epsg=check_utm_epsg(ds_crs_epsg)

        if is_UTM_epsg:
            return False,"Input file is already in UTM Projection", None
        else:
            bbox  = ds.bounds
            success,best_epsg,utm_crs_list=utm_epsg_finder(ds_crs_epsg,bbox)
            if success==True:
                return True,"success", {"best_epsg":best_epsg,"utm_crs_list": utm_crs_list}  #c['best_epsg']
    except Exception as e:
        return False, str(e), None
    

def raster_projection(file_path, out_path,dest_utm_epsg):
    """
        Reproject the raster dataset to UTM if necessary.
    """
    try:
        ds = rasterio.open(file_path)
        
        #check raster crs and reproject if necessary
        ds_crs_epsg=ds.crs.to_epsg()
        
        if dst_utm_epsg:
            is_UTM_epsg=check_utm_epsg(int(dst_utm_epsg))
            if not is_UTM_epsg:
                return False, "Invalid input dest_utm_epsg"
        else:
            is_UTM_epsg=check_utm_epsg(ds_crs_epsg)

            if not is_UTM_epsg:
                bbox  = ds.bounds
                success,dst_utm_epsg,utm_crs_list=utm_epsg_finder(ds_crs_epsg,bbox)
                if not success:
                    error=str(dst_utm_epsg)
                    return False, f"Error in finding utm: {error}"
            
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
    """
        Reproject the vector dataset to UTM if necessary.
    """
    try:
        gdf = gpd.read_file(file_path)
        gdf.set_crs(epsg=4326, inplace=True)
        gdf_crs = gdf.crs.to_epsg()
        is_UTM_epsg=check_utm_epsg(gdf_crs)

        if not is_UTM_epsg:
            gdf_bbox  = gdf.total_bounds
            min_x, min_y, max_x, max_y = gdf_bbox
            bbox=[min_x, min_y, max_x, max_y]
            
            success,dst_utm_epsg,utm_crs_list=utm_epsg_finder(gdf_crs,bbox)
            
            if not success:
                error=str(dst_utm_epsg)
                return False, f"Error in finding utm: {error}"
            
            target_crs = CRS.from_epsg(dst_utm_epsg).to_string()
            gdf = gdf.to_crs(target_crs)
            
            gdf.to_file(out_path, driver='ESRI Shapefile')
        return True, "Success"
    except Exception as e:
        return False, str(e)