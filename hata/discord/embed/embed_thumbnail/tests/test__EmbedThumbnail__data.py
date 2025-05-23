import vampytest

from ...embed_field_base import EmbedMediaFlag

from ..thumbnail import EmbedThumbnail

from .test__EmbedThumbnail__constructor import _assert_fields_set


def test__EmbedThumbnail__from_data():
    """
    Tests whether ``EmbedThumbnail.from_data`` works as intended.
    """
    flags = EmbedMediaFlag(3)
    height = 1000
    proxy_url = 'https://www.astil.dev/'
    url = 'https://orindance.party/'
    width = 1001
    
    data = {
        'flags': flags,
        'height': height,
        'proxy_url': proxy_url,
        'url': url,
        'width': width,
    }
    
    embed_thumbnail = EmbedThumbnail.from_data(data)
    _assert_fields_set(embed_thumbnail)
    
    vampytest.assert_eq(embed_thumbnail.flags, flags)
    vampytest.assert_eq(embed_thumbnail.height, height)
    vampytest.assert_eq(embed_thumbnail.proxy_url, proxy_url)
    vampytest.assert_eq(embed_thumbnail.url, url)
    vampytest.assert_eq(embed_thumbnail.width, width)


def test__EmbedThumbnail__to_data():
    """
    Tests whether ``EmbedThumbnail.to_data`` works as intended.
    
    Case: Include defaults & internals.
    """
    flags = EmbedMediaFlag(3)
    height = 1000
    proxy_url = 'https://www.astil.dev/'
    url = 'https://orindance.party/'
    width = 1001
    
    data = {
        'flags': flags,
        'height': height,
        'proxy_url': proxy_url,
        'url': url,
        'width': width,
    }
    
    # We cant set the internal fields with the constructor, so we use `.from_data` instead.
    embed_thumbnail = EmbedThumbnail.from_data(data)
    
    expected_output = data
    
    vampytest.assert_eq(
        embed_thumbnail.to_data(defaults = True, include_internals = True),
        expected_output,
    )
