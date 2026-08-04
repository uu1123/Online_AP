Feature: ATM Withdrawal

Scenario: Withdraw Money
    Given the customer has enough balance
    When the customer withdraws 100 dollars
    Then the account balance should be reduced

Scenario: Insufficient Balance
    Given the customer has insufficient balance
    When the customer withdraws 100 dollars
    Then the withdrawal should be rejected
