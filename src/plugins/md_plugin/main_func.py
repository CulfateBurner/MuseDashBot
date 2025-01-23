import json
import asyncio

from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz, process
from PIL import Image, ImageDraw, ImageFont
import os

import psutil
from psutil._common import bytes2human
import winreg
import pynvml

from .help import *
from .utils import *

data_path = 'data/'

async def save_player(qq, name, uid):
    with open(players_path, 'r') as f:
        data = json.load(f)

    qq_set = list(data.keys())

    player_info = [name, uid]
    new_player_data = {qq: player_info}

    if qq not in qq_set:
        data.update(new_player_data)

    with open(players_path, 'w') as f:
        json.dump(data, f, indent=4)

async def search_uid_by_name(name):
    response = await get_url_text(url=search_url + name)

    # 将得到的数据转化为二维列表形式
    players = json.loads(response)

    if len(players) == 0:
        return '', False
    else:
        name = players[0][0]
        uid = players[0][1]
        if len(players) == 1:
            return uid, True
        else:
            return uid, False

async def search_name_by_uid(uid):
    response = await get_url_text(player_url + uid)
    soup = BeautifulSoup(response, 'html.parser')
    name = soup.find(name="h1").text.strip()
    return name

async def search_info_by_qq(qq):
    with open(players_path, 'r') as f:
        player_data = json.load(f)

    if qq in player_data:
        return True, player_data[qq][0], player_data[qq][1]
    else:
        return False, '', ''

async def bind_name(qq, name):
    uid, only = await search_uid_by_name(name)
    if only:
        await save_player(qq, name, uid)
        return True, name
    else:
        return False, ''

async def bind_uid(qq, uid):
    name = await search_name_by_uid(uid)
    if name != 'User not Found':
        await save_player(qq, name, uid)
        return True, name
    return False, name

async def show_all_players():
    with open(players_path, 'r') as f:
        players_data = json.load(f)

    player_names = []
    for qq in players_data:
        player_names.append(players_data[qq][0])

    num_players = len(player_names)
    message = '查询到以下玩家:'
    for i in range(num_players):
        message += f'\n{i+1}. {player_names[i]}'

    return message

async def unbind(qq):
    with open(players_path, 'r') as f:
        player_data = json.load(f)

    if qq in player_data:
        name = player_data[qq][0]
        del player_data[qq]
        with open(players_path, 'w') as f:
            json.dump(player_data, f, indent=4)
        return True, name
    else:
        return False, ''

async def update_song_info():
    # 官谱信息
    response = await get_url_text(albums_url)
    albums = json.loads(response)

    # moe定数信息
    response = await get_url_text(diff_url)
    diff_info = json.loads(response)

    musics = {}
    musics_name = []
    diff = {}
    for i in range(12):
        diff[str(i + 1)] = {}
    diff['?'] = {}
    diff['¿'] = {}
    diff['L'] = {}
    diff['E'] = {}
    diff['N'] = {}
    diff['H'] = {}
    diff['IG'] = {}
    diff['Jh'] = {}
    diff['a2'] = {}
    diff['Eh'] = {}
    diff['〇'] = {}

    for album in albums:
        for music_uid in albums[album]['music']:
            music_info = albums[album]['music'][music_uid]
            if music_info['name'] == music_info['ChineseS']['name']:
                pass
            else:
                music_info['name'] = music_info['ChineseS']['name']
            useful_music_info = {i: music_info[i] for i in list(music_info)[0:7]}
            musics[music_uid] = useful_music_info
            useful_music_info['diff'] = [0, 0, 0, 0, 0]
            useful_music_info['album'] = albums[album]['ChineseS']['title']
            musics_name.append(music_info['name'])
            if music_uid == '39-8':
                img = Image.open(cover_path + 'qu_jianhai_de_rizi_cover.png')
                new_img_name = 'fm_17314_sugar_radio_cover.png'
                img.save(cover_path + new_img_name)
            if music_uid == '33-12':
                img = Image.open(cover_path + 'chaos_cover.png')
                new_img_name = 'chaos_glitch_cover.png'
                img.save(cover_path + new_img_name)


    for diff_list in diff_info:
        musics[diff_list[0]]['diff'][diff_list[1]] = diff_list[4]

    with open(musics_path, 'w') as f:
        json.dump(musics, f, indent=4)

    for music_uid in musics:
        music_info = musics[music_uid]
        for i in range(5):
            difficulty = musics[music_uid]['difficulty'][i]
            if difficulty != '0':
                if i <= 2:
                    diff[difficulty][music_info['name']] = [music_info['diff'][i], music_info['author']]
                else:
                    diff[difficulty][music_info['name'] + '(里)'] = [music_info['diff'][i], music_info['author']]

    for music_uid in musics:
        # 两首没有曲绘的歌单独处理
        if music_uid != '39-8' and music_uid != '33-12':
            await save_song_info_image(music_uid)
        elif music_uid == '39-8':
            img = Image.open(cover_path + 'qu_jianhai_de_rizi_cover.png')
            new_img_name = 'fm_17314_sugar_radio_cover.png'
            img.save(cover_path + new_img_name)
            await save_song_info_image(music_uid)
        else:
            img = Image.open(cover_path + 'chaos_cover.png')
            new_img_name = 'chaos_glitch_cover.png'
            img.save(cover_path + new_img_name)
            await save_song_info_image(music_uid)


    for level in diff:
        diff[level] = sorted(diff[level].items(), key=lambda x: x[1][0], reverse=True)
    diff = dict(diff)

    with open(musics_name_path, 'w') as f:
        json.dump(musics_name, f, indent=4)

    with open(diff_path, 'w') as f:
        json.dump(diff, f, indent=4)

async def get_song_info(name):
    with open(musics_name_path, 'r') as f:
        musics_name = json.load(f)

    with open(musics_path, 'r') as f:
        musics_data = json.load(f)

    close_name = process.extract(name, musics_name, scorer=fuzz.partial_ratio, limit=2)
    num_songs = len(close_name)
    if num_songs == 0:
        return '找不到喵~，再想想'

    uid_list = ['', '']
    for uid in musics_data:
        if musics_data[uid]['name'] == close_name[0][0]:
            uid_list[0] = uid
            break

    for uid in musics_data:
        if musics_data[uid]['name'] == close_name[1][0] and uid != uid_list[0]:
            uid_list[1] = uid
            break

    return uid_list

    # message = '查找到以下可能符合的曲目:\n'
    # for num_song in range(num_songs):
    #     message += f'{num_song + 1}. {close_name[num_song][0]}'
    #     for uid in musics_data:
    #         if musics_data[uid]['name'] == close_name[num_song][0]:
    #             designer = musics_data[uid]["levelDesigner"]
    #             difficulty = ['萌新', '高手', '大触', '里谱', '里谱']
    #             message += f'\n曲师:{musics_data[uid]["author"]}'
    #             message += f'\nbpm:{musics_data[uid]["bpm"]}'
    #             message += f'\n难度:'
    #             i = 0
    #             j = 0
    #             while i < 5:
    #                 if musics_data[uid]['difficulty'][i] != '0':
    #                     diff = musics_data[uid]["diff"][i]
    #                     formatted_diff = '%.2f' % diff
    #                     message += (f'\n{difficulty[i]}:{musics_data[uid]["difficulty"][i]}, '
    #                                 f'(moe定数:{formatted_diff})'
    #                                 f'\n\t谱师:{designer[j]}')
    #                 i += 1
    #                 if j + 1 < len(designer):
    #                     j += 1
    #     message += '\n\n'
    # return message

async def query_song_info(qq, name):
    # 查询用户上榜记录
    flag, user_name, user_uid = await search_info_by_qq(qq)
    song_uids = await get_song_info(name)
    song_uid = song_uids[0]
    user_url = f"https://musedash.moe/player/{user_uid}"
    response = await get_url_text(user_url)
    soup = BeautifulSoup(response, 'html.parser')
    # print(song_uid)

    record_list = [None] * 5
    for i in range(5):
        result = soup.find('a', attrs={'href': f'/music/{song_uid}/{i}'})
        try:
            record_info = result.parent.parent.previous_sibling.previous_sibling.text.split(' ', maxsplit=2)
            record_info.append(result.text)
            record_list[i] = record_info
        except AttributeError:
            continue
    # print(record_list)

    with open(musics_path, 'r') as f:
        musics_data = json.load(f)

    song_name = musics_data[song_uid]['name']
    cover_name = cover_path + musics_data[song_uid]['cover'] + '.png'
    author_name = musics_data[song_uid]['author']
    level_designer = musics_data[song_uid]['levelDesigner']
    bpm_info = 'BPM:' + musics_data[song_uid]['bpm']
    album_name = '曲包:' + musics_data[song_uid]['album']
    difficulty_info = musics_data[song_uid]['difficulty']
    diff_info = musics_data[song_uid]['diff']
    uid_info = 'UID:' + song_uid
    difficulty_name = ['萌新', '高手', '大触', '里谱', '东方']

    # print(difficulty_info)

    # 对moe定数保留两位小数
    for i in range(5):
        diff = diff_info[i]
        formatted_diff = '%.2f' % diff
        diff_info[i] = formatted_diff


    background = Image.new('RGBA', (1080, 720), (18, 18, 18, 255))
    table_title = Image.new('RGBA', (960, 50), (18, 18, 18, 255))
    table1 = Image.new('RGBA', (960, 50), (28, 28, 28, 255))
    table2 = Image.new('RGBA', (960, 50), (48, 48, 48, 255))

    # 为美观，制作第二层背景
    for i in range(1020):
        for j in range(640):
            background.putpixel((i + 30, j + 30), (33, 33, 33, 255))

    cover = Image.open(cover_name)
    star_e = Image.open(icon_path + 'IconEasy.png')
    star_e = star_e.resize((60, 60), Image.LANCZOS)
    star_h = Image.open(icon_path + 'IconHard.png')
    star_h = star_h.resize((60, 60), Image.LANCZOS)
    star_m = Image.open(icon_path + 'IconMaster.png')
    star_m = star_m.resize((60, 60), Image.LANCZOS)
    star_hid = Image.open(icon_path + 'IconHidden.png')
    star_hid = star_hid.resize((60, 60), Image.LANCZOS)
    star_hid2 = Image.open(icon_path + 'IconHidden2.png')
    star_hid2 = star_hid2.resize((60, 60), Image.LANCZOS)

    # 将曲绘放到背景上
    cover = cover.resize((330, 330))
    cover_width, cover_height = cover.size
    for i in range(cover_width):
        for j in range(cover_height):
            pixel = cover.getpixel((i, j))
            if pixel[3] != 0:
                background.putpixel((i + 60, j + 60), pixel)

    # 定义字体及大小
    title_font = ImageFont.truetype('msyh.ttc', 40)
    author_font = ImageFont.truetype('simsun.ttc', 30)
    difficulty_font = ImageFont.truetype('/////////////msyhbd.ttc', 32)
    text_font = ImageFont.truetype('simhei.ttf', 24)
    table_font = ImageFont.truetype('STXIHEI.TTF', 20)

    drawer = ImageDraw.Draw(background)
    # 定义高度和宽度的偏移
    height_offset = 60
    width_offset = 420

    title_size = title_font.getbbox(song_name)
    title_width = title_size[2] - title_size[0]
    title_height = title_size[3] - title_size[1]
    author_size = author_font.getbbox(author_name)
    author_width = author_size[2] - author_size[0]
    author_height = author_size[3] - author_size[1]
    # 处理超长的曲名和曲师名
    if title_width <= 640:
        drawer.text((width_offset, height_offset), song_name, font=title_font, fill='white')
    else:
        song_length = len(song_name)
        song_name_list = [song_name[0:int(song_length / 2)], song_name[int(song_length / 2):]]
        drawer.text((width_offset, height_offset), song_name_list[0], font=title_font, fill='white')
        height_offset += title_height
        drawer.text((width_offset, height_offset), song_name_list[1], font=title_font, fill='white')
    height_offset += (title_height + 20)

    if author_width <= 640:
        drawer.text((width_offset, height_offset), author_name, font=author_font, fill='grey')
    else:
        author_length = len(author_name)
        author_name_list = [author_name[0:int(author_length / 2)], author_name[int(author_length / 2):]]
        drawer.text((width_offset, height_offset), author_name_list[0], font=author_font, fill='grey')
        height_offset += author_height
        drawer.text((width_offset, height_offset), author_name_list[1], font=author_font, fill='grey')
    height_offset += (author_height + 20)

    # 向星星中加入难度数字
    star_width, star_height = star_e.size
    star_list = [star_e, star_h, star_m, star_hid, star_hid2]
    for i in range(5):
        fontsize = difficulty_font.getbbox(difficulty_info[i])
        x = fontsize[2] - fontsize[0]
        x = star_width / 2 - x / 2
        y = 14
        if difficulty_info[i] != '0':
            star_drawer = ImageDraw.Draw(star_list[i])
            star_drawer.text((x, y), difficulty_info[i], font=difficulty_font, fill='grey')

    # 将星星加入图中
    for i in range(star_width):
        for j in range(star_height):
            width_offset = 420
            if difficulty_info[0] != '0' and star_e.getpixel((i, j))[3] != 0:
                background.putpixel((i + width_offset, j + height_offset), star_e.getpixel((i, j)))
                width_offset += 100
            if difficulty_info[1] != '0' and star_h.getpixel((i, j))[3] != 0:
                background.putpixel((i + width_offset, j + height_offset), star_h.getpixel((i, j)))
                width_offset += 100
            if difficulty_info[2] != '0' and star_m.getpixel((i, j))[3] != 0:
                background.putpixel((i + width_offset, j + height_offset), star_m.getpixel((i, j)))
                width_offset += 100
            if difficulty_info[3] != '0' and star_hid.getpixel((i, j))[3] != 0:
                background.putpixel((i + width_offset, j + height_offset), star_hid.getpixel((i, j)))
                width_offset += 100
            if difficulty_info[3] != '0' and difficulty_info[4] != '0' and star_hid2.getpixel((i, j))[3] != 0:
                background.putpixel((i + width_offset, j + height_offset), star_hid2.getpixel((i, j)))
                width_offset += 100
            if difficulty_info[3] == '0' and difficulty_info[4] != '0' and star_hid2.getpixel((i, j))[3] != 0:
                background.putpixel((i + width_offset, j + height_offset), star_hid2.getpixel((i, j)))
                width_offset += 100

    width_offset = 420
    drawer.text((width_offset, height_offset + 80), uid_info, font=text_font, fill='white')
    height_offset += 40
    drawer.text((width_offset, height_offset + 80), bpm_info, font=text_font, fill='white')
    height_offset += 40
    drawer.text((width_offset, height_offset + 80), album_name, font=text_font, fill='white')

    height_offset = 420
    width_offset = 60

    # 添加表头
    for i in range(960):
        for j in range(40):
            background.putpixel((i + width_offset, j + height_offset), (18, 18, 18, 255))
    # title = '难度' + ' ' * 10 + 'MOE定数' + ' ' * 10 + '上榜记录' + ' ' * 20 + '上榜搭配'
    # drawer.text((width_offset + 15, height_offset + 8), title, font=text_font, fill='white')

    num_diff = 0
    for i in range(5):
        if difficulty_info[i] != '0':
            num_diff += 1

    lines = num_diff
    height_offset += 40
    flag = 0
    while num_diff > 0:
        if flag % 2 == 0:
            for i in range(960):
                for j in range(40):
                    background.putpixel((i + width_offset, j + height_offset), (28, 28, 28, 255))
            flag += 1
            num_diff -= 1
            height_offset += 40
        else:
            for i in range(960):
                for j in range(40):
                    background.putpixel((i + width_offset, j + height_offset), (48, 48, 48, 255))
            flag += 1
            num_diff -= 1
            height_offset += 40

    height_offset = 420
    width_offset = 60

    drawer.text((width_offset + 15, height_offset + 8), '难度', font=text_font, fill='white')
    drawer.text((width_offset + 120, height_offset + 8), 'moe定数', font=text_font, fill='white')
    j = 0
    for i in range(lines):
        if difficulty_info[i] != '0':
            drawer.text((width_offset + 15, height_offset + 48 + 40 * j), difficulty_name[i], font=text_font, fill='white')
            drawer.text((width_offset + 120, height_offset + 48 + 40 * j), diff_info[i], font=text_font, fill='white')
            j += 1

    drawer.text((width_offset + 240, height_offset + 8), '上榜记录', font=text_font, fill='white')
    for i in range(lines):
        if record_list[i] != None:
            record = f'acc: {record_list[i][0]}, score: {record_list[i][1]}, rank: {record_list[i][3]}'
            drawer.text((width_offset + 240, height_offset + 48 + 40 * i), record, font=text_font, fill='white')
        else:
            drawer.text((width_offset + 240, height_offset + 48 + 40 * i), '暂无', font=text_font, fill='white')

    try:
        background.save(f'./data/song_image/{qq}/{song_uid}.png')
    except FileNotFoundError:
        os.mkdir(f'./data/song_image/{qq}')
        background.save(f'./data/song_image/{qq}/{song_uid}.png')

async def save_song_info_image(uid):

    with open(musics_path, 'r') as f:
        musics_data = json.load(f)

    song_name = musics_data[uid]['name']
    cover_name = cover_path + musics_data[uid]['cover'] + '.png'
    author_name = musics_data[uid]['author']
    level_designer = musics_data[uid]['levelDesigner']
    bpm_info = 'BPM:' + musics_data[uid]['bpm']
    album_name = '曲包:' + musics_data[uid]['album']
    difficulty_info = musics_data[uid]['difficulty']
    diff_info = musics_data[uid]['diff']
    uid_info = 'UID:' + uid

    # 对moe定数保留两位小数
    for i in range(5):
        diff = diff_info[i]
        formatted_diff = '%.2f' % diff
        diff_info[i] = formatted_diff

    background = Image.new('RGBA', (1080, 720), (0, 0, 0, 255))
    cover = Image.open(cover_name)
    star_e = Image.open(icon_path + 'IconEasy.png')
    star_e = star_e.resize((80, 80), Image.LANCZOS)
    star_h = Image.open(icon_path + 'IconHard.png')
    star_h = star_h.resize((80, 80), Image.LANCZOS)
    star_m = Image.open(icon_path + 'IconMaster.png')
    star_m = star_m.resize((80, 80), Image.LANCZOS)
    star_hid = Image.open(icon_path + 'IconHidden.png')
    star_hid = star_hid.resize((80, 80), Image.LANCZOS)
    star_hid2 = Image.open(icon_path + 'IconHidden2.png')
    star_hid2 = star_hid2.resize((80, 80), Image.LANCZOS)
    star_width, star_height = star_e.size

    cover = cover.resize((330, 330))
    cover_width, cover_height = cover.size
    for i in range(0, cover_width):
        for j in range(0, cover_height):
            if cover.getpixel((i, j))[3] != 0:
                background.putpixel((i + 60, j + 60), cover.getpixel((i, j)))




    # 定义字体及大小
    title_font = ImageFont.truetype('msyh.ttc', 40)
    author_font = ImageFont.truetype('simsun.ttc', 30)
    difficulty_font = ImageFont.truetype('/////////////msyhbd.ttc', 32)
    text_font = ImageFont.truetype('simhei.ttf', 24)
    table_font = ImageFont.truetype('STXIHEI.TTF', 20)

    # 处理里谱
    # hidden_df = 1
    # hidden = 1
    # if difficulty_info[4] == '0':
    #     del difficulty_info[4]
    #     hidden_df = 0
    # if difficulty_info[3] == '0':
    #     del difficulty_info[3]
    #     hidden = 0
    # if difficulty_info[2] == '0':
    #     del difficulty_info[2]
    # len_difficulty = len(difficulty_info)

    drawer = ImageDraw.Draw(background)
    title_size = title_font.getbbox(song_name)
    title_width = title_size[2] - title_size[0]
    title_height = title_size[3] - title_size[1]
    author_size = author_font.getbbox(author_name)
    author_width = author_size[2] - author_size[0]
    author_height = author_size[3] - author_size[1]
    if title_width <= 640 and author_width <= 640:
        drawer.text((420, 60), song_name, font=title_font, fill='white')
        drawer.text((420, 120), author_name, font=author_font, fill='grey')
        drawer.text((420, 250), uid_info, font=text_font, fill='white')
        drawer.text((420, 290), bpm_info, font=text_font, fill='white')
        drawer.text((420, 330), album_name, font=text_font, fill='white')
    elif title_width > 640:
        song_length = len(song_name)
        song_name_list = [song_name[0:int(song_length / 2)], song_name[int(song_length / 2): ]]
        drawer.text((420, 60), song_name_list[0], font=title_font, fill='white')
        drawer.text((420, 60 + title_height), song_name_list[1], font=title_font, fill='white')
        drawer.text((420, 120 + title_height), author_name, font=author_font, fill='grey')
        drawer.text((420, 250 + title_height), uid_info, font=text_font, fill='white')
        drawer.text((420, 290 + title_height), bpm_info, font=text_font, fill='white')
        drawer.text((420, 330 + title_height), album_name, font=text_font, fill='white')
    elif author_width > 640:
        author_length = len(author_name)
        author_name_list = [author_name[0:int(author_length / 2)], author_name[int(author_length / 2):]]
        drawer.text((420, 60), song_name, font=title_font, fill='white')
        drawer.text((420, 120), author_name_list[0], font=author_font, fill='white')
        drawer.text((420, 120 + author_height), author_name_list[1], font=author_font, fill='white')
        drawer.text((420, 250 + author_height), uid_info, font=text_font, fill='white')
        drawer.text((420, 290 + author_height), bpm_info, font=text_font, fill='white')
        drawer.text((420, 330 + author_height), album_name, font=text_font, fill='white')


    # 向星星中加入难度数字
    star_list = [star_e, star_h, star_m, star_hid, star_hid2]
    for i in range(5):
        fontsize = difficulty_font.getbbox(difficulty_info[i])
        x = fontsize[2] - fontsize[0]
        x = star_width / 2 - x / 2
        y = 22
        if difficulty_info[i] != '0':
            star_drawer = ImageDraw.Draw(star_list[i])
            star_drawer.text((x, y), difficulty_info[i], font=difficulty_font, fill='grey')

    # 将星星加入图中
    if title_width <= 640 and author_width <= 640:
        for i in range(0, star_width):
            for j in range(0, star_height):
                x_offset = 420
                if difficulty_info[0] != '0' and star_e.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160), star_e.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[1] != '0' and star_h.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160), star_h.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[2] != '0' and star_m.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160), star_m.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[3] != '0' and star_hid.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160), star_hid.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[3] != '0' and difficulty_info[4] != '0' and star_hid2.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160), star_hid2.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[3] == '0' and difficulty_info[4] != '0' and star_hid2.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160), star_hid2.getpixel((i, j)))
                    x_offset += 100
    elif title_width > 640:
        for i in range(0, star_width):
            for j in range(0, star_height):
                x_offset = 420
                if difficulty_info[0] != '0' and star_e.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160 + title_height), star_e.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[1] != '0' and star_h.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160 + title_height), star_h.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[2] != '0' and star_m.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160 + title_height), star_m.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[3] != '0' and star_hid.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160 + title_height), star_hid.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[3] != '0' and difficulty_info[4] != '0' and star_hid2.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160 + title_height), star_hid2.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[3] == '0' and difficulty_info[4] != '0' and star_hid2.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160 + title_height), star_hid2.getpixel((i, j)))
                    x_offset += 100
    elif author_width > 640:
        for i in range(0, star_width):
            for j in range(0, star_height):
                x_offset = 420
                if difficulty_info[0] != '0' and star_e.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160 + author_height), star_e.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[1] != '0' and star_h.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160 + author_height), star_h.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[2] != '0' and star_m.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160 + author_height), star_m.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[3] != '0' and star_hid.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160 + author_height), star_hid.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[3] != '0' and difficulty_info[4] != '0' and star_hid2.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160 + author_height), star_hid2.getpixel((i, j)))
                    x_offset += 100
                if difficulty_info[3] == '0' and difficulty_info[4] != '0' and star_hid2.getpixel((i, j))[3] != 0:
                    background.putpixel((i + x_offset, j + 160 + title_height), star_hid2.getpixel((i, j)))
                    x_offset += 100

    drawer.text((200, 420), '难度', font=text_font, fill='white')
    difficulty_name = ['萌新', '高手', '大触', '里谱', '东方']
    j = 0
    for i in range(5):
        if difficulty_info[i] != '0':
            drawer.text((200, 460 + j * 50), difficulty_name[i], font=table_font, fill='white')
            j += 1

    drawer.text((400, 420), '谱师', font=text_font, fill='white')
    j = 0
    p = 0
    designer_maxlength = 0
    for i in range(5):
        if difficulty_info[i] != '0':
            drawer.text((400, 460 + j * 50), level_designer[p], font=table_font, fill='white')
            j += 1
            designer_size = table_font.getbbox(level_designer[p])
            if (designer_size[2] - designer_size[0]) > designer_maxlength:
                designer_maxlength = (designer_size[2] - designer_size[0])
        if p + 1 < len(level_designer):
            p += 1

    drawer.text((540 + designer_maxlength, 420), 'moe定数', font=text_font, fill='white')
    j = 0
    for i in range(5):
        if difficulty_info[i] != '0':
            drawer.text((540 + designer_maxlength, 460 + j * 50), diff_info[i], font=table_font, fill='white')
            j += 1

    # background.show()
    try:
        os.remove(f'./data/song_image/{uid}.png')
    except FileNotFoundError:
        pass
    background.save(f'./data/song_image/{uid}.png')

async def get_song_by_level(level):
    with open(diff_path, 'r')as f:
        diff_data = json.load(f)

    if level not in list(diff_data.keys()):
        return '您玩的是Muse Dash吗🥺?'

    message = '查找到以下曲目:'
    i = 1
    for song_info_list in diff_data[level]:
        name = song_info_list[0]
        diff = song_info_list[1][0]
        formatted_diff = '%.2f' % diff
        message += f'\n{i}.{name} ,  定数:{formatted_diff}'
        i += 1

    return message

async def score_calc(diff, accuracy):
    accuracy = float(accuracy)
    if accuracy < 0 or accuracy > 100:
        return '您玩的是Muse Dash吗🥺?'
    diff = float(diff)
    acc = accuracy / 100
    ratio = acc - (acc ** 2) + (acc ** 4)
    score = diff * ratio
    formatted_score = '%.2f' % score
    message = ''
    message += f'accuracy: {accuracy}%'
    message += f'\nscore: {diff} -> {formatted_score}'
    return message

async def get_advice(advice):
    with open(advice_path, 'r')as f:
        advice_data = json.load(f)

    advice_data.append(advice)

    with open(advice_path, 'w')as f:
        json.dump(advice_data, f, indent=4)

    return '感谢建议，已经记在小本本上了喵~'

async def get_status(qq):
    if qq not in managers:
        return '你不许看😡!'

    message = ''
    # CPU信息
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
    cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
    key.Close()
    cpu_cores = psutil.cpu_count(logical=False)
    cpu_threads = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    cpu_percent = psutil.cpu_percent()

    # 内存信息
    memory_percent = psutil.virtual_memory().percent

    # 硬盘信息
    disk_C_percent = psutil.disk_usage('C:/').percent
    disk_E_percent = psutil.disk_usage('E:/').percent

    # GPU信息
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    gpu_name = pynvml.nvmlDeviceGetName(handle)
    gpu_memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
    gpu_percent = gpu_memory.used / gpu_memory.total * 100
    gpu_percent = '%.2f' % gpu_percent
    pynvml.nvmlShutdown()

    message += f'CPU: {cpu_name}\n'
    message += f'GPU: {gpu_name}\n'
    message += f'CPU核心数: {cpu_cores}, 线程数: {cpu_threads}, 频率: {cpu_freq.current}MHz\n'
    message += f'GPU显存占用: {bytes2human(gpu_memory.used)}B / {bytes2human(gpu_memory.total)}B, 显存使用率: {gpu_percent}%\n'
    message += f'CPU使用率: {cpu_percent}%\n'
    message += f'内存使用率: {memory_percent}%\n'
    message += f'C盘使用率: {disk_C_percent}%\n'
    message += f'E盘使用率: {disk_E_percent}%'

    return message














async def md_main(qq: str, message: str):
    message_chars = message.split(' ', maxsplit=1)
    return_message = ''
    # 判断黑名单和管理员（优先判断黑名单）
    if qq in blacklist:
        return '哪凉快哪待着去!'
    if qq in managers:
        return_message  += '尊敬的管理员，'


    if len(message_chars) == 0 or message_chars[0] in ['帮助', 'help']:
        return help_message

    # 更新
    if message_chars[0] in ['更新', 'update']:
        if qq in managers:
            await update_song_info()
            return '更新完成喵~'
        else:
            return '请联系管理员更新曲库喵~'

    # 绑定
    if message_chars[0] in ['绑定', 'bind']:
        # 默认输入为uid，按照输入uid处理
        uid = message_chars[1]
        uid_success, name = await bind_uid(qq, uid)
        if uid_success:
            # 用户输入为uid，判定成功
            return return_message + f'{name}，您好，uid绑定成功喵~'
        else:
            # 用户输入为用户名
            name = message_chars[1]
            name_success, uid = await bind_name(qq, name)
            if name_success:
                return return_message + f'{name}，您好，用户名绑定成功喵~'
            else:
                return return_message + f'没搜到{name}喵~，是不是输错了/有重名，请检查一下uid或用户名喵~'

    # 解绑
    if message_chars[0] in ['解绑', '解除', '解除绑定', '删除', 'unbind']:
        success, name = await unbind(qq)
        if success:
            return return_message + f'{name}，还会再见吗(TAT)'
        else:
            return return_message + f'没找到喵~，是不是没绑定？'

    # b50
    if message_chars[0] in ['b50']:
        return return_message + '还没写，别急喵~'

    # 特权指令，查询所有已绑定玩家
    if message_chars[0] in ['查询玩家', 'all']:
        if qq in managers:
            return await show_all_players()
        else:
            return '你不许看😡!'


    if message_chars[0] in ['难度', 'diff', 'dif']:
        try:
            diff = message_chars[1]
            return return_message + (await get_song_by_level(diff))
        except IndexError:
            return '您玩的是Muse Dash吗🥺?'

    # 搜歌
    if message_chars[0] in ['查找', '搜曲', '找曲', 'song']:
        try:
            name = message_chars[1]
            await query_song_info(qq, name)
            return await get_song_info(name)
        except IndexError:
            return return_message + '请输入曲名喵~'

    if message_chars[0] in ['计算', 'acc']:
        try:
            info = message_chars[1].split(' ')
            diff = info[0]
            acc = info[1]
            return await score_calc(diff, acc)
        except IndexError:
            return '请输入完整信息喵~'


    if message_chars[0] in ['建议', 'advice']:
        return return_message + (await get_advice(message_chars[1]))
