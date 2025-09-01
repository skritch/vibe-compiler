# Maybe just use Google's SDK


def parse_retry_delay(response) -> float | None:
    try:
        error_data = response.json()
        for detail in error_data.get("error", {}).get("details", []):
            if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                retry_delay_str = detail.get("retryDelay", "1s")
                # Parse delay like "7s"
                if retry_delay_str.endswith("s"):
                    return float(retry_delay_str[:-1])
    except Exception:
        return None
