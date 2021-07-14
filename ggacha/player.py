import os
from datetime import datetime, timedelta
from json import loads, load, dumps
from json.decoder import JSONDecodeError
from random import random
from time import sleep
from typing import Callable
from urllib.parse import urlparse, urlencode, parse_qsl

from requests import get

from ggacha import GachaWish
from ggacha.common.hash import sm3u, sm3r
from ggacha.common.throwable import GenshinBaseException


class CollectingError(GenshinBaseException):
    """获取祈愿卡池抽取记录时触发的错误。"""

    def __init__(self, *args):
        super(CollectingError, self).__init__(*args)


class MultiUIDError(GenshinBaseException):
    """不允许合并两段不同UID的抽卡记录"""

    def __init__(self, uid1, uid2):
        super(MultiUIDError, self).__init__(
            '{tip}：{uid_a} 与 {uid_b}'.format(
                tip=self.__doc__,
                uid_a=uid1,
                uid_b=uid2,
            ),
        )


def http_get_json(url: str, encoding: str = 'UTF-8'):
    return loads(get(url).content.decode(encoding))


# 导出的数据的模板：
# （用这种方式是为了导出紧凑兼易读的JSON格式）
# （放在这里是为了保证缩进正确）
JSON_DUMP_TEMPLATE = '''{
  "collector": {
    "version": "%s",
    "create": "%s",
    "modify": "%s"
  },
  "infos": {
    "uid": "%s",
    "lang": "%s",
    "region": "%s"
  },
  "wishes": %s,
  "records": %s
}'''


class GachaPlayer:
    """原神祈愿抽取记录数据类。

    本类是多个祈愿卡池的抽取记录的存取载体，
    提供面向玩家的抽卡记录获取、载入、导出、排序与合并等功能。

    目前采用读取日志的方式获取抽卡记录。
    """

    _PAGE_SIZE_MAX = 20
    """抽卡记录每页最大数量。"""

    _UTCTIME_F = '%Y-%m-%d %H:%M:%S UTC+0'
    """collector 属性的时间字符串格式。"""

    VERSION = '1.6'
    """本类适配的最新游戏版本。"""

    SUPPORT_VERSIONS = ['1.4', '1.5', VERSION]
    """兼容的游戏版本。意思是可以对这些版本的数据进行合并操作。"""

    PROCESS_READ_LOG = 0x0011
    PROCESS_PARSE_LOG = 0x0012
    PROCESS_TEST_PASSKEY = 0x0013
    PROCESS_GET_WISHES_TYPE = 0x0014
    PROCESS_END_INIT = 0x001F
    PROCESS_GET_WISH_RECORDS = 0x0021
    PROCESS_GET_RECORD_PAGE = 0x0022
    PROCESS_END_DOWNLOAD = 0x002F

    def __init__(self,
                 allow_multi_uid: bool = False,
                 handler: Callable = None,
                 file: str = '') -> None:
        """
        :param allow_multi_uid: 是否允许合并不同玩家（UID）的数据。False表示不允许。
        :param handler: 可选。接收数据获取进度通知的函数。
        :param file: 可选。含有抽卡记录数据的JSON文件的文件地址。
                     当提供了本参数时，将直接依据文件内容构造对象。
        """

        self.create = ''
        """记录数据的创建时间（字符串），时区固定为UTC+0。该时间代表最初的数据获取的开始时间。"""

        self.modify = ''
        """记录数据的修改时间（字符串），时区固定为UTC+0。该时间代表合并时两对创建修改时间中最晚的那个时间。"""

        self.uid = ''
        """经过散列运算的玩家游戏UID，长度为10个字符。"""

        self.language = ''
        """抽卡记录数据的语言文字。"""

        self.region = ''
        """游戏地区的缩写。
        
        游戏地区决定了获取到的抽卡记录的时间的时区。详见游戏内祈愿面板的说明。
        """

        self.wishes = [
            GachaWish(gacha_type='100'),  # 新手祈愿
            GachaWish(gacha_type='200'),  # 常驻祈愿
            GachaWish(gacha_type='301'),  # 角色活动祈愿
            GachaWish(gacha_type='302'),  # 武器活动祈愿
        ]
        """所有祈愿卡池。"""

        self.multi_uid: bool = allow_multi_uid
        """是否允许合并多个UID的数据。若为 ``True`` ，则 ``uid`` 字段无效。"""

        if file != '':  # 使用文件直接新建本类。
            self.load(file)

        self.handler = handler if callable(handler) else None
        """获取抽卡记录的回调函数。
        
        当获取抽卡记录时会自动调用本函数，以向外界传递操作进度。
        """

        self._url_part = str()
        self._url_params = dict()
        # 从日志里获取到的URL的GET请求参数。

    def __repr__(self) -> str:
        r_ws = [repr(self.wishes[i]) for i in range(len(self.wishes))]
        return '<%s(v%s) 创建：%s，修改：%s，语言：%s，地区：%s，抽卡记录：%s>' % (
            self.__class__.__name__,
            GachaPlayer.VERSION,
            self.create,
            self.modify,
            self.language,
            self.region,
            '' if len(r_ws) == 0 else ('[%s]' % ', '.join(r_ws)),
        )

    def __len__(self) -> int:
        return sum([len(self.wishes[i]) for i in range(len(self.wishes))])

    def __iadd__(self, other):
        if type(other) is not self.__class__:
            raise TypeError(
                '仅支持与 %s 类型相加，而提供的是 %s' % (
                    self.__class__.__name__, type(other).__name__,
                )
            )
        if other.uid != '':
            if self.multi_uid:
                self.uid = other.uid
            else:
                raise MultiUIDError(self.uid, other.uid)
        for i in range(len(self.wishes)):
            self.wishes[i] += other.wishes[i]

        self.modify = max(self.create, self.modify, other.create, other.modify)
        return self

    def _call_handler(self, code: int, message: str, **kwargs) -> None:
        if callable(self.handler):
            self.handler(code, message, **kwargs)
        else:
            pass

    def map_wishes(self) -> dict:
        """获取所有祈愿卡池 gacha_type 与 wish_name 的对照表。"""
        t = dict()
        for i in range(len(self.wishes)):
            t[self.wishes[i].wish_type] = self.wishes[i].wish_name
        return t

    def init(self) -> None:
        """进行初始化以准备获取数据。如有需要，可以再次调用以重新初始化。"""

        # ################################
        # 查找本地output_log.txt：
        self._call_handler(self.PROCESS_READ_LOG, '正在查找本地日志')
        assert 'USERPROFILE' in os.environ, 'Windows 系统变量中没有配置 USERPROFILE'
        path_t = os.path.join(
            os.environ['USERPROFILE'],
            r'AppData\LocalLow\miHoYo\*\output_log.txt'
        )
        path_log_cn = path_t.replace('*', '原神')
        path_log_gl = path_t.replace('*', 'Genshin Impact')
        if os.path.isfile(path_log_cn):
            path_log = path_log_cn
        elif os.path.isfile(path_log_gl):
            path_log = path_log_gl
        else:
            raise CollectingError('没有找到output_log.txt，请尝试进入原神并浏览一下抽卡记录。')

        # ################################
        # 获取日志中的URL并解析：
        self._call_handler(self.PROCESS_PARSE_LOG, '正在解析日志中的URL')
        url = ''
        with open(path_log, 'r', encoding='GBK') as f:
            for line in f.readlines()[::-1]:
                if line.startswith('OnGetWebViewPageFinish:'):
                    url = line
                    # print(parse_qs(urlparse(url).query)['authkey'])
                    break
        if len(url) == 0:
            raise CollectingError('没有找到URL，请尝试在原神中浏览一下抽卡记录。')
        self._url_part = urlparse(url).query
        self._url_params = dict(parse_qsl(self._url_part))
        self.language = self._url_params['lang']
        self.region = self._url_params['region']
        # 这里有个坑：
        # qs返回{key: [value]}类型，qsl返回[(key, value)]类型，
        # 而前者的返回值在经过urlencode()后会跟原URL不一致。

        # ################################
        # 测试URL中的GET参数是否正确：
        self._call_handler(self.PROCESS_TEST_PASSKEY, '正在测试URL参数')
        content = http_get_json(
            url='https://hk4e-api.mihoyo.com/event/gacha_info/api/getGachaLog?' + self._url_part
        )
        # content = {
        #     "retcode": 0,
        #     "message": "OK",
        #     "data": {
        #         "page": "0",
        #         "size": "6",
        #         "total": "0",
        #         "list": [],
        #         "region": "cn_gf01"
        #     }
        # }
        if content['retcode'] != 0:
            raise CollectingError('请求数据失败：(%s) %s' % (
                content['retcode'], content['message']
            ))

        # ################################
        # 获取当前卡池类型：
        self._call_handler(self.PROCESS_GET_WISHES_TYPE, '正在获取卡池类型')
        content = http_get_json(
            url='https://hk4e-api.mihoyo.com/event/gacha_info/api/getConfigList?' + self._url_part
        )
        # content == {
        #     'retcode': 0,
        #     'message': 'OK',
        #     'data': {
        #         'gacha_type_list': [
        #             {'id': '4', 'key': '200', 'name': '常驻祈愿'},
        #             {'id': '14', 'key': '100', 'name': '新手祈愿'},
        #             {'id': '15', 'key': '301', 'name': '角色活动祈愿'},
        #             {'id': '16', 'key': '302', 'name': '武器活动祈愿'}
        #         ],
        #         'region': 'cn_gf01'
        #     }
        # }
        if content['data'] is None:
            raise CollectingError('获取卡池类型失败。(%s) %s' % (
                content['retcode'], content['message']
            ))
        wish_map = content['data']['gacha_type_list']
        for i in range(len(self.wishes)):
            for j in wish_map:
                if self.wishes[i].wish_type == j['key']:
                    self.wishes[i].wish_name = j['name']
                    break
        self._call_handler(self.PROCESS_END_INIT, '初始化完毕')

    def _build_records_api(self,
                           wish_type: str,
                           size: int,
                           page: int,
                           end_id: str
                           ) -> str:
        """构造查询抽卡记录的GET请求的地址。"""
        url = 'https://hk4e-api.mihoyo.com/event/gacha_info/api/getGachaLog?'
        params = dict(**self._url_params)  # 避免直接修改日志文件里的URL的参数
        params['size'] = str(size)
        params['gacha_type'] = wish_type
        params['page'] = str(page)
        params['end_id'] = end_id
        return url + urlencode(params)

    def _collect_one(self, wish_type: str) -> list:
        """获取某一祈愿卡池的抽卡记录。"""
        page = 1
        end_id = '0'
        result = []
        while True:
            content = http_get_json(
                url=self._build_records_api(
                    wish_type=wish_type,
                    size=self._PAGE_SIZE_MAX,
                    page=page,
                    end_id=end_id
                )
            )
            # content = {
            #     "retcode": 0,
            #     "message": "OK",
            #     "data": {
            #         "page": "0",
            #         "size": "20",
            #         "total": "0",
            #         "list": [
            #             {
            #                 "uid": "玩家id",
            #                 "gacha_type": "200",
            #                 "item_id": "",
            #                 "count": "1",
            #                 "time": "2021-01-21 18:08:54",
            #                 "name": "芭芭拉",
            #                 "lang": "zh-cn",
            #                 "item_type": "角色",
            #                 "rank_type": "4",
            #                 "id": "19位阿拉伯数字，抽卡记录的ID"
            #             }
            #         ],
            #         "region": "cn_gf01"
            #     }
            # }
            if content['data']['list'] is None:
                break
            if len(content['data']['list']) == 0:
                break
            for item in content['data']['list']:
                result.append(item)
            end_id = content['data']['list'][-1]['id']
            page += 1
            self._call_handler(
                code=self.PROCESS_GET_RECORD_PAGE,
                message='获取第 %i 页记录' % page,
                page=page,
            )
            sleep(random() * 2)
        return result

    def collect(self) -> None:
        """获取所有祈愿卡池的抽卡记录。"""
        self.modify = datetime.utcnow().strftime(self._UTCTIME_F)
        self.create = self.modify if self.create == '' else self.create
        for i in range(len(self.wishes)):
            self._call_handler(
                code=self.PROCESS_GET_WISH_RECORDS,
                message='获取【%s】的记录' % self.wishes[i].wish_name,
                wish=self.wishes[i].wish_name,
            )
            # 获取并匿名化处理数据：（因为原始数据是从新到旧的，所以直接逆序遍历）
            page = self._collect_one(self.wishes[i].wish_type)[::-1]
            for j in range(len(page)):
                self.uid = page[j].pop('uid')
                page[j].pop('gacha_type')
                page[j].pop('item_id')
                page[j].pop('count')
                page[j].pop('lang')
                page[j]['RID'] = sm3r(page[j].pop('id'))
            self.wishes[i].records = page
        self.uid = sm3u(self.uid)
        self._call_handler(self.PROCESS_END_DOWNLOAD, '记录获取完毕')

    def dump(self, file: str, save_uid: bool = False) -> None:
        """将获取到的抽卡记录保存为紧凑但兼有换行、易于浏览的JSON格式文件。

        :param file: 具体的文件地址。
        :param save_uid: 是否保存加密过的uid。
                         uid对于海量数据分析并无作用，如需去除重复，请同时使用RID与时间两个字段。
        """

        # 这个函数只是为了dump一份格式好看一点的json文件而已，不到万不得已最好不要改动。
        # 缩进采用两个空格。
        # 用[:-2]是为了去掉多余的逗号以符合JSON语法。

        # ################################
        # json_part_wishes = dumps(self.map_wishes(), ensure_ascii=False)
        json_part_wishes = ''
        wishes = self.map_wishes()
        for item in wishes:
            json_part_wishes += '    "{key}": "{value}",\n'.format(
                key=item,
                value=wishes[item],
            )
        if json_part_wishes != '':
            json_part_wishes = '\n' + json_part_wishes[:-2] + '\n  '

        # ################################
        json_part_records = ''
        for i in range(len(self.wishes)):
            temp = ''
            for record in self.wishes[i].records:
                temp += '      ' + dumps(record, ensure_ascii=False) + ',\n'
            else:
                if len(temp) > 0:
                    temp = '    "%s": [\n%s\n    ],\n' % (self.wishes[i].wish_type, temp[:-2])
                else:
                    temp = '    "%s": [],\n' % self.wishes[i].wish_type
            json_part_records += temp
        if len(json_part_records) > 0:
            json_part_records = '\n' + json_part_records[:-2] + '\n  '

        # ################################
        json_content = JSON_DUMP_TEMPLATE % (
            GachaPlayer.VERSION,
            self.create,
            self.modify,
            self.uid if save_uid else '',
            self.language,
            self.region,
            ('{%s}' % json_part_wishes) if json_part_wishes != '' else '',
            ('{%s}' % json_part_records) if json_part_records != '' else '',
        )
        with open(file, 'w', encoding='UTF-8') as f:
            f.write(json_content)

    def load(self, file: str) -> str:
        """从JSON格式文件中载入原神祈愿抽卡记录，并覆盖原有的数据。

        :param file: 具体的文件地址。
        :returns: 抽卡记录的采集器针对的游戏版本。失败返回空字符串。"""
        ret = ''
        with open(file, 'r', encoding='UTF-8') as f:
            try:
                obj = load(f)
            except JSONDecodeError:
                obj = dict()
            if type(obj) is not dict:
                return ret
            if 'collector' in obj:
                self.create = obj['collector'].get('create', '')
                self.modify = obj['collector'].get('modify', '')
                ret = obj['collector'].get('version', '')
            if 'infos' in obj:
                self.uid = obj['infos'].get('uid', '')
                self.language = obj['infos'].get('lang', '')
                self.region = obj['infos'].get('region', '')
            if 'wishes' in obj:
                for i in range(len(self.wishes)):
                    self.wishes[i].wish_name = obj['wishes'][self.wishes[i].wish_type]
            if 'records' in obj:
                for i in range(len(self.wishes)):
                    if self.wishes[i].wish_type in obj['records']:
                        self.wishes[i].records = obj['records'][self.wishes[i].wish_type]
        return ret

    def sort(self):
        """按时间戳和抽卡记录ID，对每一个祈愿卡池的抽卡数据进行排序。"""
        for i in range(len(self.wishes)):
            self.wishes[i].sort()

    @staticmethod
    def earliest() -> str:
        """当前版本的原神只能获取最近六个月的数据。
        本方法返回一个字符串，表示可以获取到最早的记录的日期。"""
        return (datetime.now() - timedelta(days=6 * 30 - 1)).strftime('%Y-%m-%d')
