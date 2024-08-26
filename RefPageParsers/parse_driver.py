import re

from RefPageParsers.github_parser import github_parse


def parse_url(url):
    patch_detail = {}
    # 根据传入的patch url解析，调用不同的parse函数
    if re.match("https://github.com/.+", url):
        github_detail = github_parse(url)
        patch_detail['detail'] = github_detail['detail']
        patch_detail['service_name'] = github_detail['service_name']
    # elif re.match("https://msrc.microsoft.com/.+", url):
    #     nvd_detail['detail'] = win_parser.parse(url)
    #     nvd_detail['service_name'] = 'microsoft'
    else:
        print('no supported parser for url:' + url)
        patch_detail['detail'] = None
        patch_detail['service_name'] = None
    return patch_detail
