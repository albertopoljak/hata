__all__ = ('ChannelMetadataPrivate',)


from scarletio import copy_docs

from ...permission.permission import PERMISSION_NONE, PERMISSION_PRIVATE, PERMISSION_PRIVATE_BOT

from .. import channel_types as CHANNEL_TYPES

from .private_base import ChannelMetadataPrivateBase


class ChannelMetadataPrivate(ChannelMetadataPrivateBase):
    """
    Channel metadata for private channels.
    
    Attributes
    ----------
    users : `list` of ``ClientUserBase``
        The users in the channel.
    
    Class Attributes
    ----------------
    type : `int` = `CHANNEL_TYPES.private`
        The channel's type.
    order_group: `int` = `0`
        The channel's order group used when sorting channels.
    """
    __slots__ = ()
    
    type = CHANNEL_TYPES.private
    
    @copy_docs(ChannelMetadataPrivateBase._created)
    def _created(self, channel_entity, client):
        if (client is not None):
            users = self.users
            if users:
                if client not in users:
                    users.append(client)
                
                client.private_channels[users[0].id] = channel_entity
                
                users.sort()
            
            else:
                users.append(client)
    
        
    @copy_docs(ChannelMetadataPrivateBase._delete)
    def _delete(self, channel_entity, client):
        if (client is not None):
            users = self.users
            if len(users) == 2:
                if client is users[0]:
                    user = users[1]
                else:
                    user = users[0]
                
                del client.private_channels[user.id]
    
    
    @copy_docs(ChannelMetadataPrivateBase.name)
    def name(self):
        users = self.users
        if len(users) == 2:
            name = f'Direct Message {users[0].full_name} with {users[1].full_name}'
        else:
            name = f'Direct Message (partial)'
        return name
    
    
    @copy_docs(ChannelMetadataPrivateBase._get_permissions_for)
    def _get_permissions_for(self, channel_entity, user):
        if user in self.users:
            if user.is_bot:
                return PERMISSION_PRIVATE_BOT
            else:
                return PERMISSION_PRIVATE
            
        return PERMISSION_NONE
