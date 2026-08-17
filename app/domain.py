from typing import List, Dict, Any


def format_currency_de(amount: float) -> str:
    """Formats float amount to German currency string e.g. -1235.0 -> "-1.235,00 €"."""
    is_negative = amount < 0
    abs_amount = abs(amount)

    # Format integer part with dot as thousands separator
    int_part = f"{int(abs_amount):,}".replace(",", ".")
    dec_part = f"{abs_amount:.2f}".split(".")[1]

    formatted = f"{int_part},{dec_part} €"
    if is_negative:
        formatted = f"-{formatted}"
    return formatted


def calculate_plan_totals(positions: List[Dict[str, Any]], contributions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculates sum of positions (expenses), sum of contributions, and net balance."""
    total_expenses = sum(float(p.get("amount", 0.0)) for p in positions)
    total_contributions = sum(float(c.get("amount", 0.0)) for c in contributions)
    net_balance = total_expenses + total_contributions

    return {
        "total_expenses": round(total_expenses, 2),
        "total_contributions": round(total_contributions, 2),
        "net_balance": round(net_balance, 2),
        "total_expenses_formatted": format_currency_de(total_expenses),
        "total_contributions_formatted": format_currency_de(total_contributions),
        "net_balance_formatted": format_currency_de(net_balance),
    }
