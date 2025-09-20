from datetime import datetime
import pandas as pd
from pathlib import Path
from typing import Dict, Any,List

from tvDatafeed import TvDatafeed, Interval
from google.adk.tools import tool_context
from pydantic import BaseModel, Field

# general
def get_current_time() -> dict:
    """
    Get the current time in the format YYYY-MM-DD HH:MM:SS
    """
    return {"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),}

# debugging agent
def _trim_lines(text, max_lines) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    # keep head and tail halves
    keep = max_lines // 2
    head_part = "\n".join(lines[:keep])
    tail_part = "\n".join(lines[-keep:])
    return f"{head_part}\n\n... [snip {len(lines)-max_lines} lines] ...\n\n{tail_part}"

def get_error_text() -> Dict[str, Any]:
    """
    Returns a token-safe view of error.txt:
      - status: "success" | "error"
      - report: { head: str, tail: str, merged: str }
      - meta: { path, size_bytes, truncated, head_bytes, tail_bytes, max_lines }
    Strategy:
      - Read HEAD_BYTES from start + TAIL_BYTES from end.
      - Merge them (with a clear divider) and apply a line cap.
    """
    # Fixed path (per your setup)
    _ERROR_PATH = Path("ai_agent/LandingStage_manager/sub_agents/debugging_bro/sample_error.txt")
    # Token-safe caps (tweak as needed)
    HEAD_BYTES   = 64_000    # first ~64KB
    TAIL_BYTES   = 128_000   # last  ~128KB
    MAX_LINES    = 6_000     # final safety line cap across head+tail

    try:
        if not _ERROR_PATH.exists():
            return {"status": "error", "report": "File not found", "meta": {"path": str(_ERROR_PATH)}}

        size = _ERROR_PATH.stat().st_size
        truncated = size > (HEAD_BYTES + TAIL_BYTES)

        with _ERROR_PATH.open("rb") as f:
            # HEAD
            head = f.read(HEAD_BYTES)
            head_txt = head.decode("utf-8", errors="replace")

            # TAIL
            tail_txt = ""
            if size > HEAD_BYTES:
                take_tail = min(TAIL_BYTES, max(0, size - HEAD_BYTES))
                # Seek to start of tail window from end
                f.seek(max(0, size - take_tail))
                tail_txt = f.read(take_tail).decode("utf-8", errors="replace")

        divider = "\n\n----- [LOG TAIL BELOW] -----\n\n"
        merged = _trim_lines(head_txt + divider + tail_txt, MAX_LINES)

        return {
            "status": "success",
            "report": {
                "head": head_txt,
                "tail": tail_txt,
                "merged": merged,
            },
            "meta": {
                "path": str(_ERROR_PATH),
                "size_bytes": size,
                "truncated": truncated,
                "head_bytes": HEAD_BYTES,
                "tail_bytes": TAIL_BYTES,
                "max_lines": MAX_LINES,
            },
        }
    except Exception as e:
        return {"status": "error", "report": str(e), "meta": {"path": str(_ERROR_PATH)}}

# download data agent
def _round_ohlc(df) -> pd.DataFrame:
    for c in ("open", "high", "low", "close"):
        if c in df.columns:
            df[c] = df[c].round(4)
    return df

def _get_tv_hist(tv, ticker, exchange, interval):
    if interval == "D":
        return tv.get_hist(symbol=ticker, exchange=exchange, interval=Interval.in_daily, n_bars=10_000_000)
    if interval == "m1":
        return tv.get_hist(symbol=ticker, exchange=exchange, interval=Interval.in_1_minute, extended_session=True, n_bars=10_000_000)
    return None

def _cleaning_df(df, ticker, date_format) -> pd.DataFrame:
    df = df.reset_index().rename(columns={"datetime": "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.strftime(date_format)
    if "symbol" in df.columns:
        df["exchange"] = df["symbol"].str.split(":").str[0]
        df = df.drop(columns=["symbol"])
    if "volume" in df.columns:
        df["volume"] = df["volume"].astype("int64")
    df["ticker"] = ticker
    return df


def _download_data_tv(ticker, date, out_dir = "./t0_missing_tickers", tool_context=None) -> Dict[str, Any]:
    """
    Download daily + m1 data for one ticker/date, save CSVs, return dict result.
    Retries each exchange up to 5 times.
    """
    tv = TvDatafeed()
    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    EXCHANGES = ["NASDAQ", "AMEX", "NYSE"]
    m1_df, daily_df, used_exchg = None, None, None

    for attempt in range(5):  # max 5 retries
        for exch in EXCHANGES:
            try:
                m1_raw = _get_tv_hist(tv, ticker, exch, "m1")
                d_raw  = _get_tv_hist(tv, ticker, exch, "D")
                if (m1_raw is None or m1_raw.empty) or (d_raw is None or d_raw.empty):
                    print(f"[{ticker}] attempt {attempt+1}: no data on {exch}")
                    continue

                m1_df    = _cleaning_df(m1_raw, ticker, "%Y-%m-%d %H:%M:%S")
                daily_df = _cleaning_df(d_raw,  ticker, "%Y-%m-%d")
                used_exchg = exch
                break
            except Exception as e:
                print(f"[{ticker}] attempt {attempt+1} on {exch} failed: {e}")
                continue

        if m1_df is not None and daily_df is not None:
            break

    if m1_df is None or daily_df is None:
        return {"ticker": ticker, "date": date, "status": "not_found"}

    # trim & round
    daily_df["spike_date"] = date
    daily_df = _round_ohlc(daily_df).query("date <= spike_date").copy()

    m1_df["date"] = pd.to_datetime(m1_df["date"])
    m1_df["extract_date"] = m1_df["date"].dt.strftime("%Y-%m-%d")
    m1_df = _round_ohlc(m1_df.query("extract_date == @date").copy())

    # stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{ticker}_{date}"

    m1_file, d_file = None, None
    if not m1_df.empty:
        m1_file = outp / f"{base}_m1.csv"
        m1_df.to_csv(m1_file, index=False)
    if not daily_df.empty:
        d_file = outp / f"{base}_daily.csv"
        daily_df.to_csv(d_file, index=False)

    return {
        "ticker": ticker, "date": date, "exchange": used_exchg,
        "m1_file": str(m1_file) if m1_file else None,
        "daily_file": str(d_file) if d_file else None,
        "m1_rows": len(m1_df), "daily_rows": len(daily_df),
        "status": "ok" if (len(m1_df) or len(daily_df)) else "empty",
    }

# ----------------- session-driven wrapper -----------------
def download_missing_batch(tool_context=None) -> Dict[str, Any]:
    """
    Session-driven batch: read 'todays_missing_tickers', process sequentially.
    If no tickers: return message.
    """
    payload = tool_context.state.get("todays_missing_tickers", {"missing_tickers": []})
    tickers: List[Dict[str, str]] = payload.get("missing_tickers", [])

    if not tickers:
        return {"message": "No missing tickers today."}

    results = []
    for item in tickers:
        ticker = str(item.get("ticker", "")).upper().strip()
        date   = str(item.get("date", "")).strip()
        if not ticker or not date:
            continue

        res = _download_data_tv(ticker, date, tool_context=tool_context)
        results.append(res)

    # write summary CSV
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outp = Path("./t0_missing_tickers")
    summary_file = outp / f"missing_ticker_summary_{stamp}.csv"
    pd.DataFrame(results).to_csv(summary_file, index=False)

    tool_context.state["last_download_result"] = results
    tool_context.state["last_download_csv"] = str(summary_file)

    return {"results": results, "summary_csv": str(summary_file)}
