import vampytest

from ..fields import validate_status
from ..preinstanced import ScheduledEventStatus


def _iter_options__passing():
    yield None, ScheduledEventStatus.none
    yield ScheduledEventStatus.active, ScheduledEventStatus.active
    yield ScheduledEventStatus.active.value, ScheduledEventStatus.active


def _iter_options__type_error():
    yield 12.6


@vampytest._(vampytest.call_from(_iter_options__passing()).returning_last())
@vampytest._(vampytest.call_from(_iter_options__type_error()).raising(TypeError))
def test__validate_status(input_value):
    """
    Validates whether ``validate_status`` works as intended.
    
    Parameters
    ----------
    input_value : `object`
        The value to validate.
    
    Returns
    -------
    output : ``ScheduledEventStatus``
    
    Raises
    ------
    TypeError
    """
    output = validate_status(input_value)
    vampytest.assert_instance(output, ScheduledEventStatus)
    return output
