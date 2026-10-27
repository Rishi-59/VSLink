# VSLink --- Requirements Freeze

**Project:** VSLink customer loyalty and referral management system for
VS Software Lab\
**Status:** Baseline frozen for implementation\
**Freeze date:** 27 October 2026\
**Target deadline:** 30 October 2026

This document records decisions confirmed in the project discussion and
the minimum implementation assumptions needed to proceed. It is intended
to prevent scope drift during the remaining build time.

## 1. Objective

Build a working prototype that allows customers to register, browse
services/products, make simulated purchases, earn loyalty and referral
points, redeem points for discounts at checkout, and view their point
history and referral hierarchy. Administrators manage products, rewards,
referral rates, and customer-related information through custom screens.

## 2. Mandatory technology and constraints

-   Language: Python
-   Framework: Django
-   Front end: HTML, CSS, Bootstrap
-   Database: SQLite
-   Package manager: `uv`
-   Editor/development environment: PyCharm on macOS
-   Authentication: Django built-in authentication and password hashing
-   **Django Admin is prohibited.** All admin pages must be custom
    Django views, templates, and forms.
-   Keep work in GitHub with meaningful commits to preserve a
    development trail.
-   Deliver working code, `requirements.txt`, and a prototype ZIP. Do
    not include `.venv`/virtual environment files in the ZIP.

## 3. Customer features

### Registration and authentication

-   Customers can register and log in.
-   A customer receives a unique referral code automatically.
-   Entering a referral code during registration is optional.
-   If a code is entered, it must be valid; invalid codes display a
    validation error.
-   A customer cannot refer themselves.
-   A customer's referrer is fixed after registration and cannot be
    changed later.
-   Use secure password hashing; never store plaintext passwords.

### Product catalogue and simulated purchase

-   Customers can view active products/services and their prices.
-   Each product has an independently configurable points value set by
    an administrator.
-   A customer can select a product and confirm a simulated purchase.
-   Clicking **Confirm Purchase** completes the purchase immediately.
-   No real payment gateway is required for the prototype.
-   Store a snapshot of the product price and points awarded at the time
    of purchase.
-   Product points edits affect future purchases only; they do not
    recalculate historical points.

### Points and referral rewards

-   The purchaser receives the points configured for the purchased
    product.
-   Referral bonuses are calculated from the points earned on the
    purchaser's product, not from the discount-adjusted cash price.
-   Initial example configuration:
    -   Direct referrer: 50% of the purchaser's product points.
    -   Second ancestor: 25% of the purchaser's product points.
-   The 50% and 25% rates are configurable by an authorized
    administrator.
-   Only the two ancestors above the purchaser receive referral bonuses.
    The purchaser earns their own product points; no more distant
    ancestor receives a bonus.
-   Current referral rates apply to new purchases only. Do not
    recalculate past transactions when rates change.
-   Record all earning and deduction events in a points transaction
    ledger.
-   Display a balance derived from the ledger (or maintain a carefully
    synchronized cache if needed).

**Example:** If a product awards 1,000 points, the purchaser earns
1,000. If the purchaser has a direct referrer, that referrer earns 500
at a 50% rate. If a second ancestor exists, that ancestor earns 250 at a
25% rate.

### Reward catalogue and redemption

-   Administrators can add/edit rewards, set point costs, and
    activate/deactivate rewards.
-   Support fixed-amount INR discounts and percentage discounts with an
    optional maximum cap.
-   Customers can redeem only an active reward for which they have
    enough points.
-   Only one reward can be used per purchase.
-   Apply the discount directly at checkout; do not create reusable
    coupon codes.
-   The checkout redemption is immediate and associated with that
    purchase.
-   Deduct points only if the checkout succeeds.
-   A failed checkout must not leave a redemption record or deduct
    points.

### Customer dashboard

-   Show the current points balance.
-   Show point transaction history.
-   Show purchase and redemption history.
-   Show the customer's referral hierarchy/tree.
-   Avoid exposing private account information belonging to other
    customers.

## 4. Administrator features

Provide a separate custom admin interface with server-side access
controls. Do not expose a public admin registration flow.

Administrators should be able to: - Add, edit, activate, and deactivate
products/services. - Configure each product's points value. - Add, edit,
activate, and deactivate rewards. - Configure the two referral bonus
percentages. - View customer records and referral hierarchy. - View
purchase and points summaries.

Admin access must be enforced in views, not merely hidden in the user
interface.

## 5. Non-functional requirements and integrity rules

-   Validate all inputs server-side.
-   Use Django's CSRF protection on forms.
-   Use decimal arithmetic for money.
-   Recalculate prices, discounts, point costs, and balances on the
    server; do not trust browser-submitted totals.
-   Use database transactions for checkout, redemption, and associated
    point entries so they succeed or fail together.
-   Prevent duplicate point awards if checkout is submitted more than
    once.
-   Do not allow negative point balances.
-   Protect customer-only and admin-only pages with authorization
    checks.
-   Keep secrets and local environment files out of Git.
-   Include setup/run instructions in the project README.

## 6. Explicitly out of scope for this deadline

-   Real payment gateway integration.
-   Reusable coupon codes.
-   Multiple rewards on a single purchase.
-   Changing a customer's referrer after registration.
-   Recalculating historical points when configuration changes.
-   Django Admin site.
-   Production-grade deployment, external order fulfilment, or
    integration with VS Software Lab's real purchasing systems unless
    separately requested.

## 7. Implementation assumptions to keep work moving

These are pragmatic defaults, not additional business decisions
requiring approval: - Use Django's built-in user model with a related
customer profile where appropriate. - Use an append-only points ledger
as the source of truth. - Treat a completed simulated purchase as
immediately successful. - Snapshot price, awarded points, reward cost,
and discount at transaction time. - If a reward discount exceeds the
purchase amount, cap the discount at the eligible purchase total. - If
no referral code is provided, register the customer without a
referrer. - Deactivated products and rewards are unavailable for new
purchases/redemptions, but historical records remain visible. - Use the
configured referral percentages that are active when a purchase is
confirmed.

## 8. Definition of done

The prototype is ready for handoff when: - A customer can register, log
in, and optionally link to a valid referrer. - Invalid referral codes
are rejected. - An administrator can manage products, points values,
rewards, and referral percentages through custom screens. - A customer
can complete a simulated purchase. - Purchase points and eligible
referral bonuses are recorded correctly. - A customer can apply at most
one eligible reward at checkout. - Point deductions and redemption
records occur only on successful checkout. - Customer dashboards show
balances, history, and referral hierarchy. - Authorization and basic
input validation are in place. - Migrations and setup instructions work
from a clean checkout. - `requirements.txt` is present, Git history is
maintained, and the ZIP excludes virtual environment files.

## 9. Change control

The requirements above are frozen for the initial prototype. Any new
feature should be deferred unless it is essential to correct a
contradiction or unblock a core requirement. When implementation reveals
a genuine ambiguity, document it briefly and resolve only that issue
before proceeding.
