import vampytest

from ...permission_overwrite import PermissionOverwrite, PermissionOverwriteTargetType

from ..guild_category import ChannelMetadataGuildCategory


def assert_fields_set(channel_metadata):
    vampytest.assert_instance(channel_metadata.parent_id, int)
    vampytest.assert_instance(channel_metadata.name, str)
    vampytest.assert_instance(channel_metadata._permission_cache, dict, nullable = True)
    vampytest.assert_instance(channel_metadata.permission_overwrites, dict, nullable = True)
    vampytest.assert_instance(channel_metadata.position, int)


def test__ChannelMetadataGuildCategory__new__0():
    """
    Tests whether ``ChannelMetadataGuildCategory.__new__`` works as intended.
    
    Case: all fields given.
    """
    parent_id = 202209170029
    name = 'Armelyrics'
    permission_overwrites = [
        PermissionOverwrite(202209170030, target_type = PermissionOverwriteTargetType.user)
    ]
    position = 7
    
    keyword_parameters = {
        'parent_id': parent_id,
        'name': name,
        'permission_overwrites': permission_overwrites,
        'position': position,
    }
    channel_metadata = ChannelMetadataGuildCategory(keyword_parameters)
    
    vampytest.assert_instance(channel_metadata, ChannelMetadataGuildCategory)
    vampytest.assert_eq(keyword_parameters, {})
    
    assert_fields_set(channel_metadata)
    
    
    vampytest.assert_eq(channel_metadata.parent_id, parent_id)
    vampytest.assert_eq(channel_metadata.name, name)
    vampytest.assert_eq(
        channel_metadata.permission_overwrites,
        {permission_overwrite.target_id: permission_overwrite for permission_overwrite in permission_overwrites},
    )
    vampytest.assert_eq(channel_metadata.position, position)


def test__ChannelMetadataGuildCategory__new__1():
    """
    Tests whether ``ChannelMetadataGuildCategory.__new__`` works as intended.
    
    Case: no fields given.
    """
    keyword_parameters = {}
    
    channel_metadata = ChannelMetadataGuildCategory(keyword_parameters)
    
    vampytest.assert_instance(channel_metadata, ChannelMetadataGuildCategory)
    vampytest.assert_eq(keyword_parameters, {})
    
    assert_fields_set(channel_metadata)


def test__ChannelMetadataGuildCategory__create_empty():
    """
    Tests whether ``ChannelMetadataGuildCategory._create_empty`` works as intended.
    """
    channel_metadata = ChannelMetadataGuildCategory._create_empty()
    
    vampytest.assert_instance(channel_metadata, ChannelMetadataGuildCategory)
    
    assert_fields_set(channel_metadata)



def test__ChannelMetadataGuildCategory__precreate__0():
    """
    Tests whether ``ChannelMetadataGuildCategory.precreate`` works as intended.
    
    Case: all fields given.
    """
    parent_id = 202209170031
    name = 'Armelyrics'
    permission_overwrites = [
        PermissionOverwrite(202209170032, target_type = PermissionOverwriteTargetType.user)
    ]
    position = 7
    
    keyword_parameters = {
        'parent_id': parent_id,
        'name': name,
        'permission_overwrites': permission_overwrites,
        'position': position,
    }
    
    channel_metadata = ChannelMetadataGuildCategory.precreate(keyword_parameters)
    
    vampytest.assert_instance(channel_metadata, ChannelMetadataGuildCategory)
    vampytest.assert_eq(keyword_parameters, {})
    
    assert_fields_set(channel_metadata)
    
    vampytest.assert_eq(channel_metadata.parent_id, parent_id)
    vampytest.assert_eq(channel_metadata.name, name)
    vampytest.assert_eq(
        channel_metadata.permission_overwrites,
        {permission_overwrite.target_id: permission_overwrite for permission_overwrite in permission_overwrites},
    )
    vampytest.assert_eq(channel_metadata.position, position)


def test__ChannelMetadataGuildCategory__precreate__1():
    """
    Tests whether ``ChannelMetadataGuildCategory.precreate`` works as intended.
    
    Case: no fields given.
    """
    keyword_parameters = {}
    
    channel_metadata = ChannelMetadataGuildCategory.precreate(keyword_parameters)
    
    vampytest.assert_instance(channel_metadata, ChannelMetadataGuildCategory)
    vampytest.assert_eq(keyword_parameters, {})
    
    assert_fields_set(channel_metadata)