# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.async.base.exchange import Exchange
import hashlib
import math
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import AuthenticationError


class exx (Exchange):

    def describe(self):
        return self.deep_extend(super(exx, self).describe(), {
            'id': 'exx',
            'name': 'EXX',
            'countries': 'CN',
            'rateLimit': 1000 / 10,
            'has': {
                'fetchTickers': True,
                'fetchOpenOrders': True,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/37770292-fbf613d0-2de4-11e8-9f79-f2dc451b8ccb.jpg',
                'api': {
                    'public': 'https://api.exx.com/data/v1',
                    'private': 'https://trade.exx.com/api',
                },
                'www': 'https://www.exx.com/',
                'doc': 'https://www.exx.com/help/restApi',
                'fees': 'https://www.exx.com/help/rate',
            },
            'api': {
                'public': {
                    'get': [
                        'markets',
                        'tickers',
                        'ticker',
                        'depth',
                        'trades',
                    ],
                },
                'private': {
                    'get': [
                        'order',
                        'cancel',
                        'getOrder',
                        'getOpenOrders',
                        'getBalance',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'maker': 0.1 / 100,
                    'taker': 0.1 / 100,
                },
                'funding': {
                    'withdraw': {
                        'BCC': 0.0003,
                        'BCD': 0.0,
                        'BOT': 10.0,
                        'BTC': 0.001,
                        'BTG': 0.0,
                        'BTM': 25.0,
                        'BTS': 3.0,
                        'EOS': 1.0,
                        'ETC': 0.01,
                        'ETH': 0.01,
                        'ETP': 0.012,
                        'HPY': 0.0,
                        'HSR': 0.001,
                        'INK': 20.0,
                        'LTC': 0.005,
                        'MCO': 0.6,
                        'MONA': 0.01,
                        'QASH': 5.0,
                        'QCASH': 5.0,
                        'QTUM': 0.01,
                        'USDT': 5.0,
                    },
                },
            },
        })

    async def fetch_markets(self):
        markets = await self.publicGetMarkets()
        ids = list(markets.keys())
        result = []
        for i in range(0, len(ids)):
            id = ids[i]
            market = markets[id]
            baseId, quoteId = id.split('_')
            upper = id.upper()
            base, quote = upper.split('_')
            base = self.common_currency_code(base)
            quote = self.common_currency_code(quote)
            symbol = base + '/' + quote
            active = market['isOpen'] is True
            precision = {
                'amount': int(market['amountScale']),
                'price': int(market['priceScale']),
            }
            lot = math.pow(10, -precision['amount'])
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'active': active,
                'lot': lot,
                'precision': precision,
                'limits': {
                    'amount': {
                        'min': lot,
                        'max': math.pow(10, precision['amount']),
                    },
                    'price': {
                        'min': math.pow(10, -precision['price']),
                        'max': math.pow(10, precision['price']),
                    },
                    'cost': {
                        'min': None,
                        'max': None,
                    },
                },
                'info': market,
            })
        return result

    def parse_ticker(self, ticker, market=None):
        symbol = market['symbol']
        timestamp = int(ticker['date'])
        ticker = ticker['ticker']
        last = float(ticker['last'])
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': float(ticker['high']),
            'low': float(ticker['low']),
            'bid': float(ticker['buy']),
            'bidVolume': None,
            'ask': float(ticker['sell']),
            'askVolume': None,
            'vwap': None,
            'open': None,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': float(ticker['riseRate']),
            'percentage': None,
            'average': None,
            'baseVolume': float(ticker['vol']),
            'quoteVolume': None,
            'info': ticker,
        }

    async def fetch_ticker(self, symbol, params={}):
        await self.load_markets()
        market = self.market(symbol)
        ticker = await self.publicGetTicker(self.extend({
            'currency': market['id'],
        }, params))
        return self.parse_ticker(ticker, market)

    async def fetch_tickers(self, symbols=None, params={}):
        await self.load_markets()
        tickers = await self.publicGetTickers(params)
        result = {}
        timestamp = self.milliseconds()
        ids = list(tickers.keys())
        for i in range(0, len(ids)):
            id = ids[i]
            if not(id in list(self.marketsById.keys())):
                continue
            market = self.marketsById[id]
            symbol = market['symbol']
            ticker = {
                'date': timestamp,
                'ticker': tickers[id],
            }
            result[symbol] = self.parse_ticker(ticker, market)
        return result

    async def fetch_order_book(self, symbol, limit=None, params={}):
        await self.load_markets()
        orderbook = await self.publicGetDepth(self.extend({
            'currency': self.market_id(symbol),
        }, params))
        return self.parse_order_book(orderbook, orderbook['timestamp'])

    def parse_trade(self, trade, market=None):
        timestamp = trade['date'] * 1000
        price = float(trade['price'])
        amount = float(trade['amount'])
        symbol = market['symbol']
        cost = self.cost_to_precision(symbol, price * amount)
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'id': self.safe_string(trade, 'tid'),
            'order': None,
            'type': 'limit',
            'side': trade['type'],
            'price': price,
            'amount': amount,
            'cost': cost,
            'fee': None,
            'info': trade,
        }

    async def fetch_trades(self, symbol, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        trades = await self.publicGetTrades(self.extend({
            'currency': market['id'],
        }, params))
        return self.parse_trades(trades, market, since, limit)

    async def fetch_balance(self, params={}):
        await self.load_markets()
        balances = await self.privateGetGetBalance(params)
        result = {'info': balances}
        balances = balances['funds']
        currencies = list(balances.keys())
        for i in range(0, len(currencies)):
            id = currencies[i]
            balance = balances[id]
            currency = self.common_currency_code(id)
            account = {
                'free': float(balance['balance']),
                'used': float(balance['freeze']),
                'total': float(balance['total']),
            }
            result[currency] = account
        return self.parse_balance(result)

    def parse_order(self, order, market=None):
        symbol = market['symbol']
        timestamp = int(order['trade_date'])
        price = float(order['price'])
        cost = self.safe_float(order, 'trade_money')
        amount = self.safe_float(order, 'total_amount')
        filled = self.safe_float(order, 'trade_amount', 0.0)
        remaining = self.amount_to_precision(symbol, amount - filled)
        status = self.safe_integer(order, 'status')
        if status == 1:
            status = 'canceled'
        elif status == 2:
            status = 'closed'
        else:
            status = 'open'
        fee = None
        if 'fees' in order:
            fee = {
                'cost': self.safe_float(order, 'fees'),
                'currency': market['quote'],
            }
        return {
            'id': self.safe_string(order, 'id'),
            'datetime': self.iso8601(timestamp),
            'timestamp': timestamp,
            'status': 'open',
            'symbol': symbol,
            'type': 'limit',
            'side': order['type'],
            'price': price,
            'cost': cost,
            'amount': amount,
            'filled': filled,
            'remaining': remaining,
            'trades': None,
            'fee': fee,
            'info': order,
        }

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        response = await self.privateGetOrder(self.extend({
            'currency': market['id'],
            'type': side,
            'price': price,
            'amount': amount,
        }, params))
        id = response['id']
        order = self.parse_order({
            'id': id,
            'trade_date': self.milliseconds(),
            'total_amount': amount,
            'price': price,
            'type': side,
            'info': response,
        }, market)
        self.orders[id] = order
        return order

    async def cancel_order(self, id, symbol=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        result = await self.privateGetCancel(self.extend({
            'id': id,
            'currency': market['id'],
        }, params))
        return result

    async def fetch_order(self, id, symbol=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        order = await self.privateGetGetOrder(self.extend({
            'id': id,
            'currency': market['id'],
        }, params))
        return self.parse_order(order, market)

    async def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        orders = await self.privateGetOpenOrders(self.extend({
            'currency': market['id'],
        }, params))
        return self.parse_orders(orders, market, since, limit)

    def nonce(self):
        return self.milliseconds()

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'][api] + '/' + path
        if api == 'public':
            if params:
                url += '?' + self.urlencode(params)
        else:
            self.check_required_credentials()
            query = self.urlencode(self.keysort(self.extend({
                'accesskey': self.apiKey,
                'nonce': self.nonce(),
            }, params)))
            signature = self.hmac(self.encode(query), self.encode(self.secret), hashlib.sha512)
            url += '?' + query + '&signature=' + signature
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    async def request(self, path, api='public', method='GET', params={}, headers=None, body=None):
        response = await self.fetch2(path, api, method, params, headers, body)
        code = self.safe_integer(response, 'code')
        message = self.safe_string(response, 'message')
        if code and code != 100 and message:
            if code == 103:
                raise AuthenticationError(message)
            raise ExchangeError(message)
        return response
