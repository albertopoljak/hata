import vampytest

from ...sku import SKU

from ..fields import validate_renewal_sku_ids


def _iter_options__passing():
    sku_id_0 = 202412210003
    sku_id_1 = 202412210004
    
    sku_0 = SKU.precreate(sku_id_0)
    sku_1 = SKU.precreate(sku_id_1)
    
    yield None, None
    yield [], None
    yield [sku_id_0, sku_id_1], (sku_id_0, sku_id_1)
    yield [sku_id_1, sku_id_0], (sku_id_0, sku_id_1)
    yield [sku_0, sku_1], (sku_id_0, sku_id_1)
    yield [sku_1, sku_0], (sku_id_0, sku_id_1)


def _iter_options__type_error():
    yield 12.6
    yield [12.6]


@vampytest._(vampytest.call_from(_iter_options__passing()).returning_last())
@vampytest._(vampytest.call_from(_iter_options__type_error()).raising(TypeError))
def test__validate_renewal_sku_ids(input_value):
    """
    Tests whether `validate_renewal_sku_ids` works as intended.
    
    Parameters
    ----------
    input_value : `object`
        Value to validate.
    
    Returns
    -------
    output : `None | tuple<int>`
    
    Raises
    ------
    TypeError
    """
    output = validate_renewal_sku_ids(input_value)
    vampytest.assert_instance(output, tuple, nullable = True)
    return output
