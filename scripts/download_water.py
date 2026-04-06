import osmnx as ox
import geopandas as gpd
from shapely.geometry import Polygon
import os
import pandas as pd

# 1. 定义用户提供的坐标点 (经度, 纬度)
# 区域 1
coords1 = [
    (114.40917221742745, 22.648648641575317),
    (114.33991369970887, 22.642730556851035),
    (114.32607095266822, 22.773342098632618),
    (114.3819920349419, 22.777912597910277),
    (114.40917221742745, 22.648648641575317) # 闭合多边形
]

# 区域 2
coords2 = [
    (115.02950018034221, 22.991157945121994),
    (115.1430527601584, 22.989250548924577),
    (115.14609862030201, 22.832580088431673),
    (115.04080473288535, 22.82327677021746),
    (115.02950018034221, 22.991157945121994) # 闭合多边形
]

# 创建多边形列表
polygons = [Polygon(coords1), Polygon(coords2)]

def download_water_data():
    # 2. 配置更全面的查询标签
    # 尽可能覆盖所有与水相关的 OSM 标签
    tags = {
        'natural': ['water', 'wetland', 'bay', 'strait', 'coastline', 'spring', 'hot_spring'],
        'waterway': True, # 获取所有航道/水道 (river, stream, canal, drain, etc.)
        'water': True,    # 获取所有标记为 water 的要素
        'landuse': ['reservoir', 'basin', 'salt_pond', 'mill_pond', 'wastewater_plant'],
        'leisure': ['swimming_pool', 'marina', 'water_park'],
        'amenity': ['fountain', 'drinking_water', 'water_point']
    }

    all_gdfs = []
    
    for i, polygon in enumerate(polygons):
        print(f"正在从 OpenStreetMap 下载区域 {i+1} 的水资源数据...")
        try:
            # 获取所有匹配标签的要素
            gdf = ox.features_from_polygon(polygon, tags=tags)
            
            if not gdf.empty:
                # 过滤掉一些可能不是地理实体的东西（比如纯属性点，除非是喷泉等）
                # 通常我们更关注 Polygon 和 LineString
                print(f"区域 {i+1} 原始找到 {len(gdf)} 个要素。")
                all_gdfs.append(gdf)
            else:
                print(f"警告：区域 {i+1} 未找到数据。")
        except Exception as e:
            print(f"处理区域 {i+1} 时出错: {e}")

    if not all_gdfs:
        print("错误：所有区域均未找到任何水资源数据。")
        return

    # 合并所有 GeoDataFrame
    combined_gdf = pd.concat(all_gdfs, ignore_index=True)
    
    # 重新构建 GeoDataFrame 并保留坐标系
    # 注意：ox.features_from_polygon 返回的可能包含点、线、面
    combined_gdf = gpd.GeoDataFrame(combined_gdf, crs=all_gdfs[0].crs)

    # 3. 数据清洗与优化
    print(f"合并后共有 {len(combined_gdf)} 个要素。正在进行数据清洗...")

    # 仅保留具有有效几何形状的要素
    combined_gdf = combined_gdf[combined_gdf.geometry.is_valid]
    
    # 删除完全重复的几何体（如果区域重叠）
    combined_gdf = combined_gdf.drop_duplicates(subset=['geometry'])

    # 处理属性列：GeoJSON 不支持 list/dict 类型
    for col in combined_gdf.columns:
        if col == 'geometry':
            continue
        # 检查该列是否包含不可序列化的对象
        if combined_gdf[col].apply(lambda x: isinstance(x, (list, dict))).any():
            combined_gdf[col] = combined_gdf[col].apply(lambda x: str(x) if isinstance(x, (list, dict)) else x)

    # 4. 导出为 GeoJSON
    output_dir = 'public/data'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, 'water_data.geojson')
    
    # 确保转换为 WGS84
    combined_gdf = combined_gdf.to_crs(epsg=4326)
    
    # 导出
    combined_gdf.to_file(output_path, driver='GeoJSON')
    print(f"成功导出 {len(combined_gdf)} 个要素到: {output_path}")
    print("\nCesium 加载建议：")
    print("使用 Cesium.GeoJsonDataSource.load() 时设置 clampToGround: true 即可实现贴地。")

if __name__ == "__main__":
    download_water_data()
