
from decimal import Decimal

import httpx
from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool
from collections import defaultdict
from app.services.bitvavo_account_service import BitvavoAccountService
from app.services.bitvavo_service import get_market_prices
from app.services.portfolio_pnl_service import calculate_pnl

router = APIRouter(
    prefix="/api/v1/portfolio",
    tags=["Portfolio"],
)


@router.get("/balances")
async def get_portfolio_balances():
    try:
        service = BitvavoAccountService()
        return await run_in_threadpool(service.get_balances)
    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail="Bitvavo API-Zugangsdaten fehlen.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Bitvavo-Kontostand nicht verfügbar.",
        ) from exc


@router.get("/summary")
async def get_portfolio_summary():
    try:
        service = BitvavoAccountService()

        balances = await run_in_threadpool(
            service.get_balances
        )

        market_prices = await get_market_prices()

        price_lookup = {
            item["market"]: Decimal(str(item["price_eur"]))
            for item in market_prices
            if item["available"] and item["price_eur"] is not None
        }

        assets = []
        total_eur = Decimal("0")
        eur_available = Decimal("0")
        missing_prices = []

        for balance in balances:
            symbol = balance["symbol"]

            available = Decimal(balance["available"])
            in_order = Decimal(balance["in_order"])
            amount = available + in_order

            if amount == 0:
                continue

            if symbol == "EUR":
                price_eur = Decimal("1")
                eur_available = available
            else:
                price_eur = price_lookup.get(f"{symbol}-EUR")

            value_eur = (
                amount * price_eur
                if price_eur is not None
                else None
            )

            if value_eur is not None:
                total_eur += value_eur
            else:
                missing_prices.append(symbol)

            assets.append({
                "symbol": symbol,
                "available": str(available),
                "in_order": str(in_order),
                "total": str(amount),
                "price_eur": (
                    str(price_eur)
                    if price_eur is not None
                    else None
                ),
                "value_eur": (
                    str(value_eur.quantize(Decimal("0.01")))
                    if value_eur is not None
                    else None
                ),
            })

        return {
            "total_value_eur": (
                str(total_eur.quantize(Decimal("0.01")))
                if not missing_prices
                else None
            ),
            "known_value_eur": str(
                total_eur.quantize(Decimal("0.01"))
            ),
            "eur_available": str(eur_available),
            "valuation_complete": not missing_prices,
            "missing_prices": missing_prices,
            "assets": assets,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail="Portfolio-Konfiguration ungültig.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Bitvavo-Daten momentan nicht verfügbar.",
        ) from exc


@router.get("/transactions")
async def get_portfolio_transactions():
    try:
        service = BitvavoAccountService()

        return await run_in_threadpool(
            service.get_transactions
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail="Bitvavo-Konfiguration ungültig.",
        ) from exc

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Bitvavo-Transaktionen nicht verfügbar.",
        ) from exc



@router.get("/trades")
async def get_portfolio_trades():
    try:
        service = BitvavoAccountService()
        history = await run_in_threadpool(
            service.get_transactions
        )

        groups = defaultdict(list)

        for item in history.get("items", []):
            side = item.get("type")

            if side not in ("buy", "sell"):
                continue

            symbol = (
                item.get("receivedCurrency")
                if side == "buy"
                else item.get("sentCurrency")
            )

            key = (
                item.get("executedAt"),
                side,
                symbol,
                item.get("priceAmount"),
            )

            groups[key].append(item)

        trades = []

        for (executed_at, side, symbol, price), fills in groups.items():
            quantity = Decimal("0")
            gross_eur = Decimal("0")
            fees_eur = Decimal("0")

            for fill in fills:
                quantity += Decimal(
                    fill["receivedAmount"]
                    if side == "buy"
                    else fill["sentAmount"]
                )

                gross_eur += Decimal(
                    fill["sentAmount"]
                    if side == "buy"
                    else fill["receivedAmount"]
                )

                if fill.get("feesCurrency") == "EUR":
                    fees_eur += Decimal(
                        fill.get("feesAmount", "0")
                    )

            total_eur = (
                gross_eur + fees_eur
                if side == "buy"
                else gross_eur - fees_eur
            )

            trades.append({
                "executed_at": executed_at,
                "side": side,
                "symbol": symbol,
                "price_eur": str(price),
                "quantity": str(quantity),
                "gross_eur": str(gross_eur),
                "fees_eur": str(fees_eur),
                "total_eur": str(total_eur),
                "executions": len(fills),
            })

        trades.sort(
            key=lambda trade: trade["executed_at"],
            reverse=True,
        )

        return {
            "count": len(trades),
            "trades": trades,
            "history_complete": (
                history.get("currentPage")
                == history.get("totalPages")
                == 1
            ),
        }

    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Transaktionen konnten nicht verarbeitet werden.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Bitvavo-Transaktionen nicht verfügbar.",
        ) from exc



@router.get("/pnl")
async def get_portfolio_pnl():
    try:
        service = BitvavoAccountService()

        history = await run_in_threadpool(
            service.get_transactions
        )

        # Keine unvollständigen Ergebnisse ausgeben.
        if (
            history.get("currentPage") != 1
            or history.get("totalPages") != 1
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Mehrere Historienseiten vorhanden. "
                    "Pagination muss zuerst implementiert werden."
                ),
            )

        market_prices = await get_market_prices()

        return calculate_pnl(
            transactions=history["items"],
            market_prices=market_prices,
        )

    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Bitvavo-Daten nicht verfügbar.",
        ) from exc
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
