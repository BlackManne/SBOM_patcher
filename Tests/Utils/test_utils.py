import requests

from Tests.Utils import HtmlResponse


def get_html_from_url(url):
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Connection': 'keep-alive'
    }
    try:
        response = requests.request("GET", url, headers=headers)
        if response.status_code != 200:
            return HtmlResponse.create_response(response.status_code, None)
        else:
            return HtmlResponse.create_response(200, response.text.strip())
    except Exception as e:
        print(e)
        return HtmlResponse.create_response(500, None)


def generate_testcases(url_list, testcases_list, func):
    for url in url_list:
        testcases_list.append({
            "parsed_data": func(url),
            "raw_html": get_html_from_url(url)
        })
    print(testcases_list)

    # 如果需要分别打印html和json数据，可以使用这里的代码
    # for element in testcases_list:
    #     if element["raw_html"].get_code() == 200:
    #         print("parsed_data", element["parsed_data"])
    #         print("raw_html:", element["raw_html"].get_data())



