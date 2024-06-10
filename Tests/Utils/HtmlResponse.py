def create_response(_code, _data):
    return HtmlResponse(_code, _data)


class HtmlResponse:

    def __init__(self, _code, _data):
        self.data = _data
        self.code = _code

    def get_code(self):
        return self.code

    def get_data(self):
        return self.data

