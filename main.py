import datetime
import requests
import time
import pandas as pd
from pyquery import PyQuery as pq

Output_CSV = True
Output_name = 'out.csv'
Domain = 'https://nyaa.si'


def get_last_time():
    return datetime.datetime.strptime("2021-06-20 00:01", "%Y-%m-%d %H:%M")


def get_html(url):
    try:
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.5) \
                            Gecko/20091102 Firefox/3.5.5 (.NET CLR 3.5.30729)"
        }
        respond = requests.get(url, headers=headers)
        respond.encoding = respond.apparent_encoding
        return pq(respond.text)
    except Exception as e:
        print(e)
        return False


def get_author(href_more):
    more_body = get_html(href_more).find('.panel-body')
    author = more_body[0][1][1][0].text
    return author


def check_time(item):
    time_item = datetime.datetime.strptime(item['time'], "%Y-%m-%d %H:%M")
    time_last = get_last_time()
    return time_item > time_last


def handle_table(trs, prefix, item_filter):
    data = []
    for item in trs:
        tds = item('td')
        href = prefix + tds[1][-1].attrib['href']

        author = get_author(href)
        item = {
            'category': tds[0][-1].attrib['title'],
            'name': tds[1][-1].attrib['title'],
            'author': author,
            'size': tds[-5].text,
            'time': tds[-4].text,
            'completes': int(tds[-1].text),
            'magnet': tds[2][-1].attrib['href']
        }

        if not item_filter(item):
            break
        data.append(item)

    data_frame = pd.DataFrame(data)
    return data_frame


def main():
    datas = pd.DataFrame(columns=('category', 'name', 'author', 'size', 'time', 'completes', 'magnet'))
    for i in range(1):
        doc = get_html(Domain + '/?p={0}'.format(i + 1))
        trs = list(doc.find('.torrent-list')('tbody')('tr').items())
        data = handle_table(trs, Domain, check_time)
        if data.empty:
            break
        else:
            datas.append(data)

    if Output_CSV:
        datas.to_csv(Output_name)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
