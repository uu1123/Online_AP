from behave import given, when, then

cart = []
logged_in = False

@given("the customer is logged in")
def step_login(context):
    global logged_in
    logged_in = True

@when("the customer adds a product")
def step_add(context):
    cart.append("Laptop")

@then("the product should appear in the cart")
def step_verify(context):
    assert "Laptop" in cart


@given("the customer has a product in the cart")
def step_cart(context):
    cart.clear()
    cart.append("Laptop")

@when("the customer removes the product")
def step_remove(context):
    cart.remove("Laptop")

@then("the cart should be empty")
def step_empty(context):
    assert len(cart) == 0