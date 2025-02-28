from datetime import datetime


def get_current_time():
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time


# 比较date1是否在date2前面
def compare_dates(date_str1, date_str2):
    try:
        date1 = datetime.strptime(date_str1, '%Y-%m-%d')
        date2 = datetime.strptime(date_str2, '%Y-%m-%d')

        if date1 > date2:  # date1在date2之后
            return 1
        elif date1 == date2:    # date1在date2同一天
            return 0
        else:
            return -1   # date1在date2之前
    except ValueError:
        print("日期格式错误，请使用 YYYY-MM-DD 格式")
        return 500
