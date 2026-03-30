from decimal import Decimal

# One-time credit granted when a user registers (same value used in ledger + balance).
WELCOME_CREDIT_AMOUNT = Decimal("10000.00")

# Transfer fee policy (percent + floor); used only via `accounts.fees.compute_transfer_fee`.
FEE_RATE = Decimal("0.025")
FEE_MIN = Decimal("5.00")
MONEY_QUANT = Decimal("0.01")
