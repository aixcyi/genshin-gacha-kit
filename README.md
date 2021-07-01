# 原神抽卡数据处理库

一个用于获取、存储、载入、合并、过滤、聚合原神抽卡数据的Python库。

 ![Version](https://img.shields.io/badge/Version-v0.1.0-orange.svg) ![Python](https://img.shields.io/badge/Base-Python%203.7-blue.svg) ![License](https://img.shields.io/badge/License-MIT-green.svg) ![Author](https://img.shields.io/badge/Author-aixcyi-purple.svg)

- 中文 ｜ [码云](https://gitee.com/aixcyi/genshin-gacha-kit)　[GitHub](https://github.com/aixcyi/genshin-gacha-kit)
- English ｜ writing...





## 目录

- [安装及使用](#安装及使用)
- [运行](#运行)
- [快速上手](#快速上手)
  - [GachaPlayer](#GachaPlayer)
  - [GachaWish](#GachaWish)
  - [扩展功能](#扩展功能)
  - [包结构](#包结构)
- [更多用法](#更多用法)
- [抽卡记录结构](#抽卡记录结构)
- [编号规则](#编号规则)
- [其它](#其它)
- [下一版本待办](#下一版本待办)
- [更新历史](#更新历史)





## 安装及使用

项目使用 **Python 3.7** 编写，已知使用到了内置数据类型`dict`键自然排序的新特性，如果你的Python低于这个版本，有可能会发生字典键排序错乱的问题。

然后使用命令行`pip list`查看本地的库及相应版本号，并确保已经安装好项目依赖的库（见下）。

如果还没有安装，或者版本低于以下要求，可以使用命令行执行以下语句：

```shell
pip install XlsxWriter==1.3.8
pip install requests==2.22.0
```

接下来通过 **开源仓库** 直接下载 **zip压缩包** 后解压到临时目录，并将 **ggacha** 文件夹移动到你的项目的源码根目录中。

之后，你就可以在你的代码中引用本项目了：

```Python
from ggacha import *

# 你的代码……
```

未来如果这个项目能够上传到PyPI，你可以使用`pip install GenshinGachaKit`的方式直接调用该项目。





## 运行

这个项目是第三方库喔，不是用来直接运行的。但为了快速展示核心功能，于是编写了`main.py`文件。

你可以直接在项目文件夹下，使用命令行执行：

```shell
python main.py
```

它会自动获取抽卡记录并保存到目录下以`raw_`开头的json文件。

如果你之前已经运行过，那么它将会自动合并以前的抽卡记录，然后把合并结果覆盖保存到以`ggr_`开头的json文件中，最后生成一个xlsx表格。

不过要注意，你需要先登录过游戏，并进入祈愿面板查看过抽卡的历史记录，这个demo才能执行到底而不报错。





## 快速上手

### GachaPlayer

这是个可以存储多个卡池的抽卡记录的类，主要功能是获取、合并、存储、载入一个玩家（所有卡池）的抽卡记录。

- 获取抽卡记录：

```Python
from ggacha import GachaPlayer

branch = GachaPlayer()
branch.init()
branch.collect()
```

- 将抽卡记录保存到本地：

```Python
branch.dump(r'C:\User\xxx\Desktop\我的抽卡记录-2021-6-13.json')
```

- 载入原有的抽卡记录：

```Python
master = GachaPlayer(file=r'C:\User\xxx\Desktop\我的抽卡记录-完整版.json')
```

- 合并两份数据并保存：

```Python
master += branch
master.dump(r'C:\User\xxx\Desktop\我的抽卡记录-完整版.json')
```

- 遍历所有卡池：

```Python
for wish in master.wishes:
    print(wish.wish_name)  # wish_name不为空字符串表明数据已经载入成功或获取完毕。
    print(wish.records)  # 当前卡池的所有抽卡记录
```

- 如果你的操作会改变一个卡池中的某一部分数据，则强烈建议用以下这种方式：

```Python
for i in range(len(master.wishes)):

    # 对抽卡记录进行排序：
    master.wishes[i].sort()

    # 修改卡池名称：
    if master.wishes[i].wish_type == '200':
    	master.wishes[i].wish_name = '常驻祈愿卡池'
        break
```



### GachaWish

这是存储单个卡池的抽卡记录的类，附加功能有抽卡记录合并、排序、聚合分析等。

如果需要获取/载入抽卡记录，请浏览 [GachaPlayer](#GachaPlayer)

- 获取某个卡池的抽卡记录数量：

```Python
print(len(wish))
```

- 将某个卡池的抽卡记录按照 **抽卡时间** 分组：（抽卡时间精确到秒钟，这样分组是划分出单抽和十连）

```Python
wish.group_by_time()
```

- 将某个卡池的抽卡记录按照 **抽卡时间在哪一天** 分组：

```Python
wish.group_by_day()
```

- 将某个卡池的抽卡记录 **同时** 按照(角色/武器)类型、星级、名称分组：

```Python
wish.group_by_all_type()
```



### 扩展功能

- 为玩家的抽卡记录生成Excel表格：

```Python
from ggacha import GachaPlayer
from ggacha.ext import save_as_xlsx

branch = GachaPlayer()
branch.init()
branch.collect()

save_as_xlsx(branch, '我的抽卡记录.xlsx')
```



### 包结构

- `ggacha` 当前项目
  - `GachaPlayer` 所有卡池的抽卡记录存取类。实现了面向玩家的抽卡记录的获取、合并、存储、载入。目前采用读取日志的方式获取。
  - `GachaWish` 单个卡池的抽卡记录存取类。实现了面向卡池的抽卡记录合并、排序、聚合分析。
  - `common` 公共包。提供通用的、不受游戏版本更新影响的函数。大部分为项目内部开发提供。
  - `ext` 扩展包。提供一些基于核心代码的扩展函数。
  - `res` 常量包。提供可以被代码直接调用的静态资源。
- `resources` 静态数据文件夹。
  - `items.json` 部分祈愿物品的信息（包括角色和武器）。
  - `wishes.json` 部分祈愿卡池的历史信息（概率提升的哪些角色）。
- `main.py` 对项目的简单应用。





## 更多用法

所有用法或相关信息以代码为准，如果文档中的信息已经落后或不齐全，请直接阅读 Python 代码中的 docstring 。

本项目的 docstring 遵循 **reStructuredText** 语法。

如果你使用 PyCharm 打开本项目，那么可以按下`Ctrl`+`Alt`+`S`打开设置面板，将

```
工具 > Python 集成工具 > 文档字符串 > 文档字符串格式
```

设置为`reStructuredText`，然后你不仅可以看到字符串被渲染了，而且将鼠标移动到代码上还会出现相应的提示。





## 抽卡记录结构

原始的抽卡记录的结构：

```json
{
    "uid": "玩家id",
    "gacha_type": "200",
    "item_id": "",
    "count": "1",
    "time": "2021-01-21 18:08:54",
    "name": "魔导绪论",
    "lang": "zh-cn",
    "item_type": "武器",
    "rank_type": "3",
    "id": "19位阿拉伯数字，抽卡记录的ID"
}
```

项目存取的抽卡记录的结构：

```json
{
    "time": "2021-01-21 18:08:54",
    "name": "芭芭拉",
    "item_type": "角色",
    "rank_type": "4",
    "RID": "项目生成的抽卡记录id"
}
```

其中`time`和`RID`字段是必须的，因为排序、合并等功能都依赖这两个字段。





## 编号规则

为了方便数据的转换，这个项目对角色和武器进行了编号。编号规则如下：

- 所有编号均使用十六进制整数表示，使用字符串形式记录在文件中。
- 目前编号只有四位数。以下所说的第几位均以字符串的 **从右到左** 表示。
- 对于角色
  - 第四位是所属国家：`1`蒙德，`2`璃月，`3`稻妻，`7`至冬。
  - 第三位是元素属性：`1`火系，`2`水系，`3`冰系，`4`雷系，`5`草系，`6`风系，`7`岩系。
  - 第二位是武器类型：`1`单手剑，`2`双手剑，`3`长柄武器，`4`法器，`5`弓。
  - 第一位是组合值，其中
    - 组合值对应二进制的第四位为`1`表示是五星角色，为`0`表示是四星角色。
    - 组合值对应二进制的低3位是序号，用于在所属国家、元素属性、武器类型、星级均相同时区分，序号取值范围是`0`到`7`。
  - 假定旅行者不属于角色，不分配编号。
  - 已被编号的角色其编号不会被更改，哪怕编号不符合以上规则。
  - 举例1：蒙德(`1`)风系(`6`)、使用弓箭(`5`)的五星角色温迪，其编号为`1658`，其中的`8`对应二进制`1000`。
  - 举例2：璃月(`2`)火系(`1`)、使用长枪(`3`)的四星角色香菱，其编号为`2130`，其中的`0`对应二进制`0000`。
- 对于武器
  - 第四位是武器类型：`1`单手剑，`2`双手剑，`3`长柄武器，`4`法器，`5`弓。
  - 第三位是武器星级：`A`五星，`B`四星，`C`三星。
  - 第二位是副属性：`1`攻击力，`2`防御力，`3`生命值，`4`元素充能效率，`5`元素精通，`6`物理伤害加成，`7`暴击率，`8`暴击伤害。
  - 第一位是序号，用于在星级、类型、副属性均相同时区分，序号取值范围是`0`到`15`。
- 编号顺序以游戏中的图鉴顺序为辅，以资源文件中的顺序为主。





## 其它

如果需要反馈代码错误，或者有任何疑问、问题，都可以提交 issue 。

如果你希望加入其它语言、协助更新静态资源，也可以提交 Pull Request 。





## 下一版本待办

- [ ] 为`README.md`添加英语版本（Python docstring 实在力不从心）。
- [ ] 为`GachaWish`添加历史信息查询和保底计算。
- [ ] 在README中添加对静态资源添的说明，比如祈愿卡池历史信息中的`plan`字段。
- [ ] 添加发起 Pull Request 的简易教程。





## 更新历史

### v0.1.0

- 2021/6/29：更新祈愿卡池的历史信息至1.6版本第二期。
- 2021/6/26：调整武器编号方式，并同步更改所有武器编号。
- 2021/6/23：为角色/武器信息添加韩文版本，并完善繁体中文、英文和日文版本。
- 2021/6/21：将祈愿卡池的历史信息中的`items`更改为本项目的编号。
- 2021/6/14：上传到开源仓库，并将包名定为`ggacha`以避免冲突。
- 2021/6/14：更新祈愿卡池的历史信息至1.6版本第一期。

### 新建

- 2021/?/??：添加了 [抽卡数据分析](https://voderl.github.io/genshin-gacha-analyzer/) 的Excel导出格式。
- 2021/3/25：重写了sunfkny的 [genshin-gacha-export](https://github.com/sunfkny/genshin-gacha-export) 。

