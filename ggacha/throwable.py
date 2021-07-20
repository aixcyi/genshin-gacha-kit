class GenshinBaseException(Exception):
    """原神祈愿卡池抽取记录处理程序所抛出的异常的基类。"""

    def __init__(self, *args):
        super(GenshinBaseException, self).__init__(*args)


class CollectingError(GenshinBaseException):
    """获取祈愿卡池抽取记录时触发的错误。"""

    def __init__(self, *args):
        super(CollectingError, self).__init__(*args)


class MergingException(GenshinBaseException):
    """合并异常。"""

    def __init__(self, *args):
        super(MergingException, self).__init__(*args)


class MultiRegionError(MergingException):
    """不允许合并两段不同地区的抽卡记录"""

    def __init__(self, region1, region2):
        super(MultiRegionError, self).__init__(
            self.__doc__ + '：%s  %s' % (region1, region2)
        )


class MultiLanguageError(MergingException):
    """不允许合并两段不同语言文字记载的抽卡记录"""

    def __init__(self, lang1, lang2):
        super(MultiLanguageError, self).__init__(
            '{tip}：{lang_a} 与 {lang_b}'.format(
                tip=self.__doc__,
                lang_a=lang1,
                lang_b=lang2,
            ),
        )


class MultiUIDError(MergingException):
    """不允许合并两段不同UID的抽卡记录"""

    def __init__(self, uid1, uid2):
        super(MultiUIDError, self).__init__(
            '{tip}：{uid_a} 与 {uid_b}'.format(
                tip=self.__doc__,
                uid_a=uid1,
                uid_b=uid2,
            ),
        )
