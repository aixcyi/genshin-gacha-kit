from xlsxwriter import Workbook

from ggacha import GachaPlayer
from ggacha.throwable import GenshinBaseException


def save_as_xlsx(obj: GachaPlayer, file: str):
    """将本项目的抽卡记录数据加工存储为带有颜色标记的xlsx文件。所存储的信息有：
    时间、名称、类别、星级、总第几抽、保底内第几抽。

    同样导出该格式的项目有：
      - https://github.com/sunfkny/genshin-gacha-export （v1.1.19）
      - https://github.com/biuuu/genshin-wish-export （v0.6.3）
    """
    if not obj:
        raise GenshinBaseException('没有抽卡数据。')

    if any([obj.language == lang for lang in ['cn', 'zh-cn', 'zh-tw']]):
        titles = ['时间', '名称', '类别', '星级', '总第几抽', '保底内第几抽']
    else:
        titles = ['Time', 'Item', 'Type', 'Star', 'No.', '[No.]']

    book = Workbook(filename=file)

    # 添加样式：
    style_head = book.add_format(  # 表格头部
        {"align": "left", "font_name": "微软雅黑", "bg_color": "#dbd7d3", "border_color": "#c4c2bf", "border": 1,
         "color": "#757575", "bold": True}
    )
    style_rank3 = book.add_format(  # 表格内容-三星
        {"align": "left", "font_name": "微软雅黑", "bg_color": "#ebebeb", "border_color": "#c4c2bf", "border": 1,
         "color": "#8e8e8e"}
    )
    style_rank4 = book.add_format(  # 表格内容-四星
        {"align": "left", "font_name": "微软雅黑", "bg_color": "#ebebeb", "border_color": "#c4c2bf", "border": 1,
         "color": "#a256e1", "bold": True}
    )
    style_rank5 = book.add_format(  # 表格内容-五星
        {"align": "left", "font_name": "微软雅黑", "bg_color": "#ebebeb", "border_color": "#c4c2bf", "border": 1,
         "color": "#bd6932", "bold": True}
    )

    # 按卡池来分表写入：
    for wish in obj.wishes:
        if type(wish.records) is not list:
            continue
        row = 0
        counter = 0
        sheet = book.add_worksheet(wish.wish_name if wish.wish_name != '' else wish.wish_type)
        sheet.write_row(row, 0, cell_format=style_head, data=titles)
        wish.sort()
        for record in wish.records:
            if type(record) is not dict:
                continue
            row += 1
            counter += 1
            data = [record['time'], record['name'],
                    record['item_type'], int(record['rank_type']),
                    row, counter]
            sheet.write_row(row, 0, data, style_rank3)
            if record['rank_type'] == '5':
                counter = 0
                sheet.write_row(row, 0, data, style_rank5)
            elif record['rank_type'] == '4':
                sheet.write_row(row, 0, data, style_rank4)
            else:
                sheet.write_row(row, 0, data, style_rank3)
        sheet.set_column("A:A", 24)
        sheet.set_column("B:B", 14)
        sheet.set_column("C:C", 7)
        sheet.set_column("D:D", 7)
        sheet.set_column("F:F", 14)
        sheet.freeze_panes(1, 0)
    book.close()
