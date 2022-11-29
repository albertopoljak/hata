import vampytest

from ....user import User

from ...team_member import TeamMember

from ..fields import put_members_into


def test__put_members_into():
    """
    Tests whether ``put_members_into`` works as intended.
    
    Case: include internals.
    """
    team_member = TeamMember(user = User.precreate(202211230021))
    
    for input_, defaults, expected_output in (
        (None, True, {'members': []}),
        ([team_member], False, {'members': [team_member.to_data(defaults = True)]}),
    ):
        data = put_members_into(input_, {}, defaults)
        vampytest.assert_eq(data, expected_output)
