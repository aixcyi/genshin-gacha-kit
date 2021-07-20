from ggacha.common.time import str_to_stamp
from ggacha.res.histories import WISHES_HISTORY
from ggacha.res.items import ITEMS

for wish in WISHES_HISTORY:
    if type(WISHES_HISTORY[wish]) is not list:
        continue

    # 根据时间字符串添加时间戳，方便各方法利用。
    for i in range(len(WISHES_HISTORY[wish])):
        # 这里分别是祈愿卡池的开始时间和结束时间：
        WISHES_HISTORY[wish][i]['stamp'] = (
            str_to_stamp(WISHES_HISTORY[wish][i]['time'][0]),
            str_to_stamp(WISHES_HISTORY[wish][i]['time'][1]),
        )

    # 将项目自定义编号替换为角色/武器的名称。
    for i in range(len(WISHES_HISTORY[wish])):
        name_list = list()
        for item_id in WISHES_HISTORY[wish][i]['items']['up']:
            name_list += ITEMS[item_id].values()
        WISHES_HISTORY[wish][i]['items']['up'] = tuple(set(name_list))  # 利用集合的特性去重
