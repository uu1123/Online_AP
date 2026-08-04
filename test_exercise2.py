import pytest

def make_headings():
    headings=[
        "transaction_id","timestamp","store_id","product_id",
        "quantity","unit_price","total_amount","payment_method"
    ]
    return headings
    
@pytest.mark.parametrize(
    "index, expected_heading",

    [

        (0, "transaction_id"),

        (1, "timestamp"),

        (2, "store_id"),

        (3, "product_id"),

        (4, "quantity"),

        (5, "unit_price"),

        (6, "total_amount"),

        (7, "payment_method"),

    ]

)

def test_make_headings(index, expected_heading):

    headings = make_headings()

    assert headings[index] == expected_heading
    assert isinstance(headings[index], str)
