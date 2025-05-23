import vampytest

from ..fields import put_safety_alerts_channel_id


def test__put_safety_alerts_channel_id():
    """
    Tests whether ``put_safety_alerts_channel_id`` works as intended.
    """
    safety_alerts_channel_id = 202301150017
    
    for input_value, defaults, expected_output in (
        (0, False, {}),
        (0, True, {'safety_alerts_channel_id': None}),
        (safety_alerts_channel_id, False, {'safety_alerts_channel_id': str(safety_alerts_channel_id)}),
    ):
        data = put_safety_alerts_channel_id(input_value, {}, defaults)
        vampytest.assert_eq(data, expected_output)
