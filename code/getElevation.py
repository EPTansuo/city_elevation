import os
import requests
import pandas as pd

key = os.environ.get('AMAP_KEY')  # 在环境变量中设置高德地图API的KEY


def getLocation(addr:str):
    '''
    输入字符串地址，返回经纬度，返回为列表:[经度，纬度]
    '''
    url = 'https://restapi.amap.com/v3/geocode/geo'# 高德地图Web API URL
    params = {
        'address' : addr,
        'key': key,
    }
    response = requests.get(url, params=params)
    while True:
        time.sleep(0.4)   # 高德地图的基础包不支持高并发，所以等一下
        result = response.json()
        if result['status'] == '1':
            loc = result['geocodes'][0]['location'].split(',')
            return [float(loc[0]),float(loc[1])]
        else:
            if(result['info'] == "CUQPS_HAS_EXCEEDED_THE_LIMIT" ):
                print("CUQPS_HAS_EXCEEDED_THE_LIMIT --> wait and retry") # 请求太频繁了
                time.sleep(5)
                continue
            print(f"Unable to retrieve the location for the address '{addr}'. Error details: {result}")
        return []



def getCityList():
    '''
    获取县级和市级行政单位列表
     - 对于直辖市，只获取该市的名称
     - 对于xxx区，则全部删去
    '''
    data_file = "china_area/area_code_2024.csv"
    df_all = pd.read_csv(data_file,header=None,dtype=str)
    df_all.columns = ["code","name","level","pcode","category"]

    df = df_all[(df_all['level'] == '2') | (df_all['level'] == '3')] #县市级

    # 北京，天津，上海，重庆
    #directCity = ['110000000000','120000000000','310000000000','500000000000']
    df = df[~df['code'].str.startswith(('11', '12', '31', '50'))]
    df = df[~df['name'].str.endswith('区')]

    city_list = df['name'].tolist()
    city_list.append(["北京市","天津市","上海市","重庆市"])

    #return city_list
    return ["北京市","天津市","上海市","重庆市"]

def getElevation(lng:float,lat:float)->float:
    '''
    输入精度和纬度，返回海拔高度
    '''
    #url = "https://api.opentopodata.org/v1/srtm30m" # public API at api.opentopodata.org
    url = "http://localhost:5000/v1/etopo1"

    params = {
        'locations':f"{lat},{lng}"
    }
    response = requests.get(url, params=params)
    result = response.json()
    if result['status'] == 'OK':
        return result['results'][0]['elevation']
    else:
        print(f"Unable to retrieve the elevation for the location 'lng:{lng}, lat:{lat}'. Error details: {result}")
    return -1000  #-1000对于海拔高度来说是不可能的


def save_to_csv(filename:str,city_list:list,loc_list:list,elevation_list:list):
    lng = [loc_[0] for loc_ in loc_list if loc_]
    lat = [loc_[1] for loc_ in loc_list if loc_]
    data = {'city': city_list, 'longitude': lng, 'latitude':lat, 'elevation': elevation_list}
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)



if __name__ == "__main__":
    i = 0
    N = 200
    loc_list = []
    city_list = []
    elevation_list = []
    city_list_all = getCityList();
    for city in city_list_all:
        i=i+1;
        loc = getLocation(city)
        elevation = getElevation(loc[0],loc[1])
        loc_list.append(loc)
        city_list.append(city)
        elevation_list.append(elevation)
        print(f"proc:{i}/{len(city_list_all)}, city:{city}, longitude:{loc[0]}, latitude:{loc[1]}, elevation:{elevation}")

        if(i%N == 0):
            save_to_csv(f"out_{int(i/N)}.csv",city_list,loc_list,elevation_list)

    save_to_csv("out.csv",city_list,loc_list,elevation_list)
