from datetime import datetime as DateTime, timezone as TimeZone

import vampytest

from ....utils import datetime_to_timestamp

from ..fields import parse_current_period_end


def _iter_options():
    current_period_end = DateTime(2016, 5, 14, tzinfo = TimeZone.utc)
    
    yield {}, None
    yield {'current_period_end': None}, None
    yield {'current_period_end': datetime_to_timestamp(current_period_end)}, current_period_end


@vampytest._(vampytest.call_from(_iter_options()).returning_last())
def test__parse_current_period_end(input_data):
    """
    Tests whether ``parse_current_period_end`` works as intended.
    
    Parameters
    ----------
    input_data : `dict<str, object>`
        Input data to parse from.
    
    Returns
    -------
    output : `None | DateTime`
    """
    output = parse_current_period_end(input_data)
    vampytest.assert_instance(output, DateTime, nullable = True)
    return output