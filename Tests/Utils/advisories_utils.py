from ExternalSearchers.github_searcher import graphql_search
from test_utils import get_html_from_url


def generate_testcases_for_advisories(url_list, advisories_testcases, parsed_data_list):
    if len(url_list) != len(parsed_data_list):
        print("url_list and parsed_data_list must have the same length!")
        return
    for index in range(len(url_list)):
        advisories_testcases.append({
            "parsed_data": parsed_data_list[index],
            "raw_html": get_html_from_url(url_list[index])
        })
    print(advisories_testcases)


def generate_url_list_for_github_advisories():
    # 构建GraphQL查询
    query = '''
    query {
        securityAdvisories(first:20, publishedSince: "2023-01-01T00:00:00Z"){
            edges{
                node{
                    permalink
                }
            }
        }
    }
    '''
    result = graphql_search(query)
    if result is not None:
        url_list = []
        nodes = result['data']['securityAdvisories']['edges']
        for node in nodes:
            url_list.append(node['node']['permalink'])
        print(url_list)
        return url_list
