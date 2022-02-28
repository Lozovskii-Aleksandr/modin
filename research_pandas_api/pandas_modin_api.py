import requests
from bs4 import BeautifulSoup


def get_all_method_pandas():
    url = 'https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html'

    response = requests.get(url)

    list_method = []

    soup = BeautifulSoup(response.text, "html.parser")

    data = soup.find_all(class_='toctree-l3')
    for i in data:
        list_method.append(i.text.replace('\n', ''))

    data = soup.find_all(class_='toctree-l2')[1:]
    for i in data:
        list_method.append(i.text.replace('\n', ''))

    res = []

    for i in list_method:
        if not (
            '.plot.' in i
            or 'Flags' in i
            or 'sparse.' in i
            ):
            values = i.replace('pandas.DataFrame.', '')
            res.append(values)

    res = list(set(res))
    res.sort()

    return res


def get_all_method_modin():
    url = 'https://modin.readthedocs.io/en/stable/supported_apis/dataframe_supported.html'

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")
    data = soup.find(class_='table').find_all(class_='reference')

    res = []
    for i in data:
        res.append(i.text)

    res = list(set(res))
    res.sort()

    return res


def main():
    methods_modin = get_all_method_modin()
    methods_pandas = get_all_method_pandas()

    print(f'{len(methods_modin) = }\n{len(methods_pandas) = }\n')

    # Каких методов нет в `modin`
    pandas_without_modin = sorted(list(set(methods_pandas) - set(methods_modin)))
    modin_without_pandas = sorted(list(set(methods_modin) - set(methods_pandas)))

    # for i in methods_modin:
    #     print(i)


    print("Методы pandas без методов modin:")
    for i in pandas_without_modin:
        print(i)

    print('')

    print("Методы modin без методов pandas:")
    for i in modin_without_pandas:
        print(i)

if __name__ == '__main__':
    main()
