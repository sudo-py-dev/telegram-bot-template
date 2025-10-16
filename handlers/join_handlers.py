from pyrogram.types import ChatMemberUpdated, ChatJoinRequest
from pyrogram.handlers import ChatMemberUpdatedHandler, ChatJoinRequestHandler
from pyrogram import filters
from database.database import AdminsPermissions
from tools.tools import BotSettings, Chats
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import ChannelPrivate, RPCError
from pyrogram.enums import ChatType


async def handle_bot_membership_update(member: ChatMemberUpdated) -> None:
    """Handle bot membership updates (join/leave/admin) in groups or channels."""
    if not member.new_chat_member.user.is_self:
        return
    settings = await BotSettings.get_settings()
    chat = member.chat
    new_status = member.new_chat_member.status
    is_group = chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    is_channel = chat.type == ChatType.CHANNEL

    # Check if bot allowed to stay
    if (is_group and not settings.can_join_group) or (is_channel and not settings.can_join_channel):  
        try:
            await chat.leave()
        except (RPCError, ChannelPrivate):
            pass
        can_stay = False
    else:
        can_stay = True

    is_admin = new_status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}
    is_active = new_status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER, ChatMemberStatus.MEMBER}

    await Chats.chat_status_change(
        chat_id=chat.id,
        chat_title=chat.title,
        chat_type=chat.type.value,
        is_active=is_active and can_stay,
        is_admin=is_admin and can_stay,
    )


async def handle_admin_update(member: ChatMemberUpdated) -> None:
    """Handle admin updates (join/leave/admin) in groups or channels."""
    chat = member.chat.id
    user_id = member.new_chat_member.user.id
    if member.new_chat_member and member.new_chat_member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
        await AdminsPermissions.update_admin(chat_id=chat, admin_id=user_id, privileges=member.new_chat_member.privileges)
    elif member.old_chat_member and member.old_chat_member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER} and member.new_chat_member and member.new_chat_member.status in {ChatMemberStatus.MEMBER, ChatMemberStatus.BANNED, ChatMemberStatus.LEFT}:
        await AdminsPermissions.delete_admin(chat_id=chat, admin_id=user_id)
    
        
async def group_join_handler(_, member: ChatMemberUpdated):
    if member.new_chat_member.user.is_self:
        await handle_bot_membership_update(member)
    elif member.new_chat_member and member.new_chat_member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER} or member.old_chat_member and member.old_chat_member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
        await handle_admin_update(member)


async def channel_join_handler(_, member: ChatMemberUpdated):
    if member.new_chat_member.user.is_self:
        await handle_bot_membership_update(member)
    elif member.new_chat_member and member.new_chat_member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER} or member.old_chat_member and member.old_chat_member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
        await handle_admin_update(member)


async def group_join_request_handler(_, request: ChatJoinRequest):
    # add implementation
    pass


async def channel_join_request_handler(_, request: ChatJoinRequest):
    # add implementation
    pass


join_handlers = [
    ChatMemberUpdatedHandler(group_join_handler, filters.group),
    ChatJoinRequestHandler(group_join_request_handler, filters.group),
    ChatMemberUpdatedHandler(channel_join_handler, filters.channel),
    ChatJoinRequestHandler(channel_join_request_handler, filters.channel)
]
