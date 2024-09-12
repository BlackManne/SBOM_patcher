import gzip
import shutil
import sys
from bs4 import BeautifulSoup
import requests
from lxml import etree
from elasticsearch.helpers import bulk
from Constants.dbConstants import es
import os


# es = []


def save_data(version):
    # global es
    localdir = "files" + os.sep + version + os.sep
    if not os.path.exists(localdir):
        os.makedirs(localdir)
        link_dirs = ['/OS/x86_64/repodata/', '/everything/x86_64/repodata/']
        for link in link_dirs:
            dirname = "https://repo.openeuler.org/openEuler-" + version + link
            response = requests.get(dirname)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                filenames = [link.get('href') for link in soup.find_all('a')]
                for filename in filenames:
                    if filename.endswith("-filelists.xml.gz") or filename.endswith("-primary.xml.gz"):
                        response = requests.get(dirname + filename)
                        with open(localdir + filename, 'wb') as file:
                            file.write(response.content)
                        with gzip.open(localdir + filename, 'rb') as f_in:
                            with open(localdir + filename[:-3], 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
            else:
                sys.stderr.write("error version")
                return

    # if not es:
    #     es = Elasticsearch(es_url)
    index_name = "openeuler-" + version.lower()
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)

    dict = {}

    filelist_namespce = {
        'xmlns': 'http://linux.duke.edu/metadata/filelists'
    }
    primary_namespce = {
        'xmlns': 'http://linux.duke.edu/metadata/common',
        'rpm': 'http://linux.duke.edu/metadata/rpm'
    }

    for filename in os.listdir(localdir):
        if filename.endswith('filelists.xml'):
            xml = etree.parse(localdir + filename)
            for elem in xml.findall("xmlns:package", namespaces=filelist_namespce):
                rpmName = elem.get('name')
                files = elem.findall('xmlns:file', namespaces=filelist_namespce)
                filenames = [filename.text.split('/')[-1].lower() for filename in files if
                             not filename.get('type') == 'dir']
                dict.setdefault(rpmName, [[], []])[0].extend(filenames)
        elif filename.endswith('primary.xml'):
            xml = etree.parse(localdir + filename)
            for elem in xml.findall("xmlns:package", namespaces=primary_namespce):
                rpmName = elem.find('xmlns:name', namespaces=primary_namespce).text
                format = elem.find('xmlns:format', namespaces=primary_namespce)
                provides = format.find('rpm:provides', namespaces=primary_namespce)
                if provides:
                    files = provides.findall('rpm:entry', namespaces=primary_namespce)
                    filenames = [filename.get('name') for filename in files]
                    dict.setdefault(rpmName, [[], []])[1].extend(filenames)

    data = []
    for key, value in dict.items():
        doc = {
            '_index': index_name,
            '_source': {
                'rpm_name': key,
                'files': value[0],
                'provides': value[1]
            }
        }
        data.append(doc)

    success, _ = bulk(es, data, index=index_name)


def search(lib, version='22.03-LTS-SP3'):
    # global es
    # if not es:
    #     es = Elasticsearch(es_url)
    index_name = "openeuler-" + version.lower()
    query_body = {
        "bool": {
            "should": [
                {'term': {'files.keyword': lib}},
                {'term': {'files.keyword': lib + '.so'}},
                {'term': {'files.keyword': lib + '.a'}},
                {'term': {'files.keyword': 'lib' + lib + '.so'}},
                {'term': {'files.keyword': 'lib' + lib + '.a'}},
                {'term': {'provides.keyword': lib}}
            ]
        }
    }
    res = es.search(index=index_name, query=query_body)
    if res['hits']['hits']:
        return res['hits']['hits'][0]['_source']['rpm_name']
    return set()


# print(search('zstd.spec'))
# save_data("20.03-LTS-SP4")
save_data('22.03-LTS-SP3')

# if __name__ == '__main__':
#     if len(sys.argv) < 2:
#         sys.stderr.write("Error : need version number")
#         exit(0)
#     save_data(sys.argv[1])
