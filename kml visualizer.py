import os
import glob
import folium
import zipfile
import xml.etree.ElementTree as ET
from folium.features import CustomIcon

def find_kmz_files(directory):
    kmz_files = glob.glob(os.path.join(directory, '*.kmz'))
    return kmz_files

def find_kml_files(directory):
    kml_files = glob.glob(os.path.join(directory, '*.kml'))
    return kml_files

def extract_kml_from_kmz(kmz_file_path):
    with zipfile.ZipFile(kmz_file_path, 'r') as kmz:
        kml_files = [name for name in kmz.namelist() if name.lower().endswith('.kml')]
        if kml_files:
            kml_file_path = kml_files[0]
            kmz.extract(kml_file_path, os.path.dirname(kmz_file_path))
            return os.path.join(os.path.dirname(kmz_file_path), kml_file_path)
    return None

def parse_kml(kml_file_path):
    gps_data = []
    tree = ET.parse(kml_file_path)
    root = tree.getroot()

    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}

    for placemark in root.findall('.//kml:Placemark', namespace):
        line_string = placemark.find('.//kml:LineString', namespace)
        
        if line_string is not None:
            coordinates = line_string.find('.//kml:coordinates', namespace)
            if coordinates is not None:
                coords = coordinates.text.strip().split()
                for coord in coords:
                    lon, lat, _ = coord.split(',')
                    gps_data.append({
                        'latitude': float(lat),
                        'longitude': float(lon),
                        'altitude': 0  # 假设高度为0
                    })

    return gps_data

def visualize_kmz_or_kml(kmz_data_list):
    if not kmz_data_list:
        print("No GPS data available to visualize.")
        return

    all_latitudes = []
    all_longitudes = []
    
    for kmz_data in kmz_data_list:
        latitudes = [data['latitude'] for data in kmz_data['gps_data']]
        longitudes = [data['longitude'] for data in kmz_data['gps_data']]
        all_latitudes.extend(latitudes)
        all_longitudes.extend(longitudes)

    avg_latitude = sum(all_latitudes) / len(all_latitudes)
    avg_longitude = sum(all_longitudes) / len(all_longitudes)
    
    map_center = [avg_latitude, avg_longitude]
    
    gps_map = folium.Map(location=map_center, zoom_start=14, tiles='OpenStreetMap')

    # 添加更多的地图源
    folium.TileLayer(
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        name='OpenTopoMap',
        attr='© OpenTopoMap contributors'
    ).add_to(gps_map)

    folium.TileLayer(
        tiles='https://{s}.tile.thunderforest.com/outdoors/{z}/{x}/{y}.png',
        name='Thunderforest Outdoors',
        attr='© Thunderforest'
    ).add_to(gps_map)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        name='Esri Satellite',
        attr='© Esri'
    ).add_to(gps_map)

    folium.TileLayer(
        tiles='https://{s}.basemaps.carto.com/light_all/{z}/{x}/{y}.png',
        name='CartoDB Positron',
        attr='© OpenStreetMap contributors'
    ).add_to(gps_map)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        name='Google Satellite',
        attr='© Google'
    ).add_to(gps_map)

    folium.LayerControl().add_to(gps_map)

    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 
              'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 
              'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']

    for idx, kmz_data in enumerate(kmz_data_list):
        color = colors[idx % len(colors)]
        
        for data in kmz_data['gps_data']:
            popup_content = f"Latitude: {data['latitude']:.6f}, Longitude: {data['longitude']:.6f}"
            
            folium.CircleMarker(
                [data['latitude'], data['longitude']],
                radius=3,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8
            ).add_to(gps_map).add_child(folium.Popup(popup_content))

    # 根据原始 KML 文件名保存 HTML 文件
    file_name = kmz_data['file_name']
    file_path = os.path.join(os.path.dirname(file_name), file_name.replace('.kml', '.html').replace('.kmz', '.html'))
    
    gps_map.save(file_path)
    print(f"Map saved as '{file_path}'.")

if __name__ == '__main__':
    directory_path = "D:\\desk\\kml"  # 修改为您的 KML 或 KMZ 文件夹路径
    
    kml_files = find_kml_files(directory_path)
    kmz_files = find_kmz_files(directory_path)

    kmz_data_list = []

    if kml_files:
        for kml_file_path in kml_files:
            print(f"Processing KML file: {kml_file_path}")
            parsed_gps_data = parse_kml(kml_file_path)
            kmz_data_list.append({
                'file_name': kml_file_path,
                'gps_data': parsed_gps_data
            })

    if kmz_files:
        for kmz_file_path in kmz_files:
            print(f"Processing KMZ file: {kmz_file_path}")
            kml_file_path = extract_kml_from_kmz(kmz_file_path)
            if kml_file_path:
                parsed_gps_data = parse_kml(kml_file_path)
                kmz_data_list.append({
                    'file_name': kmz_file_path,
                    'gps_data': parsed_gps_data
                })

    if kmz_data_list:
        visualize_kmz_or_kml(kmz_data_list)
    else:
        print("No GPS data available to visualize.")
