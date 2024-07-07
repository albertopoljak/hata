import vampytest

from ..constants import TITLE_LENGTH_MAX
from ..fields import validate_title


def _iter_options__passing():
    yield None, None
    yield '', None
    yield 'a', 'a'
    yield 'aa', 'aa'
    yield 1, '1'


def _iter_options__value_error():
    yield 'a' * (TITLE_LENGTH_MAX + 1)


@vampytest._(vampytest.call_from(_iter_options__passing()).returning_last())
@vampytest._(vampytest.call_from(_iter_options__value_error()).raising(ValueError))
def test__validate_title(input_value):
    """
    Tests whether `validate_title` works as intended.
    
    Parameters
    ----------
    input_value : `object`
        Value to validate.
    
    Returns
    -------
    output : `None | str`
    
    Raises
    ------
    TypeError
    """
    return validate_title(input_value)
