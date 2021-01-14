import hmac
import hashlib
from easyquant.exchange.util import requests
from time import sleep
from easyquant.config import config
try:
    from urllib import urlencode

# for python3
except ImportError:
    from urllib.parse import urlencode


ENDPOINT = "https://api.binance.com"

BUY = "BUY"
SELL = "SELL"

LIMIT = "LIMIT"
MARKET = "MARKET"

GTC = "GTC"
IOC = "IOC"

options = {}


def set(apiKey, secret):
    """Set API key and secret.

    Must be called before any making any signed API calls.
    """
    options["apiKey"] = apiKey
    options["secret"] = secret


def tickers():
    """Get best price/qty on the order book for all symbols."""
    data = request("GET", "/api/v3/ticker/bookTicker")
    return {d["symbol"]: {
        "bid": d["bidPrice"],
        "ask": d["askPrice"],
        "bidQty": d["bidQty"],
        "askQty": d["askQty"],
    } for d in data}


def depth(symbol, **kwargs):
    """Get order book.

    Args:
        symbol (str)
        limit (int, optional): Default 100. Must be one of 50, 20, 100, 500, 5,
            200, 10.

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = request("GET", "/api/v3/depth", params)
    return {
        "bids": data['bids'],
        "asks": data['asks']
    }


def klines(symbol, interval, **kwargs):
    """Get kline/candlestick bars for a symbol.

    Klines are uniquely identified by their open time. If startTime and endTime
    are not sent, the most recent klines are returned.

    Args:
        symbol (str)
        interval (str)
        limit (int, optional): Default 500; max 500.
        startTime (int, optional)
        endTime (int, optional)

    """
    params = {"symbol": symbol, "interval": interval}
    params.update(kwargs)
    data = request("GET", "/api/v3/klines", params)
    return data


def balances():
    """Get current balances for all symbols."""
    data = signedRequest("GET", "/api/v3/account", {})
    if 'msg' in data:
        raise ValueError("Error from exchange: {}".format(data['msg']))

    return {d["asset"]: {
        "free": d["free"],
        "locked": d["locked"],
    } for d in data.get("balances", [])}


def order(symbol, side, order_type, **kwargs):
    """Send in a new order."""

    params = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
    }
    params.update(kwargs)
    path = "/api/v3/order"
    data = signedRequest("POST", path, params)
    return data


def orderStatus(symbol, **kwargs):
    """Check an order's status.

    Args:
        symbol (str)
        orderId (int, optional)
        origClientOrderId (str, optional)
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("GET", "/api/v3/order", params)
    return data


def cancel(symbol, **kwargs):
    """Cancel an active order.

    Args:
        symbol (str)
        orderId (int, optional)
        origClientOrderId (str, optional)
        newClientOrderId (str, optional): Used to uniquely identify this
            cancel. Automatically generated by default.
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("DELETE", "/api/v3/order", params)
    return data


def openOrders(symbol, **kwargs):
    """Get all open orders on a symbol.

    Args:
        symbol (str)
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("GET", "/api/v3/openOrders", params)
    return data


def allOrders(symbol, **kwargs):
    """Get all account orders; active, canceled, or filled.

    If orderId is set, it will get orders >= that orderId. Otherwise most
    recent orders are returned.

    Args:
        symbol (str)
        orderId (int, optional)
        limit (int, optional): Default 500; max 500.
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("GET", "/api/v3/allOrders", params)
    return data


def myTrades(symbol, **kwargs):
    """Get trades for a specific account and symbol.

    Args:
        symbol (str)
        limit (int, optional): Default 500; max 500.
        fromId (int, optional): TradeId to fetch from. Default gets most recent
            trades.
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("GET", "/api/v3/myTrades", params)
    return data


def request(method, path, params=None):
    resp = requests.request(method, ENDPOINT + path, params=params)
    data = resp.json()
    # if "msg" in data:
    #     logging.error(data['msg'])
    return data


def signedRequest(method, path, params):
    if "apiKey" not in options or "secret" not in options:
        raise ValueError("Api key and secret must be set")
    timestamp = requests.get("https://api.binance.com/api/v3/time").json()['serverTime']
    query = urlencode(sorted(params.items()))
    query += "&timestamp={}".format(timestamp)
    secret = bytes(options["secret"].encode("utf-8"))
    signature = hmac.new(secret, query.encode("utf-8"),
                         hashlib.sha256).hexdigest()
    query += "&signature={}".format(signature)
    resp = requests.request(method,
                            ENDPOINT + path + "?" + query,
                            headers={"X-MBX-APIKEY": options["apiKey"]})
    data = resp.json()
    # if "msg" in data:
    #     logging.error(data['msg'])
    return data


def formatNumber(x):
    if isinstance(x, float):
        return "{:.8f}".format(x)
    else:
        return str(x)


def get_ticker(symbol):
    params = {"symbol": symbol}
    data = request("GET", "/api/v3/ticker/price", params)
    return data


def get_last_kline(symbol):
    """获取24hr 价格变动情况"""
    params = {"symbol": symbol}
    data = request("GET", "/api/v3/ticker/24hr", params)
    timestamp = int(data["closeTime"]) * 1000
    open = data["openPrice"]
    high = data["highPrice"]
    low = data["lowPrice"]
    close = data["lastPrice"]
    volume = data["volume"]
    last_kline = [timestamp, open, high, low, close, volume]
    return last_kline


def listenkeyRequest(method, path, params):
    query = urlencode(sorted(params.items()))
    resp = requests.request(method,
                            ENDPOINT + path + "?" + query,
                            headers={"X-MBX-APIKEY": options["apiKey"]})
    data = resp.json()
    return data


def post_listen_key():
    """生成 Listen Key (USER_STREAM)"""
    params = {}
    path = "/api/v3/userDataStream"
    data = listenkeyRequest("POST", path, params)
    return data