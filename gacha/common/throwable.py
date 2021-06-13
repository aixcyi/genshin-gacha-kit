class GenshinBaseException(Exception):
    """原神祈愿卡池抽取记录处理程序所抛出的异常的基类。"""

    def __init__(self, *args):
        super(GenshinBaseException, self).__init__(*args)
