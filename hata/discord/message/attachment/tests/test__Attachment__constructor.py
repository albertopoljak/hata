from datetime import datetime as DateTime, timezone as TimeZone

import vampytest

from ....application import Application
from ....user import User

from ..attachment import Attachment
from ..flags import AttachmentFlag


def _assert_fields_set(attachment):
    """
    Tests whether all attributes are set of the given attachment.
    
    Parameters
    ----------
    attachment : ``Attachment``
        The attachment to check.
    """
    vampytest.assert_instance(attachment, Attachment)
    vampytest.assert_instance(attachment.application, Application, nullable = True)
    vampytest.assert_instance(attachment.clip_created_at, DateTime, nullable = True)
    vampytest.assert_instance(attachment.clip_users, tuple, nullable = True)
    vampytest.assert_instance(attachment.content_type, str, nullable = True)
    vampytest.assert_instance(attachment.description, str, nullable = True)
    vampytest.assert_instance(attachment.duration, float)
    vampytest.assert_instance(attachment.flags, AttachmentFlag)
    vampytest.assert_instance(attachment.height, int)
    vampytest.assert_instance(attachment.id, int)
    vampytest.assert_instance(attachment.name, str)
    vampytest.assert_instance(attachment.proxy_url, str, nullable = True)
    vampytest.assert_instance(attachment.size, int)
    vampytest.assert_instance(attachment.temporary, bool)
    vampytest.assert_instance(attachment.title, str, nullable = True)
    vampytest.assert_instance(attachment.url, str)
    vampytest.assert_instance(attachment.waveform, bytes, nullable = True)
    vampytest.assert_instance(attachment.width, int)


def test__Attachment__new__no_fields():
    """
    Tests whether ``Attachment.__new__`` works as intended.
    
    Case: No fields given.
    """
    attachment = Attachment()
    _assert_fields_set(attachment)


def test__Attachment__new__all_fields():
    """
    Tests whether ``Attachment.__new__`` works as intended.
    
    Case: All fields given.
    """
    application = Application.precreate(202502020006)
    clip_created_at = DateTime(2016, 5, 14, tzinfo = TimeZone.utc)
    clip_users = [
        User.precreate(202502020020),
        User.precreate(202502020021),
    ]
    content_type = 'application/json'
    description = 'Nue'
    duration = 12.6
    flags = AttachmentFlag(12)
    height = 1000
    name = 'i miss you'
    size = 999
    temporary = True
    title = 'flandre'
    url = 'https://www.astil.dev/'
    waveform = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    width = 998
    
    attachment = Attachment(
        application = application,
        clip_created_at = clip_created_at,
        clip_users = clip_users,
        content_type = content_type,
        description = description,
        duration = duration,
        flags = flags,
        height = height,
        name = name,
        size = size,
        temporary = temporary,
        title = title,
        url = url,
        waveform = waveform,
        width = width,
    )
    _assert_fields_set(attachment)
    
    vampytest.assert_is(attachment.application, application)
    vampytest.assert_eq(attachment.clip_created_at, clip_created_at)
    vampytest.assert_eq(attachment.clip_users, tuple(clip_users))
    vampytest.assert_eq(attachment.content_type, content_type)
    vampytest.assert_eq(attachment.description, description)
    vampytest.assert_eq(attachment.duration, duration)
    vampytest.assert_eq(attachment.flags, flags)
    vampytest.assert_eq(attachment.height, height)
    vampytest.assert_eq(attachment.name, name)
    vampytest.assert_eq(attachment.size, size)
    vampytest.assert_eq(attachment.temporary, temporary)
    vampytest.assert_eq(attachment.title, title)
    vampytest.assert_eq(attachment.url, url)
    vampytest.assert_eq(attachment.waveform, waveform)
    vampytest.assert_eq(attachment.width, width)


def test__Attachment__precreate__no_fields():
    """
    Tests whether ``Attachment.precreate`` works as intended.
    
    Case: No fields given.
    """
    attachment_id = 202211010000
    
    attachment = Attachment.precreate(attachment_id)
    _assert_fields_set(attachment)
    
    vampytest.assert_eq(attachment.id, attachment_id)


def test__Attachment__precreate__all_fields():
    """
    Tests whether ``Attachment.precreate`` works as intended.
    
    Case: All fields given.
    """
    attachment_id = 202211010001
    
    application = Application.precreate(202502020007)
    clip_created_at = DateTime(2016, 5, 14, tzinfo = TimeZone.utc)
    clip_users = [
        User.precreate(202502020022),
        User.precreate(202502020023),
    ]
    content_type = 'application/json'
    description = 'Nue'
    duration = 12.6
    flags = 12
    height = 1000
    name = 'i miss you'
    proxy_url = 'https://orindance.party/'
    size = 999
    temporary = True
    title = 'flandre'
    url = 'https://www.astil.dev/'
    waveform = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    width = 998
    
    attachment = Attachment.precreate(
        attachment_id,
        application = application,
        clip_created_at = clip_created_at,
        clip_users = clip_users,
        content_type = content_type,
        description = description,
        duration = duration,
        flags = flags,
        height = height,
        name = name,
        proxy_url = proxy_url,
        size = size,
        temporary = temporary,
        title = title,
        url = url,
        waveform = waveform,
        width = width,
    )
    _assert_fields_set(attachment)
    
    vampytest.assert_eq(attachment.id, attachment_id)
    vampytest.assert_eq(attachment.proxy_url, proxy_url)

    vampytest.assert_is(attachment.application, application)
    vampytest.assert_eq(attachment.clip_created_at, clip_created_at)
    vampytest.assert_eq(attachment.clip_users, tuple(clip_users))
    vampytest.assert_eq(attachment.content_type, content_type)
    vampytest.assert_eq(attachment.description, description)
    vampytest.assert_eq(attachment.duration, duration)
    vampytest.assert_eq(attachment.flags, flags)
    vampytest.assert_eq(attachment.height, height)
    vampytest.assert_eq(attachment.name, name)
    vampytest.assert_eq(attachment.size, size)
    vampytest.assert_eq(attachment.temporary, temporary)
    vampytest.assert_eq(attachment.title, title)
    vampytest.assert_eq(attachment.url, url)
    vampytest.assert_eq(attachment.waveform, waveform)
    vampytest.assert_eq(attachment.width, width)
