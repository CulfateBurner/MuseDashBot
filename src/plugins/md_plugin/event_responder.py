from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.adapters import Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.adapters.onebot.v11 import PrivateMessageEvent
from nonebot.params import CommandArg
from nonebot.rule import to_me, keyword, is_type


from .main_func import md_main, get_status
from .help import *

md = private_rule = is_type(PrivateMessageEvent)
md = on_command("md", aliases={'MD'}, priority=1, block=True)

status = on_command("status", rule=private_rule, priority=1, block=True)


@md.handle()
async def md_handle(
    matcher: Matcher,
    event: Event,
    args: Message = CommandArg()
):
    args_msg = args.extract_plain_text()
    qq = event.get_user_id()
    msg = await md_main(qq, args_msg)
    if isinstance(msg, str):
        await matcher.finish(msg)
    else:
    #     # print(song_image_path + f'{msg[0]}.png')
        await matcher.finish(MessageSegment.image(f'C:/Users/Administrator/PycharmProjects/Bot/test/data/song_image/{qq}/{msg[0]}.png'))
    #     await matcher.send(MessageSegment.image(f'C:/Users/Administrator/PycharmProjects/Bot/test/data/song_image/{msg[1]}.png'))

@status.handle()
async def status_handle(
    matcher: Matcher,
    event: Event,
):
    msg = await get_status(event.get_user_id())

    await matcher.finish(msg)