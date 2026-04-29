import json
import logging
import time
import urllib.request
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional

logger = logging.getLogger("security")

# Realistic fallback rates relative to USD in case external currency API is unreachable
FALLBACK_USD_RATES: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "CAD": 1.36,
    "CNY": 7.24,
    "JPY": 154.5,
    "AUD": 1.52,
    "CHF": 0.91,
    "HKD": 7.82,
    "SGD": 1.35,
}

class CurrencyService:
    """
    Multi-Currency conversion service with local caching and offline fallback.
    Provides exchange rate retrieval and decimal-accurate currency conversions.
    """

    def __init__(self, cache_ttl_seconds: int = 3600):
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_rates(self, base: str = "USD") -> Dict[str, Any]:
        """
        Fetch exchange rates for a base currency.
        Utilizes an in-memory cache and falls back to pre-defined rates on failure.
        """
        base = base.upper().strip()
        now = time.time()

        # 1. Check in-memory cache
        cached = self._cache.get(base)
        if cached and (now - cached["timestamp"] < self.cache_ttl):
            return cached["data"]

        # 2. Attempt fetching from public exchange API
        url = f"https://api.frankfurter.app/latest?from={base}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "UniSplit-Fintech/1.0 (Expense Platform)"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode())
                    result = {
                        "amount": payload.get("amount", 1.0),
                        "base": payload.get("base", base),
                        "date": payload.get("date", ""),
                        "rates": payload.get("rates", {}),
                        "source": "live"
                    }
                    self._cache[base] = {"timestamp": now, "data": result}
                    return result
        except Exception as e:
            logger.warning(f"CURRENCY_API_FALLBACK | Could not reach live currency API: {str(e)}. Using fallback rates.")

        # 3. Fallback calculation if live network request fails
        return self._generate_fallback_rates(base)

    def convert(self, amount: Decimal, from_curr: str, to_curr: str) -> Decimal:
        """
        Convert an amount between two currencies with financial precision (2 decimal places).
        """
        from_curr = from_curr.upper().strip()
        to_curr = to_curr.upper().strip()

        if from_curr == to_curr:
            return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        rates_data = self.get_rates(base=from_curr)
        rate = rates_data.get("rates", {}).get(to_curr)

        if not rate:
            # If target rate is missing, calculate cross rate via USD
            usd_rates = self._generate_fallback_rates("USD")["rates"]
            from_in_usd = Decimal(str(usd_rates.get(from_curr, 1.0)))
            to_in_usd = Decimal(str(usd_rates.get(to_curr, 1.0)))
            converted = amount * (to_in_usd / from_in_usd)
        else:
            converted = amount * Decimal(str(rate))

        return converted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _generate_fallback_rates(self, base: str) -> Dict[str, Any]:
        """Generate normalized fallback rates relative to requested base."""
        base_to_usd = FALLBACK_USD_RATES.get(base, 1.0)
        rates: Dict[str, float] = {}

        for curr, usd_rate in FALLBACK_USD_RATES.items():
            if curr != base:
                # rate = target_usd_rate / base_usd_rate
                rates[curr] = round(usd_rate / base_to_usd, 4)

        return {
            "amount": 1.0,
            "base": base,
            "date": "2026-04-25",
            "rates": rates,
            "source": "fallback"
        }

# Global singleton
currency_service = CurrencyService()
