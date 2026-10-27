# VSLink --- Data Flow Diagrams

**Status:** Working design baseline\
**Last updated:** 27 October 2026\
**Scope:** Context (Level 0) and Level 1 data flows for the Django
prototype.

These Mermaid diagrams are a text-based, maintainable companion to the
original DFD sketches. They preserve the documented actors and features
while reflecting the decisions confirmed during requirements discussion.

## 1. External entities

-   **Customer:** registers, logs in, browses products, completes
    simulated purchases, redeems rewards, and views
    points/history/referral tree.
-   **Administrator:** uses protected custom admin screens to manage
    products, points values, rewards, and referral percentages, and to
    view customer/referral information.

## 2. DFD Level 0 --- Context diagram

``` mermaid
flowchart LR
    C[Customer]
    A[Administrator]
    S((VSLink Loyalty and Referral System))

    C -->|Registration details and optional referral code| S
    C -->|Login credentials| S
    C -->|Product selection and checkout/reward choice| S
    S -->|Account result, catalogue, checkout result| C
    S -->|Points balance, transaction history, referral tree| C

    A -->|Admin login and management changes| S
    S -->|Customer, purchase, points and referral summaries| A
    S -->|Management operation result| A
```

The context diagram treats VSLink as one process. It does not show
internal database tables or implementation details.

## 3. DFD Level 1 --- Decomposition

``` mermaid
flowchart TB
    C[Customer]
    A[Administrator]

    P1((1.0 Registration and Authentication))
    P2((2.0 Catalogue and Product Management))
    P3((3.0 Simulated Checkout and Purchase))
    P4((4.0 Points and Referral Calculation))
    P5((5.0 Reward Redemption))
    P6((6.0 Dashboard and Referral Tree))
    P7((7.0 Admin Configuration and Reporting))

    D1[(D1 Users and Customer Profiles)]
    D2[(D2 Products)]
    D3[(D3 Purchases)]
    D4[(D4 Points Transaction Ledger)]
    D5[(D5 Rewards and Redemptions)]
    D6[(D6 Referral Configuration)]

    C -->|Registration / login data| P1
    P1 <-->|User/profile lookup and creation| D1
    P1 -->|Registration or login result| C

    C -->|Browse request| P2
    P2 <-->|Active product data| D2
    P2 -->|Product catalogue| C

    C -->|Selected product and optional reward| P3
    P3 <-->|Product and current points settings| D2
    P3 -->|Purchase record| D3
    P3 -->|Validated checkout details| P4
    P3 -->|Reward selection and checkout context| P5
    P3 -->|Purchase result| C

    P4 <-->|Purchaser and ancestor relationships| D1
    P4 <-->|Current referral percentages| D6
    P4 -->|Purchase and referral point entries| D4
    P4 -->|Points calculation result| P3

    P5 <-->|Active rewards and redemption records| D5
    P5 <-->|Current points balance from ledger| D4
    P5 -->|Redemption and discount result| P3

    C -->|Dashboard request| P6
    P6 <-->|Customer and referral relationships| D1
    P6 <-->|Purchase history| D3
    P6 <-->|Point history and balance| D4
    P6 <-->|Redemption history| D5
    P6 -->|Dashboard, points, history, referral tree| C

    A -->|Protected management requests| P7
    P7 <-->|Product changes| D2
    P7 <-->|Reward changes| D5
    P7 <-->|Referral percentage changes| D6
    P7 <-->|Customer and purchase summaries| D1
    P7 <-->|Purchase records| D3
    P7 <-->|Points summaries| D4
    P7 -->|Management result and reports| A
```

## 4. Main process descriptions

### 1.0 Registration and Authentication

-   Validate registration fields.
-   Accept an optional referral code.
-   Reject an invalid supplied referral code.
-   Generate a unique referral code for the new customer.
-   Store the referral relationship at registration; do not permit later
    changes.
-   Authenticate using Django's authentication/password hashing
    facilities.

### 2.0 Catalogue and Product Management

-   Customers can browse active products/services.
-   Administrators can add/edit products and set each product's points
    value.
-   Product point changes affect future purchases only.

### 3.0 Simulated Checkout and Purchase

-   Customer selects a product and optionally one reward.
-   The system calculates the final amount and confirms the simulated
    purchase immediately.
-   No real payment gateway is integrated.
-   Purchase snapshots preserve the price and points applicable at
    checkout.

### 4.0 Points and Referral Calculation

-   Award the configured points to the purchasing customer.
-   Award the configured percentage of the purchaser's base product
    points to the direct referrer (initial default 50%) and second
    ancestor (initial default 25%), if present.
-   Do not award referral bonuses to more distant ancestors.
-   Store each point change as a ledger transaction.
-   The current configured rates apply to new purchases; historical
    entries are not recalculated.

### 5.0 Reward Redemption

-   Offer active rewards the customer can afford.
-   Permit one reward per purchase.
-   Apply the discount directly to that checkout; do not issue a
    reusable coupon code.
-   Deduct points only when the checkout succeeds, in the same atomic
    operation as the purchase/redemption records.

### 6.0 Dashboard and Referral Tree

-   Show the customer's point balance and transaction history.
-   Show purchase and redemption history.
-   Display the customer's referral hierarchy without exposing
    unnecessary private information.

### 7.0 Admin Configuration and Reporting

-   Use custom protected Django views/templates/forms; do not use Django
    Admin.
-   Manage products, per-product points, rewards, and referral
    percentages.
-   View customers, referral hierarchy, purchases, and points summaries.

## 5. Data-flow integrity rules

-   Every protected admin operation requires server-side authorization.
-   Client-submitted prices, points, discounts, and balances are never
    trusted; calculate them server-side.
-   Checkout and related point changes must be atomic.
-   Invalid referral codes must not silently create an unlinked
    referral.
-   No real payment processor or external order system is part of the
    current prototype.
