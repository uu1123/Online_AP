@shopping

Feature: Shopping Cart

Scenario: Add Product
    Given the customer is logged in
    When the customer adds a product
    Then the product should appear in the cart

Scenario: Remove Product
    Given the customer has a product in the cart
    When the customer removes the product
    Then the cart should be empty