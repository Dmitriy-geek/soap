from bs4 import BeautifulSoup as bs
import requests
import re
from pymongo import MongoClient
from pprint import pprint

# если тут есть ваш код напишите мне и я пришлю вам печеньки

client = MongoClient('127.0.0.1', 27017)

db = client['hh'] # задаем параметры базы и коллекции для монго дб. создания базы не требуется,
                            # т.к в монгодб достаточно указать что мы хотим туда писать
hh_col = db.users

vacancy_input = input('Ввведите название вакансии - ')  # 'data scientist'
pr_reload_file = input('Введите yes, если необходимо перезаписать файл с результатами ')
main_link = 'https://hh.ru'
addit_params = f"/search/vacancy?clusters=true&search_field=description&enable_snippets=true&salary=&st=searchVacancy&text={vacancy_input}"
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}
vacancies = []
cnt = 0
next_link = 1

che = ''
# https://spb.hh.ru/search/vacancy?clusters=true&search_field=description&enable_snippets=true&salary=&st=searchVacancy&text=Data+scientist

def check(str): # блок проверки наличия вакансии и записи\незаписи в базу
    che = hh_col.find({'link': str})
    k = ''
    for el in che:
        k = el['link']
    if k == str:
        return 0
    else:
        return 1

def search_max_min(x_price): # блок сравнения запроса в базу монгодб и вывода вакансий по зарплате (диапазон сравнения с
                                # минимальной и максимальной зарплатой)
    res = []
    for job in hh_col.find({'$or':[{'salary_max':{'$gte':int(x_price)}},{'salary_min':{'$lte':int(x_price)}}]}).sort('salary_min'):
        res.append(job)
    return res


while next_link is not None: # цикл вытягивания вакансий с hh.ru.
    response = requests.get(main_link + addit_params, params={}, headers=headers) #
    print(response.url)
    soup = bs(response.text, 'html.parser')
    if response.ok:
        vacancy_list = soup.findAll('div', {'class': 'vacancy-serp-item__row_header'})
        for vacancy in vacancy_list:
            data = {}
            cnt += 1
            vacancy_header = vacancy.find('a')
            data['site'] = 'https://hh.ru'
            data['vacancy'] = vacancy_header.text
            data['link'] = vacancy_header['href']
            vacancy_salary = vacancy.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
            if vacancy_salary is None:
                data['currency'] = None
                data['salary_min'] = None
                data['salary_max'] = None
                vacancies.append(data)
                if check(data['link']) == 1:
                    hh_col.insert_one(data)
                else:
                    print('имеется')
                continue
            salary_text = ''.join(vacancy_salary.text.split()[:-1])
            data['currency'] = vacancy_salary.text.split()[-1]
            if salary_text.find('-') > -1:
                data['salary_min'] = int(re.sub('\D', '', salary_text.split('-')[0]))
                data['salary_max'] = int(re.sub('\D', '', salary_text.split('-')[-1]))
            elif salary_text.find('от') > -1:
                data['salary_min'] = int(re.sub('\D', '', salary_text))
                data['salary_max'] = None
            elif salary_text.find('до') > -1:
                data['salary_min'] = None
                data['salary_max'] = int(re.sub('\D', '', salary_text))
            else:
                data['salary_min'] = int(re.sub('\D', '', salary_text))
                data['salary_max'] = int(re.sub('\D', '', salary_text))
            vacancies.append(data)
            if check(data['link']) == 1:
                hh_col.insert_one(data)
            else: print('имеется')
            next_link = soup.find('a', {'data-qa': 'pager-next'})
        print(cnt)
#        c = soup.find('h1').text.split('\xa0')
#        c = int(c[0])
#        if c == cnt:
#            break
        button = soup.findAll('a', {'class': 'bloko-button HH-Pager-Controls-Next HH-Pager-Control'})
        if button == []:
            break
        addit_params = next_link['href']

if pr_reload_file == 'yes':
    with open("result.csv", "w", encoding="utf-8") as my_file:
        my_file.write("")

with open("result.csv", "a", encoding="utf-8") as my_file:
    for v in vacancies:
        try:
            my_file.write(f"{v['site']};{v['link']};{v['vacancy']};{v['salary_min']};{v['salary_max']};{v['currency']}\n")
        except KeyError:
            print(v)

price = input('Введите требуемую зарплату')
pprint(search_max_min(price))