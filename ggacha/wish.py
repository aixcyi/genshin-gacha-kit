from datetime import datetime
from typing import List, Dict

from ggacha.common.throwable import GenshinBaseException
from ggacha.common.time import str_to_stamp
from ggacha.res import WISHES_HISTORY, ITEMS


class MultiRegionError(GenshinBaseException):
    """不允许合并两段不同地区的抽卡记录"""

    def __init__(self, region1, region2):
        super(MultiRegionError, self).__init__(
            self.__doc__ + '：%s  %s' % (region1, region2)
        )


class GachaWish:
    def __init__(self,
                 gacha_type: str,
                 record_region: str = '',
                 allow_multi_region: bool = False,
                 ) -> None:
        """原神祈愿卡池抽取记录类。

        本类是单一一个祈愿卡池的抽取记录的存取载体，
        提供了面向祈愿卡池的抽卡记录合并、排序、聚合、历史查询、保底计算等功能。

        :param gacha_type: 祈愿卡池类型。目前是一个整数字符串。
        :param record_region: 游戏地区缩写。默认为空字符串。
        :param allow_multi_region: 是否允许合并不同地区的抽卡数据。注意：空字符串也视为一种地区。
        """

        self.wish_type = gacha_type
        """祈愿卡池的类型（gacha_type）。目前是一个整数字符串。"""

        self.wish_name = ''
        """祈愿卡池的名称。
        
        考虑到多语言带来的复杂情况，这个值仅在获取抽卡记录时填写，其余时候仅作存储载体使用。
        """

        self.multi_region = allow_multi_region
        """允许合并多个游戏地区的数据。若为 ``True`` ，则 ``region`` 字段无效。"""

        self.region = record_region
        """游戏地区的缩写字符串。
        
        游戏地区决定抽卡时间的所在时区，从而能够解读出正确（真实）的抽卡时间。
        当 ``multi_region`` 字段为 ``True`` 时无效。
        """

        self.records = list()
        """当前祈愿卡池的所有抽取记录。"""

        self.CEILING = {
            '100': 90,  # 新手祈愿
            '200': 90,  # 常驻祈愿
            '301': 90,  # 角色活动祈愿
            '302': 80,  # 武器活动祈愿
        }[self.wish_type]
        """五星角色/物品必定抽出的保底抽取次数。"""

        if self.wish_type in WISHES_HISTORY:
            self.histories = WISHES_HISTORY[self.wish_type]
            """当前祈愿卡池的所有历史信息。"""

            # 根据时间字符串添加时间戳，方便各方法利用。
            for i in range(len(self.histories)):
                # 这里分别是祈愿卡池的开始时间和结束时间：
                self.histories[i]['stamp'] = (
                    str_to_stamp(self.histories[i]['time'][0]),
                    str_to_stamp(self.histories[i]['time'][1]),
                )

            # 将项目自定义编号替换为角色/武器的名称。
            for i in range(len(self.histories)):
                name_list = list()
                for item_id in self.histories[i]['items']['up']:
                    name_list += ITEMS[item_id].values()
                self.histories[i]['items']['up'] = \
                    tuple(set(name_list))  # 利用集合的特性去重

    def __repr__(self) -> str:
        return '<%s(%s) 记录数量：%i>' % (
            self.__class__.__name__,
            self.wish_type,
            len(self),
        )

    def __str__(self) -> str:
        return {
            '100': '新手祈愿',
            '200': '常驻祈愿',
            '301': '角色活动祈愿',
            '302': '武器活动祈愿',
        }[self.wish_type]

    def __eq__(self, o) -> bool:
        if type(o) is self.__class__:
            return o.wish_type == self.wish_type
        return False

    def __len__(self) -> int:
        return len(self.records)

    def __iadd__(self, other):

        def merge(records1, records2) -> List[dict]:
            result = records1 + records2
            result.sort(key=lambda e: (e['time'], e['RID']))
            for i in range(len(result) - 1, 0, -1):
                if result[i]['RID'] == result[i - 1]['RID'] \
                        and result[i]['time'] == result[i - 1]['time']:
                    result.pop(i)
            return result

        if type(other) is list:
            # 如果与列表相加，由于缺少地区，所以直接合并得了：
            self.records = merge(self.records, other)

        elif type(other) is self.__class__:
            # 若与本类相加，则需要判断是否允许合并不同地区的数据：
            # 因为不同地区导出的记录其所记载的时间可能需要用不同的时区才能
            # 被其他人正确解读，因此需要谨慎处理。
            if self.multi_region is False:
                if self.region != other.region:
                    raise MultiRegionError(self.region, other.region)
            print(self.wish_name, other.wish_name)
            if other.wish_name != '':
                self.wish_name = other.wish_name
            self.records = merge(self.records, other.records)

        else:
            # 不能跟其它类型相加：
            raise TypeError(
                '仅支持与 list、%s 类型相加，而提供的是 %s' % (
                    self.__class__.__name__, type(other).__name__,
                )
            )
        return self

    def sort(self):
        """对当前卡池的抽卡记录进行排序。

        先按 ``time`` 字段排序，当 ``time`` 字段相同时再按 ``RID`` 字段排序。
        """
        self.records.sort(key=lambda e: (e['time'], e['RID']))

    def t2stamp(self):
        """将卡池内所有抽卡记录的抽卡时间字符串转换为时间戳（小数），以方便处理。

        - 请确保 ``time`` 字段存在。
        - 如果 ``stamp`` 字段已经存在，则会被覆盖。
        """
        for i in range(len(self.records)):
            self.records[i]['stamp'] = datetime.strptime(
                date_string=self.records[i].pop('time'),
                format='%Y-%m-%d %H:%M:%S',
            ).timestamp()

    def stamp2t(self):
        """将卡池内所有抽卡记录的时间戳（小数）转换为时间字符串。

        - 请确保 ``stamp`` 字段存在。
        - 如果 ``time`` 字段已经存在，则会被覆盖。
        """
        for i in range(len(self.records)):
            self.records[i]['time'] = datetime.fromtimestamp(
                self.records[i].pop('stamp')
            ).strftime(
                fmt='%Y-%m-%d %H:%M:%S',
            )

    def search(self, item_name: str, moment: float = None) -> list:
        """根据时间判断某个角色（某件武器）在哪些祈愿卡池中抽取概率提升（up）。

        :param moment: 时间点。是一个时间戳小数。
        :param item_name: 某个角色或某种武器的名称。
                          名称不应该包括前后缀，比如 “「逃跑的太阳·可莉」” 名称应为 “可莉” 。
                          名称的语言文字可以是任意的，因为这个取决于卡池历史记录是否包含这种文字的名称。
        """
        history_list = list()
        try:
            for item in self.histories:
                if moment is not None:
                    if not (item['stamp'][0] <= moment <= item['stamp'][1]):
                        continue
                if item_name in item['items']['up']:
                    history_list.append(item)
        except (KeyError, AttributeError):
            pass
        return history_list

    def group_by_time(self) -> Dict[str, List[dict]]:
        """将当前卡池的抽卡记录按照 **抽卡时间** 分组。

        因为一次性抽取十次（即十连）产生的时间是一样的（至少获取到的抽卡时间是一样的），
        因此可以通过按抽卡时间分组来识别哪些抽卡记录属于十连，哪些抽卡记录属于单抽。

        :return: 返回一个字典，以抽卡记录时间为键，抽卡记录列表为值。
                 抽卡记录时间是一个字符串，格式为 “YYYY-mm-dd HH:MM:SS”。
        """
        result = dict()
        for record in self.records:
            t = record['time']
            if t not in result:
                result[t] = list()
            else:
                result[t].append(record)
        return result

    def group_by_day(self) -> Dict[str, List[dict]]:
        """将当前卡池的抽卡记录按照 **抽卡记录时间在哪一天** 分组。

        :return: 返回一个字典，以抽卡记录时间为键，抽卡记录列表为值。
                 抽卡记录时间是一个字符串，格式为 “YYYY-mm-dd”。
        """
        result = dict()
        for record in self.records:
            day = record['time'][:10]  # 10 == len('2020-12-23')
            if day not in result:
                result[day] = list()
            else:
                result[day].append(record)
        # for record in self.records:
        #     day = int(record['stamp'] - record['stamp'] % self._SECONDS_PER_DAY)
        #     if day not in result:
        #         result[day] = list()
        #     else:
        #         result[day].append(record)
        return result

    def group_by_all_type(self) -> dict:
        """将当前卡池的抽卡记录按照(角色/武器)类型、星级、名称分组。

        :return: {'角色': {'5': {'甘雨': [抽卡记录, ...], }}}
        """
        try:
            result = dict()
            for record in self.records:
                r_type = record['item_type']
                r_star = record['rank_type']
                r_name = record['name']
                if r_type not in result:
                    result[r_type] = dict()
                if r_star not in result[r_type]:
                    result[r_type][r_star] = dict()
                if r_name not in result[r_type][r_star]:
                    result[r_type][r_star][r_name] = list()
                result[r_type][r_star][r_name].append(record)
            return result
        except KeyError:
            return dict()
