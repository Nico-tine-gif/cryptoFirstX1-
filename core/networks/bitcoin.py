import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from socket import timeout as SocketTimeout


class BitcoinAdapter:

    PROVIDERS = (
        "https://mempool.space/api",
        "https://blockstream.info/api",
    )

    def __init__(self, timeout=5):
        self.timeout = timeout
        self.active_provider = None

    def _request(self, base_url, path):
        url = base_url.rstrip("/") + path

        request = Request(
            url,
            headers={
                "User-Agent": "cryptoFirstX1/0.1",
                "Accept": "application/json",
            },
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                body = response.read().decode("utf-8")

            if not body:
                return None

            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return body

        except HTTPError as exc:
            raise RuntimeError(
                f"HTTP:{exc.code}:{path}"
            ) from exc

        except (URLError, SocketTimeout, TimeoutError, OSError) as exc:
            raise RuntimeError(
                f"NETWORK:{type(exc).__name__}:{exc}"
            ) from exc

    def get(self, path):
        errors = []

        # Prefer the provider that worked last time.
        providers = list(self.PROVIDERS)

        if self.active_provider in providers:
            providers.remove(self.active_provider)
            providers.insert(0, self.active_provider)

        for provider in providers:
            try:
                result = self._request(provider, path)
                self.active_provider = provider
                return result

            except Exception as exc:
                errors.append(
                    f"{provider}: {exc}"
                )

        raise RuntimeError(
            "BITCOIN_ALL_PROVIDERS_UNREACHABLE | "
            + " | ".join(errors)
        )

    def provider(self):
        return self.active_provider

    def latest_height(self):
        return int(
            self.get("/blocks/tip/height")
        )

    def latest_hash(self):
        return self.get(
            "/blocks/tip/hash"
        )

    def block_hash(self, height):
        return self.get(
            f"/block-height/{int(height)}"
        )

    def block(self, block_hash):
        return self.get(
            f"/block/{block_hash}"
        )

    def block_transactions(
        self,
        block_hash,
        start_index=0,
    ):
        return self.get(
            f"/block/{block_hash}/txs/{start_index}"
        )

    def transaction(self, txid):
        return self.get(
            f"/tx/{txid}"
        )

    def transaction_status(self, txid):
        return self.get(
            f"/tx/{txid}/status"
        )

    def address(self, address):
        return self.get(
            f"/address/{address}"
        )

    def address_transactions(self, address):
        return self.get(
            f"/address/{address}/txs"
        )

    def address_mempool(self, address):
        return self.get(
            f"/address/{address}/txs/mempool"
        )

    def address_utxo(self, address):
        return self.get(
            f"/address/{address}/utxo"
        )

    def validate_address(self, address):
        # mempool.space supports this endpoint.
        # blockstream does not expose the same endpoint.
        return self._request(
            "https://mempool.space/api",
            f"/v1/validate-address/{address}"
        )

    def mempool(self):
        return self.get("/mempool")

    def mempool_recent(self):
        return self.get("/mempool/recent")

    def mempool_txids(self):
        return self.get("/mempool/txids")

    def fees(self):
        return self.get(
            "/v1/fees/recommended"
        )
