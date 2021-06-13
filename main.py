from os.path import isfile
from datetime import datetime

from gacha import GachaPlayer
from gacha.ext import save_as_xlsx


def handler_example(code: int, message: str, **kwargs):
    """当 GachaPlayer 进行某一步操作时会调用该函数，以向外界传达处理进度。

    如果需要自定义输出或根据进度进行其它操作，
    请在别处重写本函数，并在实例化对象时作为参数传递给 GachaPlayer。

    :param code: 操作进度码。凭该码识别当前进度。
    :param message: 默认的操作进度描述。
    :return: 该函数不需要有返回值。"""

    if code == GachaPlayer.PROCESS_END_DOWNLOAD:
        print(message)
        print('完成，按任意键退出...')
    elif code & 0x000F == 0x000F:
        print(message)
        print('='*16)
    else:
        print(message)


# 获取当天能获取的所有抽卡记录：（由于有六个月时间限制，所以可能不全）
print('今天能获取的最早的抽卡记录的时间是：', GachaPlayer.earliest())
branch = GachaPlayer(allow_multi_uid=False, handler=handler_example)
branch.init()
branch.collect()
file = './raw_%s_%s.json' % (branch.uid, datetime.now().strftime('%Y%m%d%H%M%S'))
branch.dump(file, save_uid=True)


# branch = GachaPlayer(allow_multi_uid=False, file='raw_8ea95e4175d38d1e_20210612232548.json')
# 将获取的记录当作支线，合并到总线中，形成一个完整版本：
path = 'ggr_%s.json' % branch.uid
if isfile(path):
    master = GachaPlayer(allow_multi_uid=True, file=path)
    master += branch
    master.dump(path, save_uid=True)

    # 为完整的抽卡记录生成Excel表格：
    save_as_xlsx(master, './ggr_%s.xlsx' % master.uid)
