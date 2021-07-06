import datetime
import requests
import time
import json
import re
import csv
from pyquery import PyQuery as pq

Output_CSV = True
Output_name = ('out.csv', 'out_bad.csv', 'out_passed.csv')
Domain = 'https://nyaa.si'
Retry = 5

allowed_author = ['jptv', '']
allowed_category = []


def get_last_time():
    # with open('config.json', 'r', encoding='utf-8') as load_f:
    return datetime.datetime.strptime("2019-06-28 00:01", "%Y-%m-%d %H:%M")


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
        if respond.status_code == 429:
            return False
        requests.session().close()
        respond.encoding = respond.apparent_encoding
        return pq(respond.text)
    except Exception as e:
        print(e)
        return False


def get_author(href_more):
    try:
        more_body = get_html(href_more)
        more_body = more_body.find('.panel-body')
        if len(more_body[0][1][1]):
            author = more_body[0][1][1][0].text
            return author
        else:
            return "Anonymous"
    except Exception as e:
        print(e)
        pass
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
    bad = False
    passed = False
    end = False
    ite = 0
    num = len(trs)
    fields = ['category', 'name', 'author', 'size', 'time', 'completes', 'magnet']
    # with open("data.csv", "a") as data:
    data = open("data.csv", "a", encoding='utf-8-sig', newline='')
    data_w = csv.DictWriter(data, fieldnames=fields)
    bad_data = open("bad_data.csv", "a", encoding='utf-8-sig', newline='')
    bad_data_w = csv.DictWriter(bad_data, fieldnames=fields)
    passed_data = open("passed_data.csv", "a", encoding='utf-8-sig', newline='')
    passed_data_w = csv.DictWriter(passed_data, fieldnames=fields)
    for item in trs:
        try:
            time.sleep(2)
            ite += 1
            tds = item('td')
            href = prefix + tds[1][-1].attrib['href']

            author = get_author(href)
            item = {
                'category': tds[0][-1].attrib['title'].strip(),
                'name': tds[1][-1].attrib['title'].strip(),
                'author': author.strip() if author else "Nan",
                'size': tds[-5].text,
                'time': tds[-4].text,
                'completes': int(tds[-1].text),
                'magnet': tds[-6][-1].attrib['href']
            }
            if not verify_item(item):
                bad_data_w.writerow(item)
                bad = True
            elif not check_time(item):
                end = True
                print("\033[1;33mReached last time.\033[0m")
                break
            elif not item_filter(item):
                passed_data_w.writerow(item)
                passed = True
            else:
                data_w.writerow(item)

            print("\033[1;32m[{0}/{1}]\033[1;37m {2} \033[1;31m{3} \033[1;36m{4}\033[0m"
                  .format(ite, num, item['name'], "Bad" if bad else "", "Passed" if passed else ""))
        except Exception as e:
            pass
        finally:
            bad = passed = False
    passed_data.close()
    bad_data.close()
    data.close()
    return end


def main(argv=None):
    docs = []
    for i in range(300):
        print('\033[1;33mPage {0}:\033[0m'.format(i + 1))
        try:
            time.sleep(2)
            doc = get_html(Domain + '/?p={0}'.format(i + 1))
            if not doc:
                print("Failed to fetch {0}th page.".format(i + 1))
                break
            docs.append(doc)
        except Exception as e:
            pass
    for i in range(len(docs)):
        with open("doc_" + str(i + 1) + '.txt', "a", encoding='utf-8') as d:
            d.write(docs[i].html())
    for doc in docs:
        trs = list(doc.find('.torrent-list')('tbody')('tr').items())
        end = handle_table(trs, Domain, lambda item: True)
        # if end:
        #     break


if __name__ == '__main__':
    main()

