import requests


headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Connection': 'keep-alive'
}

if __name__ == "__main__":
    detail_url = "https://github.com/PX4/PX4-Autopilot/commit/d1fcd39a44e6312582c6ab02b0d5ee2599fb55aa"
    response = requests.request("GET", detail_url, headers=headers)
    print(response.text.strip())
