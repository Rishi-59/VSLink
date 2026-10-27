# VSLink --- Entity Relationship Design

**Status:** Working design baseline\
**Last updated:** 27 October 2026\
**Purpose:** Translate the existing VSLink ER diagram and the confirmed
requirements into an implementation-ready data model. This is a proposed
schema update, not a claim that the original diagram already contains
every field below.

## 1. Design principles

-   Use Django models and SQLite for the prototype.
-   Use Django's built-in user/authentication model for password hashing
    and session authentication. Do not store plaintext passwords or
    create a separate password field.
-   Use custom Django views, templates, and forms for customer and admin
    screens. **Django Admin must not be used.**
-   Keep a self-referencing customer referral relationship.
-   Record point changes as transactions so purchase points, referral
    bonuses, and redemption deductions can be audited.
-   Once awarded, historical points must not be recalculated when an
    administrator changes a product's points setting or referral
    percentages.

## 2. Proposed entities

### Customer / User

Use Django's built-in user model, extended with a profile if needed.
Avoid duplicating authentication fields.

  -----------------------------------------------------------------------
  Field                               Purpose
  ----------------------------------- -----------------------------------
  `id`                                Primary key (Django user ID)

  `name`                              Customer's display/full name; use
                                      built-in first/last name or a
                                      profile field

  `email`                             Login/contact identifier; enforce
                                      uniqueness if email is the login
                                      identity

  `phone`                             Optional contact number

  `role` or staff flag                Distinguishes customer and
                                      authorized administrator; use
                                      Django permissions/staff flags
                                      rather than trusting a form field

  `referral_code`                     Unique code generated for each
                                      customer

  `referrer_id`                       Nullable self-reference to the
                                      customer who referred them

  `created_at`                        Registration timestamp
  -----------------------------------------------------------------------

**Rules** - Generate a unique referral code when a customer account is
created. - A registration referral code is optional. - If a code is
provided, it must match an existing customer; otherwise show a
validation error. - A customer's referrer cannot be changed after
registration. - A customer cannot refer themselves. - Never expose
another customer's private account details through the referral tree.

### Product

  -----------------------------------------------------------------------
  Field                               Purpose
  ----------------------------------- -----------------------------------
  `id`                                Primary key

  `name`                              Product/service name

  `description`                       Description shown in the catalogue

  `price`                             Price in INR; use a decimal field

  `points_awarded`                    Points earned by the buyer for a
                                      successful purchase of this product

  `is_active`                         Whether the product is available
                                      for new purchases

  `created_at`, `updated_at`          Audit timestamps
  -----------------------------------------------------------------------

Each product has its own points value, configured by an administrator. A
change applies to **future purchases only**.

### Purchase

  -----------------------------------------------------------------------
  Field                               Purpose
  ----------------------------------- -----------------------------------
  `id`                                Primary key

  `customer_id`                       Customer making the purchase

  `product_id`                        Purchased product

  `price_paid`                        Final simulated purchase amount,
                                      after any discount

  `base_price`                        Product price at the time of
                                      purchase

  `points_earned`                     Snapshot of the product points
                                      awarded for this purchase

  `reward_id`                         Nullable reference to the single
                                      reward used, if any

  `discount_amount`                   Discount applied to this purchase

  `status`                            For this prototype, a confirmed
                                      purchase is completed immediately;
                                      a status field may still record
                                      `COMPLETED`

  `purchased_at`                      Timestamp
  -----------------------------------------------------------------------

Store price and points snapshots on the purchase so later catalogue
edits do not alter history. Checkout is simulated; there is no real
payment gateway in scope.

### Reward

  Field                        Purpose
  ---------------------------- ----------------------------------------------
  `id`                         Primary key
  `name`                       Reward name
  `description`                Customer-facing explanation
  `points_required`            Points needed to redeem the reward
  `discount_type`              Fixed INR amount or percentage
  `discount_value`             Fixed discount amount or percentage value
  `max_discount_amount`        Optional cap for percentage discounts
  `is_active`                  Whether the reward can currently be selected
  `created_at`, `updated_at`   Audit timestamps

Administrators can add, edit, activate, and deactivate rewards. A fixed
discount and a percentage discount with an optional cap are supported by
the agreed concept.

### PointsTransaction

Use an append-only transaction ledger rather than maintaining an
unexplained mutable balance.

  -----------------------------------------------------------------------
  Field                               Purpose
  ----------------------------------- -----------------------------------
  `id`                                Primary key

  `customer_id`                       Account whose balance changes

  `purchase_id`                       Nullable purchase associated with
                                      the transaction

  `redemption_id`                     Nullable redemption associated with
                                      the transaction

  `transaction_type`                  `PURCHASE`, `DIRECT_REFERRAL`,
                                      `INDIRECT_REFERRAL`, or
                                      `REDEMPTION`

  `points_delta`                      Signed change: positive for earned
                                      points, negative for redeemed
                                      points

  `referral_level`                    Optional level marker for referral
                                      bonuses

  `description`                       Human-readable reason

  `created_at`                        Timestamp
  -----------------------------------------------------------------------

The balance is the sum of `points_delta` for that customer. If a cached
balance is added for convenience, the ledger remains the source of
truth.

### Redemption

  Field               Purpose
  ------------------- -----------------------------------------------
  `id`                Primary key
  `customer_id`       Customer redeeming the reward
  `reward_id`         Reward selected
  `purchase_id`       Purchase/checkout where the reward is applied
  `points_used`       Snapshot of points charged
  `discount_amount`   Snapshot of discount applied in INR
  `redeemed_at`       Timestamp

A redemption is linked to the checkout that uses it. It is not a
reusable coupon code.

### ReferralConfig

  Field              Purpose
  ------------------ ----------------------------------------------
  `id`               Primary key
  `level1_percent`   Direct referrer's share; initial default 50%
  `level2_percent`   Second ancestor's share; initial default 25%
  `updated_at`       Last update timestamp

Only the **two ancestors above the purchasing customer** receive
referral bonuses. The purchasing customer earns their own product
points. There is no third-ancestor bonus. The percentages are editable
by authorized administrators, and current settings apply to new
purchases only.

> The original ER diagram appears to include `level3_percent`. Remove it
> or leave it unused only if implementation constraints require
> temporary compatibility; the agreed business rule supports two
> referral-bonus levels, not three.

## 3. Relationships and cardinality

-   One customer can make many purchases; each purchase belongs to one
    customer.
-   One product can appear in many purchases; each purchase refers to
    one product.
-   One customer can have many referred customers; each customer has
    zero or one direct referrer.
-   One customer can have many points transactions; each transaction
    belongs to one customer.
-   A purchase can generate multiple point transactions: buyer purchase
    points and eligible ancestor referral bonuses.
-   One reward can be redeemed many times; each redemption belongs to
    one customer and one reward.
-   A completed purchase can have zero or one redemption/reward applied.
-   Referral configuration is a singleton-like configuration record for
    the current rates.

## 4. ER diagram (Mermaid)

``` mermaid
erDiagram
    USER ||--o| CUSTOMER_PROFILE : has
    USER ||--o{ PURCHASE : makes
    PRODUCT ||--o{ PURCHASE : purchased_as
    USER o|--o{ USER : refers
    USER ||--o{ POINTS_TRANSACTION : owns
    PURCHASE o|--o{ POINTS_TRANSACTION : causes
    REWARD ||--o{ REDEMPTION : selected_for
    USER ||--o{ REDEMPTION : makes
    PURCHASE ||--o| REDEMPTION : applies
    REWARD o|--o{ PURCHASE : applied_to

    CUSTOMER_PROFILE {
        int user_id PK
        string referral_code UK
        int referrer_id FK
        string phone
        datetime created_at
    }
    PRODUCT {
        int id PK
        string name
        text description
        decimal price
        int points_awarded
        boolean is_active
    }
    PURCHASE {
        int id PK
        int customer_id FK
        int product_id FK
        decimal base_price
        decimal price_paid
        int points_earned
        decimal discount_amount
        string status
        datetime purchased_at
    }
    REWARD {
        int id PK
        string name
        int points_required
        string discount_type
        decimal discount_value
        decimal max_discount_amount
        boolean is_active
    }
    REDEMPTION {
        int id PK
        int customer_id FK
        int reward_id FK
        int purchase_id FK
        int points_used
        decimal discount_amount
        datetime redeemed_at
    }
    POINTS_TRANSACTION {
        int id PK
        int customer_id FK
        int purchase_id FK
        int redemption_id FK
        string transaction_type
        int points_delta
        int referral_level
        datetime created_at
    }
    REFERRAL_CONFIG {
        int id PK
        decimal level1_percent
        decimal level2_percent
        datetime updated_at
    }
```

## 5. Critical implementation constraints

1.  Complete checkout and its point transactions atomically using a
    database transaction.
2.  Recheck the customer's point balance at redemption time; do not
    trust a balance submitted by the browser.
3.  Apply at most one reward per purchase.
4.  A reward must be active, affordable, and valid for the purchase.
5.  Do not create a redemption or deduct points if checkout fails.
6.  Prevent duplicate point awards if the confirmation endpoint is
    submitted more than once.
7.  Use Django password hashing and permission checks for all protected
    screens.
8.  Keep all price calculations in `Decimal`-based fields/logic, not
    binary floating-point arithmetic.
