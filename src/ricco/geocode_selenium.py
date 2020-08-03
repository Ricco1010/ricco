import pandas as pd
from ricco.coord_trans import BD2WGS
from ricco.util import reset2name
from ricco.util import serise_to_float

from selenium import webdriver


def get_geocoding(driver, kwd):
    # 输入项目名称
    driver.find_element_by_xpath('//*[@id="localvalue"]').send_keys(kwd)
    # 点击搜索
    driver.find_element_by_xpath('//*[@id="localsearch"]').click()
    # 点击第一个项目 两次点击不同位置 主要目的是拖延时间
    driver.find_element_by_xpath('//*[@id="no_0"]/a').click()
    driver.find_element_by_xpath('//*[@id="no_0"]/p').click()
    # 获取项目名称 用于核对
    title = driver.find_element_by_xpath('//*[@id="no_0"]/a').get_attribute('title')
    # 获取经纬度
    try:
        txt = driver.find_element_by_xpath('//*[@id="no_0"]/p').text
        geom = txt.split('：')[-1]
    except:
        geom = ''
    driver.find_element_by_xpath('//*[@id="localvalue"]').clear()
    kwd = kwd.split(' ')[-1]
    return [kwd, title, geom]


def selenium_geocode(df, proj_name='项目名称', city=''):
    fp = webdriver.FirefoxProfile()
    driver = webdriver.Firefox(firefox_profile=fp)
    driver.implicitly_wait(10)
    driver.maximize_window()
    path = 'http://api.map.baidu.com/lbsapi/getpoint/index.html'
    driver.get(path)
    empty = pd.DataFrame(columns=[proj_name, '查询项目名称', '查询经纬度'])
    for i in df[proj_name]:
        kwd = city + ' ' + i
        try:
            data_list = get_geocoding(driver, kwd)
        except:
            data_list = [i, '', '']
        print(data_list)
        dic = {proj_name: [data_list[0]],
               '查询项目名称': [data_list[1]],
               '查询经纬度': [data_list[2]]}
        add = pd.DataFrame(dic)
        empty = empty.append(add, sort=False)
    driver.close()
    empty['lng'] = empty['查询经纬度'].str.split(',', expand=True)[0]
    empty['lat'] = empty['查询经纬度'].str.split(',', expand=True)[1]
    empty['lng'] = serise_to_float(empty['lng'])
    empty['lat'] = serise_to_float(empty['lat'])
    empty.drop('查询经纬度', axis=1, inplace=True)
    if 'name' not in df.columns:
        empty = reset2name(empty)
    empty = BD2WGS(empty)
    return empty
