__all__ = (
    'API_ENDPOINT', 'CDN_ENDPOINT', 'DISCORD_ENDPOINT', 'INVITE_URL_RP', 'STATUS_ENDPOINT', 'VALID_ICON_FORMATS',
    'VALID_ICON_FORMATS_EXTENDED', 'VALID_ICON_MEDIA_TYPES', 'VALID_ICON_MEDIA_TYPES_EXTENDED',
    'VALID_IMAGE_MEDIA_TYPES_ALL', 'VALID_STICKER_IMAGE_MEDIA_TYPES', 'is_media_url', 'parse_message_jump_url'
)

import re

from scarletio import export, include

from ...env import (
    API_VERSION, CUSTOM_API_ENDPOINT, CUSTOM_CDN_ENDPOINT, CUSTOM_DISCORD_ENDPOINT, CUSTOM_INVITE_ENDPOINT,
    CUSTOM_MEDIA_ENDPOINT, CUSTOM_STATUS_ENDPOINT
)


StickerFormat = include('StickerFormat')
_try_get_guild_id = include('_try_get_guild_id')


API_ENDPOINT = f'https://discord.com/api/v{API_VERSION}' if (CUSTOM_API_ENDPOINT is None) else CUSTOM_API_ENDPOINT
CDN_ENDPOINT = 'https://cdn.discordapp.com' if (CUSTOM_CDN_ENDPOINT is None) else CUSTOM_CDN_ENDPOINT
DISCORD_ENDPOINT = 'https://discord.com' if (CUSTOM_DISCORD_ENDPOINT is None) else CUSTOM_DISCORD_ENDPOINT
STATUS_ENDPOINT = 'https://status.discord.com/api/v2' if (CUSTOM_STATUS_ENDPOINT is None) else CUSTOM_STATUS_ENDPOINT
MEDIA_ENDPOINT =  'https://media.discordapp.net' if (CUSTOM_MEDIA_ENDPOINT is None) else CUSTOM_MEDIA_ENDPOINT
INVITE_ENDPOINT = 'https://discord.gg' if (CUSTOM_INVITE_ENDPOINT is None) else CUSTOM_INVITE_ENDPOINT

del CUSTOM_API_ENDPOINT, CUSTOM_CDN_ENDPOINT, CUSTOM_DISCORD_ENDPOINT, CUSTOM_STATUS_ENDPOINT, API_VERSION

VALID_ICON_SIZES = frozenset((
    *( 1 << x      for x in range(4, 13)),
    *((1 << x) * 3 for x in range(9, 11)),
    *((1 << x) * 5 for x in range(2,  9)),
))

VALID_ICON_FORMATS = frozenset(('jpg', 'jpeg', 'png', 'webp'))
VALID_ICON_FORMATS_EXTENDED = frozenset((*VALID_ICON_FORMATS, 'gif',))

VALID_ICON_MEDIA_TYPES = frozenset(('image/jpeg', 'image/png', 'image/webp'))
VALID_ICON_MEDIA_TYPES_EXTENDED = frozenset(('image/gif', *VALID_ICON_MEDIA_TYPES))

VALID_STICKER_IMAGE_MEDIA_TYPES = frozenset(('image/gif', 'image/png', 'application/json'))
VALID_IMAGE_MEDIA_TYPES_ALL = frozenset((*VALID_ICON_MEDIA_TYPES_EXTENDED, *VALID_STICKER_IMAGE_MEDIA_TYPES))


WIDGET_STYLE_RP = re.compile('shield|banner[1-4]')

MESSAGE_JUMP_URL_RP = re.compile(
    '(?:https://)?(?:(?:canary|ptb)\\.)?discord(?:app)?.com/channels/(?:(\\d{7,21})|@me)/(\\d{7,21})/(\\d{7,21})'
)
export(MESSAGE_JUMP_URL_RP, 'MESSAGE_JUMP_URL_RP')


def _validate_extension(icon_type, ext):
    """
    Validates the given icon extension.
    
    Parameters
    ----------
    icon_type : ``IconType``
        The respective icon type.
    ext : `None | str`
        The received extension.
    
    Returns
    -------
    ext : `str`
        The validated extension.
    
    Raises
    ------
    ValueError
        - If `ext`'s value is not applicable for the given icon type.
    """
    if ext is None:
        ext = icon_type.default_postfix
    
    else:
        if not icon_type.allows_postfix(ext):
            raise ValueError(
                f'Extension must be one of {ext.allowed_postfixes}, got {ext!r}.'
            )
    
    return ext


def _build_end(size):
    """
    Validates the given icon size.
    
    Parameters
    ----------
    size : `None | int`
        The received size.
    
    Returns
    -------
    end : `str`
        The validated size as query string.
    
    Raises
    ------
    ValueError
        - If `size`'s value is not applicable for the given icon type.
    """
    if size is None:
        end = ''
    
    elif size in VALID_ICON_SIZES:
        end = f'?size={size}'
    
    else:
        raise ValueError(
            f'Size must be in {sorted(VALID_ICON_SIZES)!r}, got {size!r}.'
        )
    
    return end


# returns a URL that allows the client to jump to this message
# guild is guild's id, or @me if there is no guild
def message_jump_url(message):
    """
    Returns a jump url to the message. If the message's channel is a partial guild channel, returns `None`.
    
    This function is a shared property of ``Message``-s.
    
    Returns
    -------
    url : `str`
    """
    channel_id = message.channel_id
    guild_id = message.guild_id
    if guild_id:
        guild_id = str(guild_id)
    else:
        guild_id = '@me'
    
    return f'{DISCORD_ENDPOINT}/channels/{guild_id}/{channel_id}/{message.id}'


def parse_message_jump_url(message_url):
    """
    Parses the jump url of a message. On failure returns `0`-s.
    
    Parameters
    ----------
    message_url : `str`
        The message url to parse.
    
    Returns
    -------
    guild_id : `int`
        The message's guild's identifier. Defaults to `0` if the message is from a private channel.
    channel_id : `int`
        The message's channel's identifier.
    message_id : `int`
        The message's identifier.
    """
    parsed = MESSAGE_JUMP_URL_RP.fullmatch(message_url)
    if parsed is None:
        guild_id = 0
        channel_id = 0
        message_id = 0
    else:
        guild_id, channel_id, message_id = parsed.groups()
        if guild_id is None:
            guild_id = 0
        else:
            guild_id = int(guild_id)
        channel_id = int(channel_id)
        message_id = int(message_id)
    
    return guild_id, channel_id, message_id


CDN_RP = re.compile(
    'https://(?:'
        'cdn\\.discordapp\\.com|'
        '(?:(?:canary|ptb)\\.)?discord\\.com|'
        '(?:'
            'images-ext-\\d+|'
            'media'
        ')\\.discordapp\\.net'
    ')/'
)

def is_cdn_url(url):
    """
    Returns whether the given url a Discord content delivery network url.
    
    Parameters
    ----------
    url : `str`
        The url to check.
    
    Returns
    -------
    is_cdn_url : `bool`
    
    Examples
    --------
    Icons: `https://cdn.discordapp.com/...`
    Assets: `https://discord.com/...`
    Proxy service: `https://images-ext-1.discordapp.net/...`
    Attachments: `https://media.discordapp.net/...`
    ```
    """
    return (CDN_RP.match(url) is not None)


def is_media_url(url):
    """
    Returns whether the given url uses the discord's media content delivery network.
    
    Parameters
    ----------
    url : `str`
        The url to check.
    
    Returns
    -------
    is_media_url : `bool`
    """
    return url.startswith('https://media.discordapp.net/')


def guild_icon_url(guild):
    """
    Returns the guild's icon's image's url. If the guild has no icon, then returns `None`.
    
    This function is a shared property of ``Guild``, ``GuildPreview``.
    
    Returns
    -------
    url : `None | str`
    """
    icon_type = guild.icon_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/icons/{guild.id}/{prefix}{guild.icon_hash:0>32x}.{ext}'


def guild_icon_url_as(guild, ext = None, size = None):
    """
    Returns the guild's icon's url. If the guild has no icon, then returns `None`.
    
    This function is a shared method of ``Guild``, ``GuildPreview``.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`. If the guild has
        animated icon, it can `'gif'` as well.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon_type = guild.icon_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/icons/{guild.id}/{prefix}{guild.icon_hash:0>32x}.{ext}{end}'


def guild_invite_splash_url(guild):
    """
    Returns the guild's invite splash's image's url. If the guild has no invite splash, then returns `None`.
    
    This function is a shared property of ``Guild``, ``GuildPreview``.
    
    Returns
    -------
    url : `None | str`
    """
    icon_type = guild.invite_splash_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/splashes/{guild.id}/{prefix}{guild.invite_splash_hash:0>32x}.{ext}'


def guild_invite_splash_url_as(guild, ext = None, size = None):
    """
    Returns the guild's invite splash's image's url. If the guild has no invite splash, then returns `None`.
    
    This function is a shared method of ``Guild``, ``GuildPreview``.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon_type = guild.invite_splash_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/splashes/{guild.id}/{prefix}{guild.invite_splash_hash:0>32x}.{ext}{end}'


def guild_discovery_splash_url(guild):
    """
    Returns the guild's discovery splash's image's url. If the guild has no discovery splash, then returns `None`.
    
    This function is a shared property of ``Guild``-s.
    
    Returns
    -------
    url : `None | str`
    """
    icon_type = guild.discovery_splash_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/discovery-splashes/{guild.id}/{prefix}{guild.discovery_splash_hash:0>32x}.{ext}'


def guild_discovery_splash_url_as(guild, ext = None, size = None):
    """
    Returns the guild's discovery splash's image's url. If the guild has no discovery splash, then returns `None`.
    
    This function is a shared method of ``Guild``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon_type = guild.discovery_splash_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/discovery-splashes/{guild.id}/{prefix}{guild.discovery_splash_hash:0>32x}.{ext}{end}'


def guild_banner_url(guild):
    """
    Returns the guild's banner's image's url. If the guild has no banner, then returns `None`.
    
    This function is a shared property of ``Guild``-s.
    
    Returns
    -------
    url : `None | str`
    """
    icon_type = guild.banner_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/banners/{guild.id}/{prefix}{guild.banner_hash:0>32x}.{ext}'


def guild_banner_url_as(guild, ext = None, size = None):
    """
    Returns the guild's banner's image's url. If the guild has no banner, then returns `None`.
    
    This function is a shared method of ``Guild``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`, `'gif'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon_type = guild.banner_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/banners/{guild.id}/{prefix}{guild.banner_hash:0>32x}.{ext}{end}'


def guild_widget_url(guild):
    """
    Returns the guild's widget image's url in `.png` format.
    
    This function is a shared property of ``Guild``-s.
    
    Returns
    -------
    url : `str`
    """
    return f'{API_ENDPOINT}/guilds/{guild.id}/widget.png?style=shield'


def guild_widget_url_as(guild, style = 'shield'):
    """
    Returns the guild's widget image's url in `.png` format.
    
    This function is a shared method of ``Guild``-s.
    
    Parameters
    ----------
    style : `str` = `'shield'`, Optional
        The widget image's style. Can be any of: `'shield'`, `'banner1'`, `'banner2'`, `'banner3'`, `'banner4'`.
    
    Returns
    -------
    url : `str`
    
    Raises
    ------
    ValueError
        If `style` was not passed as any of the expected values.
    """
    if WIDGET_STYLE_RP.fullmatch(style) is None:
        raise ValueError(f'Invalid style: {style!r}')
    
    return f'{API_ENDPOINT}/guilds/{guild.id}/widget.png?style={style}'


def guild_widget_json_url(guild):
    """
    Returns an url to request a ``Guild``'s widget data.
    
    This function is a shared property of ``Guild``, ``GuildWidget``.
    
    Returns
    -------
    url : `str`
    """
    return  f'{API_ENDPOINT}/guilds/{guild.id}/widget.json'


def guild_home_splash_url(guild):
    """
    Returns the guild's home splash's image's url. If the guild has no home splash, then returns `None`.
    
    This function is a shared property of ``Guild``-s.
    
    Returns
    -------
    url : `None | str`
    """
    icon_type = guild.home_splash_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/home-headers/{guild.id}/{prefix}{guild.home_splash_hash:0>32x}.{ext}'


def guild_home_splash_url_as(guild, ext = None, size = None):
    """
    Returns the guild's home splash's image's url. If the guild has no home splash, then returns `None`.
    
    This function is a shared method of ``Guild``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
    
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon_type = guild.home_splash_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/home-headers/{guild.id}/{prefix}{guild.home_splash_hash:0>32x}.{ext}{end}'


def channel_group_icon_url(channel):
    """
    Returns the group channel's icon's image's url. If the channel has no icon, then returns `None`.
    
    This function is a shared property of ``Channel``-s.
    
    Returns
    -------
    url : `None | str`
    """
    icon = channel.icon
    icon_type = icon.type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/channel-icons/{channel.id}/{prefix}{icon.hash:0>32x}.{ext}'
    
    
def channel_group_icon_url_as(channel, ext = None, size = None):
    """
    Returns the group channel's icon's image's url. If the channel has no icon, then returns `None`.
    
    This function is a shared method of ``Channel``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon = channel.icon
    icon_type = icon.type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/channel-icons/{channel.id}/{prefix}{icon.hash:0>32x}.{ext}{end}'


def emoji_url(emoji):
    """
    Returns the emoji's image's url. If the emoji is unicode emoji, then returns `None` instead.
    
    This function is a shared property of ``Emoji``-s.
    
    Returns
    -------
    url : `None | str`
    """
    if not emoji.is_custom_emoji():
        return None
    
    if emoji.animated:
         ext = 'gif'
    else:
         ext = 'png'
    
    return f'{CDN_ENDPOINT}/emojis/{emoji.id}.{ext}'


def emoji_url_as(emoji, ext = None, size = None):
    """
    Returns the emoji's image's url. If the emoji is unicode emoji, then returns `None` instead.
    
    This function is a shared method of ``Emoji``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`. If emoji is
        animated, it can `'gif'` as well.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    if not emoji.is_custom_emoji():
        return None
    
    if ext is None:
        if emoji.animated:
            ext = 'gif'
        else:
            ext = 'png'
    else:
        if emoji.animated:
            if ext not in VALID_ICON_FORMATS_EXTENDED:
                raise ValueError(
                    f'Extension must be one of {VALID_ICON_FORMATS_EXTENDED}, got {ext!r}.'
                )
        else:
            if ext not in VALID_ICON_FORMATS:
                raise ValueError(
                    f'Extension must be one of {VALID_ICON_FORMATS}, got {ext!r}.'
                )
    
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/emojis/{emoji.id}.{ext}{end}'


def webhook_url(webhook):
    """
    Returns the webhook's url.
    
    This function is a shared property of ``Webhook``-s.
    
    Returns
    -------
    url : `str`
    """
    return f'{API_ENDPOINT}/webhooks/{webhook.id}/{webhook.token}'


WEBHOOK_URL_PATTERN = re.compile(
    '(?:https://)?discord(?:app)?.com/api/(?:v\\d+/)?webhooks/([0-9]{17,21})/([a-zA-Z0-9.\\-_%]{60,68})(?:/.*)?'
)


def invite_url(invite):
    """
    Returns the invite's url.
    
    This function is a shared property of ``Invite``-s.
    
    Returns
    -------
    url : `str`
    """
    return f'{INVITE_ENDPOINT}/{invite.code}'


def guild_vanity_invite_url(guild):
    """
    Returns the guild vanity invite's url.
    
    This function is a shared property of ``Guild``-s.
    
    Returns
    -------
    url : `None | str`
    """
    vanity_code = guild.vanity_code
    if (vanity_code is not None):
        return f'{INVITE_ENDPOINT}/{vanity_code}'


INVITE_URL_RP = re.compile('(?:https?://)?discord(?:\\.gg|(?:app)?\\.com/invite)/([a-zA-Z0-9-]+)')


def activity_asset_image_large_url(activity):
    """
    Returns the activity's large asset image's url. If the activity has no large asset image, then returns `None`.
    
    This function is a shared property of ``Activity``-s.
    
    Returns
    -------
    url : `None | str`
    """
    application_id = activity.application_id
    if not application_id:
        return None
    
    assets = activity.assets
    if assets is None:
        return None
    
    image_large = assets.image_large
    if image_large is None:
        return None
    
    if not image_large.isdigit():
        return None
    
    return f'{CDN_ENDPOINT}/app-assets/{application_id}/{image_large}.png'


def activity_asset_image_large_url_as(activity, ext = None, size = None):
    """
    Returns the activity's large asset image's url. If the activity has no large asset image, then returns `None`.
    
    This function is a shared method of ``Activity``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    application_id = activity.application_id
    if not application_id:
        return None

    assets = activity.assets
    if assets is None:
        return None
    
    image_large = assets.image_large
    if image_large is None:
        return None
    
    if not image_large.isdigit():
        return None
    
    if size is None:
        end = ''
    elif size in VALID_ICON_SIZES:
        end = f'?size={size}'
    else:
        raise ValueError(f'Size must be in {sorted(VALID_ICON_SIZES)!r}, got {size!r}.')

    if ext is None:
        ext = 'png'
    elif ext not in VALID_ICON_FORMATS:
        raise ValueError(f'Extension must be one of {VALID_ICON_FORMATS}, got {ext!r}.')
    
    return f'{CDN_ENDPOINT}/app-assets/{application_id}/{image_large}.{ext}{end}'


def activity_asset_image_small_url(activity):
    """
    Returns the activity's small asset image's url. If the activity has no small asset image, then returns `None`.
    
    This function is a shared property of ``Activity``-s.
    
    Returns
    -------
    url : `None | str`
    """
    application_id = activity.application_id
    if not application_id:
        return None
    
    assets = activity.assets
    if assets is None:
        return None
    
    image_small = assets.image_small
    if image_small is None:
        return None
    
    if not image_small.isdigit():
        return None
    
    return f'{CDN_ENDPOINT}/app-assets/{application_id}/{image_small}.png'


def activity_asset_image_small_url_as(activity, ext = None, size = None):
    """
    Returns the activity's small asset image's url. If the activity has no small asset image, then returns `None`.
    
    This function is a shared method of ``Activity``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    application_id = activity.application_id
    if not application_id:
        return None
    
    assets = activity.assets
    if assets is None:
        return None
    
    image_small = assets.image_small
    if image_small is None:
        return None
    
    if not image_small.isdigit():
        return None
    
    if size is None:
        end = ''
    elif size in VALID_ICON_SIZES:
        end = f'?size={size}'
    else:
        raise ValueError(f'Size must be in {sorted(VALID_ICON_SIZES)!r}, got {size!r}.')
    
    if ext is None:
        ext = 'png'
    elif ext not in VALID_ICON_FORMATS:
        raise ValueError(f'Extension must be one of {VALID_ICON_FORMATS}, got {ext!r}.')
    
    return f'{CDN_ENDPOINT}/app-assets/{application_id}/{image_small}.{ext}{end}'


def user_banner_url(user):
    """
    Returns the user's banner's url. If the user has no banner, then returns `None`.
    
    This function is a shared property of ``UserBase``-s.
    
    Returns
    -------
    url : `None | str`
    """
    icon_type = user.banner_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/banners/{user.id}/{prefix}{user.banner_hash:0>32x}.{ext}'


def user_banner_url_as(user, ext = None, size = None):
    """
    Returns the user's banner's url. If the user has no banner, then returns `None`.
    
    This function is a shared method of ``UserBase``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`. If the user has
        animated banner, it can `'gif'` as well.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the avatar's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon_type = user.banner_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/banners/{user.id}/{prefix}{user.banner_hash:0>32x}.{ext}{end}'


def user_banner_url_for(user, guild):
    """
    Returns the user's guild specific banner. If the user has no guild local banner, returns `None`.
    
    This function is a shared method of ``UserBase``-s.
    
    Parameters
    ----------
    guild : ``int | Guild``
        The respective guild or it's identifier.
    
    Returns
    -------
    url : `None | str`
    """
    guild_id = _try_get_guild_id(guild)
    
    try:
        guild_profile = user.guild_profiles[guild_id]
    except KeyError:
        return None
    
    icon_type = guild_profile.banner_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/guilds/{guild_id}/users/{user.id}/banners/{prefix}{guild_profile.banner_hash:0>32x}.{ext}'


def user_banner_url_for_as(user, guild, ext = None, size = None):
    """
    Returns the user's guild specific banner. If the user has no guild local banner, then returns `None`.
    
    This function is a shared method of ``UserBase``-s.
    
    Parameters
    ----------
    guild : ``int | Guild``
        The respective guild or it's identifier.
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'` and `'gif'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the banner's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    guild_id = _try_get_guild_id(guild)
    
    try:
        guild_profile = user.guild_profiles[guild_id]
    except KeyError:
        return None
    
    icon_type = guild_profile.banner_type
    if not icon_type.can_create_url():
        return None

    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return (
        f'{CDN_ENDPOINT}/guilds/{guild_id}/users/{user.id}/banners/{prefix}{guild_profile.banner_hash:0>32x}.{ext}{end}'
    )


def user_banner_url_at(user, guild):
    """
    Returns the user's banner's url at the guild.
    
    This function is a shared method of ``UserBase``-s.
    
    Parameters
    ----------
    guild : ``int | Guild``
        The respective guild or it's identifier.
    
    Returns
    -------
    url : `None | str`
    """
    banner_url = user_banner_url_for(user, guild)
    if banner_url is None:
        banner_url = user_banner_url(user)
    
    return banner_url


def user_banner_url_at_as(user, guild, ext = None, size = None):
    """
    Returns the user's banner's url at the guild. If the user has no banner, then returns it's default banner's url.
    
    This function is a shared method of ``UserBase``-s.
    
    Parameters
    ----------
    guild : ``int | Guild``
        The respective guild or it's identifier.
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'` and `'gif'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the banner's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    banner_url = user_banner_url_for_as(user, guild, ext = ext, size = size)
    if banner_url is None:
        banner_url = user_banner_url_as(user, ext = ext, size = size)
    
    return banner_url


def user_avatar_url(user):
    """
    Returns the user's avatar's url. If the user has no avatar, then returns it's default avatar's url.
    
    This function is a shared property of ``UserBase``-s.
    
    Returns
    -------
    url : `None | str`
    """
    icon_type = user.avatar_type
    if not icon_type.can_create_url():
        return user.default_avatar.url
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/avatars/{user.id}/{prefix}{user.avatar_hash:0>32x}.{ext}'


def user_avatar_url_as(user, ext = None, size = None):
    """
    Returns the user's avatar's url. If the user has no avatar, then returns it's default avatar's url.
    
    This function is a shared method of ``UserBase``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`. If the user has
        animated avatar, it can `'gif'` as well.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the avatar's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon_type = user.avatar_type
    if not icon_type.can_create_url():
        return user.default_avatar.url
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/avatars/{user.id}/{prefix}{user.avatar_hash:0>32x}.{ext}{end}'


def user_avatar_url_for(user, guild):
    """
    Returns the user's guild specific avatar. If the user has no guild local avatar, returns `None`.
    
    This function is a shared method of ``UserBase``-s.
    
    Parameters
    ----------
    guild : ``int | Guild``
        The respective guild or it's identifier.
    
    Returns
    -------
    url : `None | str`
    """
    guild_id = _try_get_guild_id(guild)
    
    try:
        guild_profile = user.guild_profiles[guild_id]
    except KeyError:
        return None
    
    icon_type = guild_profile.avatar_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/guilds/{guild_id}/users/{user.id}/avatars/{prefix}{guild_profile.avatar_hash:0>32x}.{ext}'


def user_avatar_url_for_as(user, guild, ext = None, size = None):
    """
    Returns the user's guild specific avatar. If the user has no guild local avatar, then returns `None`.
    
    This function is a shared method of ``UserBase``-s.
    
    Parameters
    ----------
    guild : ``int | Guild``
        The respective guild or it's identifier.
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`. If the user has
        animated avatar, it can `'gif'` as well.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the avatar's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    guild_id = _try_get_guild_id(guild)
    
    try:
        guild_profile = user.guild_profiles[guild_id]
    except KeyError:
        return None
    
    icon_type = guild_profile.avatar_type
    if not icon_type.can_create_url():
        return None

    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return (
        f'{CDN_ENDPOINT}/guilds/{guild_id}/users/{user.id}/avatars/{prefix}{guild_profile.avatar_hash:0>32x}.{ext}{end}'
    )


def user_avatar_url_at(user, guild):
    """
    Returns the user's avatar's url at the guild.
    
    This function is a shared method of ``UserBase``-s.
    
    Parameters
    ----------
    guild : ``int | Guild``
        The respective guild or it's identifier.
    
    Returns
    -------
    url : `None | str`
    """
    avatar_url = user_avatar_url_for(user, guild)
    if avatar_url is None:
        avatar_url = user_avatar_url(user)
    
    return avatar_url


def user_avatar_url_at_as(user, guild, ext = None, size = None):
    """
    Returns the user's avatar's url at the guild. If the user has no avatar, then returns it's default avatar's url.
    
    This function is a shared method of ``UserBase``-s.
    
    Parameters
    ----------
    guild : ``int | Guild``
        The respective guild or it's identifier.
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`. If the user has
        animated avatar, it can `'gif'` as well.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the avatar's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    avatar_url = user_avatar_url_for_as(user, guild, ext = ext, size = size)
    if avatar_url is None:
        avatar_url = user_avatar_url_as(user, ext = ext, size = size)
    
    return avatar_url


def default_avatar_url(default_avatar):
    """
    Returns the user's default avatar's url.
    
    This function is a shared property of ``UserBase``-s.
    
    Returns
    -------
    url : `str`
    """
    return f'{CDN_ENDPOINT}/embed/avatars/{default_avatar.value}.png'


def application_icon_url(application):
    """
    Returns the application's icon's url. If the application has no icon, then returns `None`.
    
    This function is a shared property of ``Application``, ``MessageApplication``, ``IntegrationApplication``.
    
    Returns
    -------
    url : `None | str`
    """
    icon_type = application.icon_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/app-icons/{application.id}/{prefix}{application.icon_hash:0>32x}.{ext}'


def application_icon_url_as(application, ext = None, size = None):
    """
    Returns the application's icon's url. If the application has no icon, then returns `None`.
    
    This function is a shared method of ``Application``, ``MessageApplication``, ``IntegrationApplication``.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the icon's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the icon's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon_type = application.icon_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/app-icons/{application.id}/{prefix}{application.icon_hash:0>32x}.{ext}{end}'


def application_cover_url(application):
    """
    Returns the application's cover image's url. If the application has no cover image, then returns `None`.
    
    This function is a shared property of ``Application``, ``MessageApplication``.
    
    Returns
    -------
    url : `None | str`
    """
    icon_type = application.cover_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/app-assets/{application.id}/store/{prefix}{application.cover_hash:0>32x}.{ext}'


def application_cover_url_as(application, ext = None, size = None):
    """
    Returns the application's cover image's url. If the application has no cover image, then returns `None`.
    
    This function is a shared method of ``Application``, ``MessageApplication``.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the cover's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the cover's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon_type = application.cover_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/app-assets/{application.id}/store/{prefix}{application.cover_hash:0>32x}.{ext}{end}'


def team_icon_url(team):
    """
    Returns the team's icon's url. If the team has no icon, then returns `None`.
    
    This function is a shared property of ``Team``-s.
    
    Returns
    -------
    url : `None | str`
    """
    icon_type = team.icon_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/team-icons/{team.id}/{prefix}{team.icon_hash:0>32x}.{ext}'


def team_icon_url_as(team, ext = None, size = None):
    """
    Returns the team's icon's url. If the team has no icon, then returns `None`.
    
    This function is a shared method of ``Team``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the icon's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the icon's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon_type = team.icon_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/team-icons/{team.id}/{prefix}{team.icon_hash:0>32x}.{ext}{end}'


def sticker_url(sticker):
    """
    Returns the sticker's url.
    
    This function is a shared method of ``property``-s.
    
    Returns
    -------
    url : `None | str`
    """
    sticker_format = sticker.format
    if sticker_format is StickerFormat.none:
        return None
    
    if sticker_format is StickerFormat.gif:
        endpoint = MEDIA_ENDPOINT
    else:
        endpoint = CDN_ENDPOINT
        
    return f'{endpoint}/stickers/{sticker.id}.{sticker_format.extension}'


def sticker_url_as(sticker, size = None, preview = False):
    """
    Returns the sticker's url.
    
    This function is a shared method of ``Sticker``-s.
    
    Parameters
    ----------
    size : `None | int` = `None`, Optional
        The preferred minimal size of the icon's url.
    preview : `bool` = `False`, Optional
        Whether preview url should be generated.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `size` was not passed as any of the expected values.
    """
    sticker_format = sticker.format
    if sticker_format is StickerFormat.none:
        return None
    
    # Resolve size
    if size is None:
        end = ''
    else:
        if sticker_format is StickerFormat.lottie:
            end = ''
        else:
            if size in VALID_ICON_SIZES:
                end = f'?size={size}'
            else:
                raise ValueError(f'Size must be in {sorted(VALID_ICON_SIZES)!r}, got {size!r}.')
    
    # Resolve preview
    if preview:
        if sticker_format is StickerFormat.apng:
            end = f'{end}{"&" if end else "?"}passthrough=false'
    
    if sticker_format is StickerFormat.gif:
        endpoint = MEDIA_ENDPOINT
    else:
        endpoint = CDN_ENDPOINT
    
    return f'{endpoint}/stickers/{sticker.id}.{sticker_format.extension}{end}'


def sticker_pack_banner(sticker_pack):
    """
    Returns the sticker pack banner's url.
    
    This function is a shared property of ``StickerPack``-s.
    
    Returns
    -------
    url : `None | str`
    """
    banner_id = sticker_pack.banner_id
    if banner_id:
        return f'{CDN_ENDPOINT}/app-assets/710982414301790216/store/{banner_id}.png'


def sticker_pack_banner_as(sticker_pack, ext = None, size = None):
    """
    Returns the achievement's icon's url.
    
    This function is a shared method of ``StickerPack``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the banner's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the banner's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    banner_id = sticker_pack.banner_id
    if not banner_id:
        return
    
    end = _build_end(size)
    
    if ext is None:
        ext = 'png'
    
    else:
        if ext not in VALID_ICON_FORMATS:
            raise ValueError(
                f'Extension must be one of {VALID_ICON_FORMATS}, got {ext!r}.'
            )
    
    return f'{CDN_ENDPOINT}/app-assets/710982414301790216/store/{banner_id}.{ext}{end}'


def role_icon_url(role):
    """
    Returns the role's icon's image's url. If the role has no icon, then returns `None`.
    
    This function is a shared property of ``Role``-s.
    
    Returns
    -------
    url : `None | str`
    """
    icon_type = role.icon_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/role-icons/{role.id}/{prefix}{role.icon_hash:0>32x}.{ext}'


def role_icon_url_as(role, ext = None, size = None):
    """
    Returns the role's icon's image's url. If the role has no icon, then returns `None`.
    
    This function is a shared method of ``Role``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`, `'gif'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon_type = role.icon_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/role-icons/{role.id}/{prefix}{role.icon_hash:0>32x}.{ext}{end}'


def scheduled_event_image_url(scheduled_event):
    """
    Returns the scheduled event's image's url. If the scheduled event has no image, then returns `None`.
    
    This function is a property of ``ScheduledEvent``-s.
    
    Returns
    -------
    url : `None | str`
    """
    icon_type = scheduled_event.image_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/guild-events/{scheduled_event.id}/{prefix}{scheduled_event.image_hash:0>32x}.{ext}'


def scheduled_event_image_url_as(scheduled_event, ext = None, size = None):
    """
    Returns the scheduled event's image's url. If the scheduled event has no image, then returns `None`.
    
    This function is a method of ``ScheduledEvent``-s.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    icon_type = scheduled_event.image_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/guild-events/{scheduled_event.id}/{prefix}{scheduled_event.image_hash:0>32x}.{ext}{end}'


def scheduled_event_url(scheduled_event):
    """
    Returns the scheduled event's url.
    
    This function is a property of ``ScheduledEvent``-s.
    
    Returns
    -------
    url : `str`
    """
    return f'{DISCORD_ENDPOINT}/events/{scheduled_event.guild_id}/{scheduled_event.id}'


def user_avatar_decoration_url(user_or_guild_profile):
    """
    Returns the user's or guild profile's avatar decoration's url. If the user has no avatar decoration returns `None`.
    
    This function is a property of ``UserBase`` and ``GuildProfile``.
    
    Returns
    -------
    url : `None | str`
    """
    avatar_decoration = user_or_guild_profile.avatar_decoration
    if avatar_decoration is None:
        return None

    icon_type = avatar_decoration.asset_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/avatar-decoration-presets/{prefix}{avatar_decoration.asset_hash:0>32x}.{ext}'


def user_avatar_decoration_url_as(user_or_guild_profile, ext = None, size = None):
    """
    Returns the user's or guild profile's avatar decoration's url. If the user has no avatar decoration returns `None`.
    
    This function is a method of ``UserBase`` and ``GuildProfile``.
    
    Returns
    -------
    url : `None | str`
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `png`.
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    avatar_decoration = user_or_guild_profile.avatar_decoration
    if avatar_decoration is None:
        return None
    
    icon_type = avatar_decoration.asset_type
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/avatar-decoration-presets/{prefix}{avatar_decoration.asset_hash:0>32x}.{ext}{end}'


def soundboard_sound_url(sound):
    """
    Returns the url to the sound board sound.
    
    This function is a property of ``SoundboardSound``.
    
    Returns
    -------
    url : `str`
    """
    return f'{CDN_ENDPOINT}/soundboard-sounds/{sound.id}'


def _get_guild_badge_icon_url(guild_id, icon_type, icon_hash):
    """
    Gets the url for a guild badge's icon.
    
    Parameters
    ----------
    guild_id : `int`
        The guild's identifier.
    
    icon_type : ``IconType``
        The icon's type.
    
    icon_hash : `int`
        The icon's hash (uint128).
    
    Returns
    -------
    url : `None | str`
    """
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = icon_type.default_postfix
    
    return f'{CDN_ENDPOINT}/badge-icons/{guild_id}/{prefix}{icon_hash:0>32x}.{ext}'


def _get_guild_badge_icon_url_as(guild_id, icon_type, icon_hash, ext, size):
    """
    Gets the url for a guild badge's icon.
    
    Parameters
    ----------
    guild_id : `int`
        The guild's identifier.
    
    icon_type : ``IconType``
        The icon's type.
    
    icon_hash : `int`
        The icon's hash (uint128).
    
    ext : `None | str`
        The extension of the image's url.
    
    size : `None | int`
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    """
    if not icon_type.can_create_url():
        return None
    
    prefix = icon_type.prefix
    ext = _validate_extension(icon_type, ext)
    end = _build_end(size)
    
    return f'{CDN_ENDPOINT}/badge-icons/{guild_id}/{prefix}{icon_hash:0>32x}.{ext}{end}'


def guild_badge_icon_url(guild_badge):
    """
    Returns the guild badge's icon's image's url. If the guild badge has no icon, then returns `None`.
    
    This function is a property of ``UserClan``
    
    Returns
    -------
    url : `None | str`
    """
    return _get_guild_badge_icon_url(guild_badge.guild_id, guild_badge.icon_type, guild_badge.icon_hash)


def guild_badge_icon_url_as(guild_badge, ext = None, size = None):
    """
    Returns the guild badge's icon's url. If the guild badge has no icon, then returns `None`.
    
    This function is a method of ``GuildBadge``.
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
        If the guild badge has animated icon, it can be `'gif'` as well.
    
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    return _get_guild_badge_icon_url_as(guild_badge.guild_id, guild_badge.icon_type, guild_badge.icon_hash, ext, size)


def guild_activity_overview_badge_icon_url(guild_activity_overview):
    """
    Returns the guild activity overview guild's badge's icon's image's url.
    If the guild badge has no icon, then returns `None`.
    
    This function is a property of ``GuildActivityOverview``
    
    Returns
    -------
    url : `None | str`
    """
    return _get_guild_badge_icon_url(
        guild_activity_overview.id,
        guild_activity_overview.badge_icon_type,
        guild_activity_overview.badge_icon_hash,
    )


def guild_activity_overview_badge_icon_url_as(guild_activity_overview, ext = None, size = None):
    """
    Returns the guild activity overview guild's badge's icon's image's url.
    If the guild's badge has no icon, then returns `None`.
    
    This function is a property of ``GuildActivityOverview``
    
    Parameters
    ----------
    ext : `None | str` = `None`, Optional
        The extension of the image's url. Can be any of: `'jpg'`, `'jpeg'`, `'png'`, `'webp'`.
        If the guild's badge has animated icon, it can be `'gif'` as well.
    
    size : `None | int` = `None`, Optional
        The preferred minimal size of the image's url.
    
    Returns
    -------
    url : `None | str`
    
    Raises
    ------
    ValueError
        If `ext`, `size` was not passed as any of the expected values.
    """
    return _get_guild_badge_icon_url_as(
        guild_activity_overview.id,
        guild_activity_overview.badge_icon_type,
        guild_activity_overview.badge_icon_hash,
        ext,
        size,
    )
