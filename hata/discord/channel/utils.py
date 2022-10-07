__all__ = ('cr_pg_channel_object', 'create_partial_channel_from_data', 'create_partial_channel_from_id')

import reprlib
from functools import partial as partial_func

from scarletio import export, include

from ..core import CHANNELS

from .channel_type import ChannelType
from .fields.applied_tag_ids import validate_applied_tag_ids, put_applied_tag_ids_into
from .fields.auto_archive_after import validate_auto_archive_after, put_auto_archive_after_into
from .fields.bitrate import validate_bitrate, put_bitrate_into
from .fields.default_thread_auto_archive_after import (
    validate_default_thread_auto_archive_after, put_default_thread_auto_archive_after_into
)
from .fields.default_thread_reaction import validate_default_thread_reaction, put_default_thread_reaction_into
from .fields.default_thread_slowmode import validate_default_thread_slowmode, put_default_thread_slowmode_into
from .fields.flags import validate_flags, put_flags_into
from .fields.invitable import validate_invitable, put_invitable_into
from .fields.name import validate_name, put_name_into
from .fields.nsfw import validate_nsfw, put_nsfw_into
from .fields.open_ import validate_open, put_open_into
from .fields.parent_id import validate_parent_id, put_parent_id_into
from .fields.permission_overwrites import validate_permission_overwrites, put_permission_overwrites_into
from .fields.position import validate_position, put_position_into
from .fields.region import validate_region, put_region_into
from .fields.slowmode import validate_slowmode, put_slowmode_into
from .fields.topic import validate_topic, put_topic_into
from .fields.user_limit import validate_user_limit, put_user_limit_into
from .fields.video_quality_mode import validate_video_quality_mode, put_video_quality_mode_into
from .metadata.base import CHANNEL_METADATA_ICON_SLOT


Channel = include('Channel')


CHANNEL_GUILD_MAIN_FIELD_CONVERTERS = {
    'bitrate': (validate_bitrate, put_bitrate_into),
    'default_thread_auto_archive_after': (
        validate_default_thread_auto_archive_after, put_default_thread_auto_archive_after_into
    ),
    'default_thread_reaction': (validate_default_thread_reaction, put_default_thread_reaction_into),
    'default_thread_slowmode': (validate_default_thread_slowmode, put_default_thread_slowmode_into),
    'flags': (validate_flags, put_flags_into),
    'name': (validate_name, put_name_into),
    'nsfw': (validate_nsfw, put_nsfw_into),
    'parent_id': (validate_parent_id, put_parent_id_into),
    'permission_overwrites': (validate_permission_overwrites, put_permission_overwrites_into),
    'position': (validate_position, put_position_into),
    'region': (validate_region, put_region_into),
    'slowmode': (validate_slowmode, put_slowmode_into),
    'topic': (validate_topic, put_topic_into),
    'user_limit': (validate_user_limit, put_user_limit_into),
    'video_quality_mode': (validate_video_quality_mode, put_video_quality_mode_into),
}


CHANNEL_PRIVATE_GROUP_FIELD_CONVERTERS = {
    'icon': (
        CHANNEL_METADATA_ICON_SLOT.validate_data_icon,
        partial_func(CHANNEL_METADATA_ICON_SLOT.put_into, as_data = True),
    ),
    'name': (validate_name, put_name_into),
}


CHANNEL_GUILD_THREAD_FIELD_CONVERTERS = {
    'applied_tag_ids': (validate_applied_tag_ids, put_applied_tag_ids_into),
    'auto_archive_after': (
        validate_auto_archive_after, partial_func(put_auto_archive_after_into, flatten_thread_metadata = True)
    ),
    'flags': (validate_flags, put_flags_into),
    'invitable': (validate_invitable, partial_func(put_invitable_into, flatten_thread_metadata = True)),
    'name': (validate_name, put_name_into),
    'open_': (validate_open, partial_func(put_open_into, flatten_thread_metadata = True)),
    'slowmode': (validate_slowmode, put_slowmode_into),
}


CHANNEL_GUILD_FIELD_CONVERTERS = {
    **CHANNEL_GUILD_THREAD_FIELD_CONVERTERS,
    **CHANNEL_GUILD_MAIN_FIELD_CONVERTERS,
}


def create_partial_channel_from_data(data, guild_id):
    """
    Creates a partial channel from partial channel data.
    
    Parameters
    ----------
    data : `None`, `dict` of (`str`, `Any`) items
        Partial channel data received from Discord.
    guild_id : `int`
        The channel's guild's identifier.
    
    Returns
    -------
    channel : `None`, ``Channel``
        The created partial channel, or `None`, if no data was received.
    """
    if (data is None) or (not data):
        return None
    
    channel_id = int(data['id'])
    try:
        return CHANNELS[channel_id]
    except KeyError:
        pass
    
    channel = Channel._from_partial_data(data, channel_id, guild_id)
    CHANNELS[channel_id] = channel
    
    return channel


@export
def create_partial_channel_from_id(channel_id, channel_type, guild_id):
    """
    Creates a new partial channel from the given identifier.
    
    Parameters
    ----------
    channel_id : `int`
        The channel's identifier.
    channel_type : ``ChannelType``
        The channel's type.
    guild_id : `int`
        A guild's identifier of the created channel.
    """
    try:
        return CHANNELS[channel_id]
    except KeyError:
        pass
    
    channel = Channel._create_empty(channel_id, channel_type, guild_id)
    CHANNELS[channel_id] = channel
    
    return channel


HAS_SLOWMODE = (
    *(
        channel_type for channel_type in ChannelType.INSTANCES.values()
        if channel_type.flags.guild and channel_type.flags.textual
    ),
    ChannelType.guild_forum,
)



def cr_pg_channel_object(name, channel_type, *, guild = None, **keyword_parameters):
    """
    Deprecated, please use `Channel(..).to_data(...)` instead.
    
    Will be removed in 2023 February.
    """
    return Channel(channel_type = channel_type, name = name, **keyword_parameters).to_data()
