from decimal import ROUND_HALF_UP, Decimal

from .constants import FEE_MIN, FEE_RATE, MONEY_QUANT


def compute_transfer_fee(transfer_amount: Decimal) -> Decimal:
    """``max(transfer_amount * FEE_RATE, FEE_MIN)`` rounded to cents (half-up)."""
    raw = max(transfer_amount * FEE_RATE, FEE_MIN)
    return raw.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
