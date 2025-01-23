# 玩家信息路径
players_path = 'data/players.json'

# 曲目信息路径
musics_path = 'data/musics.json'

# 曲目名信息路径
musics_name_path = 'data/musics_name.json'

# 每首曲目定数信息路径
diff_path = 'data/diff.json'

# 建议信息路径
advice_path = 'data/advice.json'

# 封面/曲绘路径
cover_path = 'data/covers/'

# 各种图标路径
icon_path = 'data/icons/'

# 每首曲目对应的图像化信息
song_image_path = '.data/song_image/'


# 帮助菜单
help_message = """
    MuseDash B50帮助菜单

    md help\n\t唤出帮助菜单
    md bind+用户名/UID\n\t使用用户名或UID绑定账户
    md unbind\n\t解绑账户
    md b50\n\t查询当前绑定账户b50信息
    md diff+等级\n\t查询指定等级
    md song+曲名\n\t查询指定歌曲信息
    md acc+歌曲定数+准确率\n\t查询单曲得分
    md advice+建议\n\t向管理员提建议
    
    不过现在只写好了帮助菜单 绑定 解绑 查歌 建议部分，其他的指令不会有反应喔
    """

# moe网站链接
base_url = 'https://musedash.moe'

# 每首曲目定数链接
diff_url = 'https://api.musedash.moe/diffdiff'

# 所有专辑、曲目链接
albums_url = 'https://api.musedash.moe/albums'

# 搜索界面链接
search_url = 'https://api.musedash.moe/search/'

# 玩家链接（需在链接后拼接玩家uid访问）
player_url = 'https://musedash.moe/player/'


# 高贵的管理员名单（QQ号）
managers = ['3088044264', '2547168140', '2425366598', '2386950968', '2438810889', '1259734051']

# 黑名单（QQ号）
blacklist = []