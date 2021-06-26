import datetime
import requests
import time
import json
import re
import pandas as pd
from pyquery import PyQuery as pq

Output_CSV = True
Output_name = ('out.csv', 'out_bad.csv', 'out_passed.csv')
Domain = 'https://nyaa.si'
Retry = 5


def get_last_time():
    with open('config.json', 'r', encoding='utf-8') as load_f:
        return datetime.datetime.strptime(json.load(load_f)['last-time'], "%Y-%m-%d %H:%M")


def write_last_time():
    with open('config.json', 'r', encoding='utf-8') as load_f:
        temp = json.load(load_f)
    temp['last-time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open('config.json', 'w') as write_f:
        return json.dump(temp, write_f, ensure_ascii=False)


def get_html(url):
    try:
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.5) \
                            Gecko/20091102 Firefox/3.5.5 (.NET CLR 3.5.30729)",
            'Connection': 'close'
        }
        respond = requests.get(url, headers=headers)
        requests.session().close()
        respond.encoding = respond.apparent_encoding
        return pq(respond.text)
    except Exception as e:
        print(e)
        return False


def get_author(href_more):
    more_body = get_html(href_more)
    if more_body:
        try:
            more_body = more_body.find('.panel-body')
            author = more_body[0][1][1][0].text
            return author
        except Exception as e:
            print(e)
    return False


def check_time(item):
    time_item = datetime.datetime.strptime(item['time'], "%Y-%m-%d %H:%M")
    time_last = get_last_time()
    return time_item > time_last


def verify_item(item):
    if re.match(r"\d+\.\d+\s([GMK])iB\s*$", item['size']):
        if re.match(r"\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}\s*$", item['time']):
            if re.match(r"^\s*magnet", item['magnet']):
                return True
    return False


def handle_table(trs, prefix, item_filter):
    data = []
    bad_data = []
    passed_data = []
    end = True
    bad = False
    passed = False
    ite = 0
    num = len(trs)
    for item in trs:
        ite += 1
        tds = item('td')
        href = prefix + tds[1][-1].attrib['href']

        author = get_author(href)
        item = {
            'category': tds[0][-1].attrib['title'],
            'name': tds[1][-1].attrib['title'],
            'author': author if author else "",
            'size': tds[-5].text,
            'time': tds[-4].text,
            'completes': int(tds[-1].text),
            'magnet': tds[2][-1].attrib['href']
        }

        if not verify_item(item):
            bad_data.append(item)
            bad = True
        if not item_filter(item):
            passed_data.append(item)
            passed = True

        print("[{0}/{1}] {2} {3} {4}".format(ite, num, item['name'], "Bad" if bad else "", "Passed" if passed else ""))

        if bad or passed:
            bad = passed = False
            continue

        if not check_time(item):
            end = True
            break

        data.append(item)

    data_frame = pd.DataFrame(data)
    bad_data_frame = pd.DataFrame(bad_data)
    passed_frame = pd.DataFrame(passed_data)
    return data_frame, bad_data_frame, passed_frame, end


def main():
    datas = pd.DataFrame(columns=('category', 'name', 'author', 'size', 'time', 'completes', 'magnet'))
    bad_datas = pd.DataFrame(columns=('category', 'name', 'author', 'size', 'time', 'completes', 'magnet'))
    passed_datas = pd.DataFrame(columns=('category', 'name', 'author', 'size', 'time', 'completes', 'magnet'))

    for i in range(1):
        print('Page {0}:'.format(i + 1))
        doc = get_html(Domain + '/?p={0}'.format(i + 1))
        if not doc:
            print("Failed to fetch {0}th page.".format(i + 1))
            break
        trs = list(doc.find('.torrent-list')('tbody')('tr').items())
        data, bad_data, passed_data, end = handle_table(trs, Domain, lambda item: True)
        if end:
            break
        datas = datas.append(data)
        bad_datas = bad_datas.append(bad_data)
        passed_datas = passed_datas.append(passed_data)

    if Output_CSV:
        datas.to_csv(Output_name[0], encoding=requests.get(Domain).apparent_encoding)
        datas.to_csv(Output_name[1], encoding=requests.get(Domain).apparent_encoding)
        datas.to_csv(Output_name[2], encoding=requests.get(Domain).apparent_encoding)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
