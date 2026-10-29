
from collections import defaultdict, deque
from decimal import Decimal


ZERO = Decimal("0")
CENT = Decimal("0.01")


def money(value: Decimal) -> str:
    return str(value.quantize(CENT))


def calculate_pnl(
    transactions: list[dict],
    market_prices: list[dict],
) -> dict:
    prices = {
        item["market"]: Decimal(str(item["price_eur"]))
        for item in market_prices
        if item["available"] and item["price_eur"] is not None
    }

    # Pro Coin: noch nicht verkaufte Kaufmengen
    lots = defaultdict(deque)
    realized = defaultdict(lambda: ZERO)
    buy_count = defaultdict(int)
    sell_count = defaultdict(int)

    # Historie von alt nach neu verarbeiten
    transactions = sorted(
        transactions,
        key=lambda item: item["executedAt"],
    )

    for tx in transactions:
        side = tx.get("type")

        if side not in ("buy", "sell"):
            # Einzahlungen und Rebates sind keine Trades.
            continue

        if side == "buy":
            symbol = tx["receivedCurrency"]

            if tx["sentCurrency"] != "EUR":
                raise ValueError(
                    "Nur direkte EUR-Käufe werden unterstützt."
                )

            if tx.get("feesCurrency") not in (None, "EUR"):
                raise ValueError(
                    "Gebühren in anderen Währungen "
                    "werden noch nicht unterstützt."
                )

            quantity = Decimal(tx["receivedAmount"])
            gross = Decimal(tx["sentAmount"])
            fee = Decimal(tx.get("feesAmount") or "0")

            if quantity <= 0:
                raise ValueError("Ungültige Kaufmenge.")

            # Gesamte Anschaffungskosten inkl. Kaufgebühr
            lots[symbol].append({
                "quantity": quantity,
                "unit_cost": (gross + fee) / quantity,
            })

            buy_count[symbol] += 1

        elif side == "sell":
            symbol = tx["sentCurrency"]

            if tx["receivedCurrency"] != "EUR":
                raise ValueError(
                    "Nur direkte EUR-Verkäufe werden unterstützt."
                )

            if tx.get("feesCurrency") not in (None, "EUR"):
                raise ValueError(
                    "Gebühren in anderen Währungen "
                    "werden noch nicht unterstützt."
                )

            quantity = Decimal(tx["sentAmount"])
            gross = Decimal(tx["receivedAmount"])
            fee = Decimal(tx.get("feesAmount") or "0")

            if quantity <= 0:
                raise ValueError("Ungültige Verkaufsmenge.")

            net_proceeds = gross - fee
            remaining = quantity
            cost_basis = ZERO

            # FIFO: älteste Käufe zuerst verrechnen
            while remaining > 0:
                if not lots[symbol]:
                    raise ValueError(
                        f"Für {symbol} fehlen frühere Käufe."
                    )

                lot = lots[symbol][0]
                used = min(remaining, lot["quantity"])

                cost_basis += used * lot["unit_cost"]
                lot["quantity"] -= used
                remaining -= used

                if lot["quantity"] == 0:
                    lots[symbol].popleft()

            realized[symbol] += net_proceeds - cost_basis
            sell_count[symbol] += 1

    symbols = sorted(
        set(lots) | set(realized)
    )

    positions = []
    realized_total = ZERO
    unrealized_total = ZERO
    valuation_complete = True

    for symbol in symbols:
        quantity = sum(
            (lot["quantity"] for lot in lots[symbol]),
            ZERO,
        )

        cost_basis = sum(
            (
                lot["quantity"] * lot["unit_cost"]
                for lot in lots[symbol]
            ),
            ZERO,
        )

        price = prices.get(f"{symbol}-EUR")

        market_value = (
            quantity * price
            if price is not None
            else None
        )

        unrealized = (
            market_value - cost_basis
            if market_value is not None
            else None
        )

        if unrealized is None and quantity > 0:
            valuation_complete = False
        elif unrealized is not None:
            unrealized_total += unrealized

        realized_total += realized[symbol]

        positions.append({
            "symbol": symbol,
            "quantity": str(quantity),
            "cost_basis_eur": money(cost_basis),
            "average_cost_eur": (
                str(cost_basis / quantity)
                if quantity > 0
                else None
            ),
            "market_price_eur": (
                str(price) if price is not None else None
            ),
            "market_value_eur": (
                money(market_value)
                if market_value is not None
                else None
            ),
            "unrealized_pnl_eur": (
                money(unrealized)
                if unrealized is not None
                else None
            ),
            "realized_pnl_eur": money(realized[symbol]),
            "buy_executions": buy_count[symbol],
            "sell_executions": sell_count[symbol],
        })

    return {
        "cost_basis_method": "FIFO",
        "realized_pnl_eur": money(realized_total),
        "unrealized_pnl_eur": (
            money(unrealized_total)
            if valuation_complete
            else None
        ),
        "valuation_complete": valuation_complete,
        "positions": positions,
        "rebates_included": False,
    }
