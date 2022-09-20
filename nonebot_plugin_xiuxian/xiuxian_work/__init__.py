import re
from nonebot import on_command, require, on_message
from nonebot.params import CommandArg, RawCommand, Depends, Arg, ArgStr, RegexMatched
from nonebot.adapters.onebot.v11 import (
    Bot,
    Event,
    GROUP,
    GROUP_ADMIN,
    GROUP_OWNER,
    Message,
    MessageEvent,
    GroupMessageEvent,
    MessageSegment,
)
from ..xiuxian2_handle import XiuxianDateManage, OtherSet # ,XiuxianJsonDate
from .work_handle import workhandle
from datetime import datetime
import random
from nonebot.permission import SUPERUSER
from ..xiuxian_opertion import gamebingo, do_is_work, time_msg
from ..xiuxian_config import XiuConfig
from ..data_source import jsondata

do_work = on_command("悬赏令", priority=5)

work = {}  # 悬赏令信息记录
sql_message = XiuxianDateManage()  # sql类

@do_work.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """悬赏令"""
    global work
    user_type = 2
    work_list = []
    user_id = event.get_user_id()

    text = args.extract_plain_text().strip()

    if sql_message.get_user_message(user_id) is None:
        await do_work.finish("修仙界没有道友的信息，请输入【我要修仙】加入！")

    user_cd_message = sql_message.get_user_cd(user_id)
    userinfo = sql_message.get_user_message(user_id)
    
    if "接取" in text:
        try:
            if work[user_id]:
                work_num = re.findall("\d+", text)  ##任务序号

                try:
                    get_work = work[user_id].world[int(work_num[0]) - 1]
                    sql_message.do_work(user_id, user_type, get_work[0])
                    del work[user_id]
                    await do_work.finish(f"接取任务【{get_work[0]}】成功")
                except IndexError:
                    await do_work.finish("没有这样的任务")

        except KeyError:
            await do_work.finish("没有查到你的悬赏令信息呢！")
    elif text == "结算":
        if user_cd_message is None:
            await do_work.finish("没有查到你的悬赏令信息呢！输入【悬赏令】获取！")

        elif user_cd_message.type == 0:
            await do_work.finish("没有查到你的悬赏令信息呢！输入【悬赏令】获取！")

        elif user_cd_message.type == 1:
            await do_work.finish("道友现在在闭关呢，小心走火入魔！", at_sender=True)

        elif user_cd_message.type == 2:
            work_time = datetime.strptime(
                user_cd_message.create_time, "%Y-%m-%d %H:%M:%S.%f"
            )
            exp_time = (datetime.now() - work_time).seconds // 60  # 时长计算
            time2 = workhandle().do_work(
                # key=1, name=user_cd_message.scheduled_time  修改点
                key=1, name=user_cd_message.scheduled_time, level=userinfo.level[:3], exp=userinfo.exp
            )
            if exp_time < time2:
                await do_work.finish(
                    f"进行中的悬赏令【{user_cd_message.scheduled_time}】，预计{time2 - exp_time}分钟后可结束",
                    at_sender=True,
                )
            else:
                work_sf = workhandle().do_work(2, work_list= user_cd_message.scheduled_time, level=userinfo.level[:3], exp=userinfo.exp)
                if work_sf[3]: #大成功
                    sql_message.update_ls(user_id, work_sf[1] * 2, 1)
                    sql_message.do_work(user_id, 0)
                    #todu 战利品结算sql
                    await do_work.finish(f"悬赏令结算，{work_sf[0]},最终获得报酬{work_sf[1] * 2}枚灵石,额外获得战利品{work_sf[2]}!")
                    
                else: #普通结算
                    sql_message.update_ls(user_id, work_sf[1], 1)
                    sql_message.do_work(user_id, 0)
                    await do_work.finish(f"悬赏令结算，{work_sf[0]},最终获得报酬{work_sf[1]}枚灵石！")
                    

    try:
        if work[user_id]:
            if (datetime.now() - work[user_id].time).seconds // 60 >= 60:
                work_msg = workhandle().do_work(0, level=userinfo.level[:3], exp=userinfo.exp)

                n = 1
                work_msg_f = f"""     ✨道友的个人悬赏令✨"""
                for i in work_msg:
                    work_list.append([i[0], i[3]])
                    work_msg_f += f"""
{n}、{i[0]}     完成机率{i[1]}   基础报酬{i[2]}灵石   预计需{i[3]}分钟   可能获取额外战利品{''.join(sp + ' ' for sp in i[4])}"""
                    n += 1
                work_msg_f += "\n(悬赏令每小时更新一次)"
                work[user_id].msg = work_msg_f
                work[user_id].world = work_list
                await do_work.finish(work[user_id].msg)
            else:
                await do_work.finish(work[user_id].msg)
    except KeyError:
        pass

    if user_cd_message is None:
        work_msg = workhandle().do_work(0, level=userinfo.level[:3], exp=userinfo.exp)
        n = 1
        work_msg_f = f"""     ✨道友的个人悬赏令✨"""
        for i in work_msg:
            work_list.append([i[0], i[3]])
            work_msg_f += f"""
{n}、{i[0]}     完成机率{i[1]}   基础报酬{i[2]}灵石   预计需{i[3]}分钟   可能获取额外战利品{''.join(sp + ' ' for sp in i[4])}"""
            n += 1
        work_msg_f += f"\n(悬赏令每小时更新一次)"
        work[user_id] = do_is_work(user_id)
        work[user_id].time = datetime.now()
        work[user_id].msg = work_msg_f
        work[user_id].world = work_list
        await do_work.finish(work_msg_f)

    elif user_cd_message.type == 0:

        work_msg = workhandle().do_work(0, level=userinfo.level[:3], exp=userinfo.exp)
        work_msg_f = f"""     ✨道友的个人悬赏令✨"""
        n = 1
        for i in work_msg:
            work_list.append([i[0], i[3]])
            work_msg_f += f"""
{n}、{i[0]}     完成机率{i[1]}   基础报酬{i[2]}灵石   预计需{i[3]}分钟   可能获取额外战利品{''.join(sp + ' ' for sp in i[4])}"""
            n += 1
        work_msg_f += f"\n(榜单每小时更新一次)"
        work[user_id] = do_is_work(user_id)
        work[user_id].time = datetime.now()
        work[user_id].msg = work_msg_f
        work[user_id].world = work_list
        await do_work.finish(work_msg_f)

    elif user_cd_message.type == 1:
        await do_work.finish("已经在闭关中，请输入【出关】结束后才能获取悬赏令！", at_sender=True)

    elif user_cd_message.type == 2:
        work_time = datetime.strptime(
            user_cd_message.create_time, "%Y-%m-%d %H:%M:%S.%f"
        )
        exp_time = (datetime.now() - work_time).seconds // 60  # 闭关时长计算
        time2 = workhandle().do_work(key=1, name=user_cd_message.scheduled_time)
        if exp_time < time2:
            await do_work.finish(
                f"进行中的悬赏令【{user_cd_message.scheduled_time}】，预计{time2 - exp_time}分钟后可结束",
                at_sender=True,
            )
        else:
            await do_work.finish(
                f"进行中的悬赏令【{user_cd_message.scheduled_time}】，已结束，请输入【悬赏令结算】结算任务信息！",
                at_sender=True,
            )
            
class MsgError(ValueError):
    pass
