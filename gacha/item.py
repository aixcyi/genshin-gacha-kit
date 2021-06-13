
# class Item:
#     """角色和武器的工具类。"""
#
#     # items == [{"item_id":"1022","name":"温迪","item_type":"角色","rank_type":"5"}, ...]
#     items = http_get_json(
#         url='https://webstatic.mihoyo.com/hk4e/gacha_info/cn_gf01/items/zh-cn.json'
#     )
#
#     # ################################################################
#     @staticmethod
#     def search(s: str) -> list:
#         """根据字符串查找角色或武器的相关信息。
#
#         :param s: 任意字符串。可以是名称、key、id等。
#         :return: 返回一个列表，包含一条或多条角色或武器的相关信息。如果找不到，将返回空列表。"""
#         try:
#             result = list()
#             for item in Item.items:
#                 if any([item[key].find(s) >= 0 for key in item]):
#                     result.append(item)
#             return result
#         except Exception:
#             return list()
#
#     # ################################################################
#     @staticmethod
#     def find(s: str) -> dict:
#         """根据字符串查找角色或武器的一条相关信息。
#
#         :param s: 任意字符串。可以是名称、key、id等。
#         :return: 比如{"item_id":"1022","name":"温迪","item_type":"角色","rank_type":"5"}
#                  当找不到时返回空字典。"""
#         try:
#             for item in Item.items:
#                 if any([item[key].find(s) >= 0 for key in item]):
#                     return item
#             else:
#                 return dict()
#         except Exception:
#             return dict()
#
#     # ################################################################
#     @staticmethod
#     def is_character(s: str) -> bool:
#         """判断一个字符串是不是角色（的相关信息）。"""
#         info = Item.find(s)
#         try:
#             return info['item_type'] == '角色' or \
#                    info['item_type'] == 'Character'
#         except KeyError:
#             return False
#
#     # ################################################################
#     @staticmethod
#     def is_weapon(s: str) -> bool:
#         """判断一个字符串是不是武器（的相关信息）。"""
#         info = Item.find(s)
#         try:
#             return info['item_type'] == '武器' or \
#                    info['item_type'] == 'Weapon'
#         except KeyError:
#             return False
#
#     # ################################################################
#     @staticmethod
#     def get_star(s: str) -> int:
#         """获取一个角色或武器的星级。返回一个整数，失败返回0。"""
#         info = Item.find(s)
#         try:
#             return int(info['rank_type'])
#         except (KeyError, ValueError):
#             return 0
