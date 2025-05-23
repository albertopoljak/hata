import vampytest

from ..fields import put_content


def _iter_options():
    yield None, False, {}
    yield None, True, {'content': ''}
    yield 'a', False, {'content': 'a'}
    yield 'a', True, {'content': 'a'}


@vampytest._(vampytest.call_from(_iter_options()).returning_last())
def test__put_content(input_value, defaults):
    """
    Tests whether ``put_content`` works as intended.
    
    Parameters
    ----------
    input_value : `None`, `str`
        Value to serialize.
    defaults : `bool`
        Whether values of their default value should be included as well.
    
    Returns
    -------
    output : `dict<str, object>`
    """
    return put_content(input_value, {}, defaults)
