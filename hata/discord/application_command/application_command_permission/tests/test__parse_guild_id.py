import vampytest

from ..fields import parse_guild_id


def test__parse_id():
    """
    Tests whether ``parse_id`` works as intended.
    """
    guild_id = 202302210027
    
    for input_data, expected_output in (
        ({}, 0),
        ({'guild_id': None}, 0),
        ({'guild_id': str(guild_id)}, guild_id),
    ):
        output = parse_guild_id(input_data)
        vampytest.assert_eq(output, expected_output)