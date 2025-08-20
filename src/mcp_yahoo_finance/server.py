import json
from typing import Any, Literal, Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np

import pandas as pd
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent, TextContent
from requests import Session
from yfinance import Ticker

from mcp_yahoo_finance.visualization import (
    generate_market_sentiment_dashboard,
    generate_portfolio_tracking,
    generate_stock_analysis
)

# Remove instantiations from here
# mcp_instance = FastMCP()
# yf_instance = YahooFinance()

class YahooFinance:
    def __init__(self, session: Session | None = None, verify: bool = True) -> None:
        self.session = session or Session()
        self.session.verify = verify

    def get_current_stock_price(self, symbol: str) -> str:
        """Get the current stock price based on stock symbol.

        Args:
            symbol (str): Stock symbol in Yahoo Finance format.
        """
        stock = Ticker(ticker=symbol, session=self.session).info
        current_price = stock.get(
            "regularMarketPrice", stock.get("currentPrice", "N/A")
        )
        return (
            f"{current_price:.4f}"
            if current_price
            else f"Couldn't fetch {symbol} current price"
        )

    def get_stock_price_by_date(self, symbol: str, date: str) -> str:
        """Get the stock price for a given stock symbol on a specific date.

        Args:
            symbol (str): Stock symbol in Yahoo Finance format.
            date (str): The date in YYYY-MM-DD format.
        """
        stock = Ticker(ticker=symbol, session=self.session)
        price = stock.history(start=date, period="1d")
        return f"{price.iloc[0]['Close']:.4f}"

    def get_stock_price_date_range(
        self, symbol: str, start_date: str, end_date: str
    ) -> str:
        """Get the stock prices for a given date range for a given stock symbol.

        Args:
            symbol (str): Stock symbol in Yahoo Finance format.
            start_date (str): The start date in YYYY-MM-DD format.
            end_date (str): The end date in YYYY-MM-DD format.
        """
        stock = Ticker(ticker=symbol, session=self.session)
        prices = stock.history(start=start_date, end=end_date)
        prices.index = prices.index.astype(str)
        return f"{prices['Close'].to_json(orient='index')}"

    def get_historical_stock_prices(
        self,
        symbol: str,
        period: Literal[
            "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
        ] = "1mo",
        interval: Literal["1d", "5d", "1wk", "1mo", "3mo"] = "1d",
    ) -> str:
        """Get historical stock prices for a given stock symbol.

        Args:
            symbol (str): Stock symbol in Yahoo Finance format.
            period (str): The period for historical data. Defaults to "1mo".
                    Valid periods: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
            interval (str): The interval beween data points. Defaults to "1d".
                    Valid intervals: "1d", "5d", "1wk", "1mo", "3mo"
        """
        stock = Ticker(ticker=symbol, session=self.session)
        prices = stock.history(period=period, interval=interval)

        if hasattr(prices.index, "date"):
            prices.index = prices.index.date.astype(str)  # type: ignore
        return f"{prices['Close'].to_json(orient='index')}"

    def get_dividends(self, symbol: str) -> str:
        """Get dividends for a given stock symbol.

        Args:
            symbol (str): Stock symbol in Yahoo Finance format.
        """
        stock = Ticker(ticker=symbol, session=self.session)
        dividends = stock.dividends

        if hasattr(dividends.index, "date"):
            dividends.index = dividends.index.date.astype(str)  # type: ignore
        return f"{dividends.to_json(orient='index')}"

    def get_income_statement(
        self, symbol: str, freq: Literal["yearly", "quarterly", "trainling"] = "yearly"
    ) -> str:
        """Get income statement for a given stock symbol.

        Args:
            symbol (str): Stock symbol in Yahoo Finance format.
            freq (str): At what frequency to get cashflow statements. Defaults to "yearly".
                    Valid freqencies: "yearly", "quarterly", "trainling"
        """
        stock = Ticker(ticker=symbol, session=self.session)
        income_statement = stock.get_income_stmt(freq=freq, pretty=True)

        if isinstance(income_statement, pd.DataFrame):
            income_statement.columns = [
                str(col.date()) for col in income_statement.columns
            ]
            return f"{income_statement.to_json()}"
        return f"{income_statement}"

    def get_cashflow(
        self, symbol: str, freq: Literal["yearly", "quarterly", "trainling"] = "yearly"
    ):
        """Get cashflow for a given stock symbol.

        Args:
            symbol (str): Stock symbol in Yahoo Finance format.
            freq (str): At what frequency to get cashflow statements. Defaults to "yearly".
                    Valid freqencies: "yearly", "quarterly", "trainling"
        """
        stock = Ticker(ticker=symbol, session=self.session)
        cashflow = stock.get_cashflow(freq=freq, pretty=True)

        if isinstance(cashflow, pd.DataFrame):
            cashflow.columns = [str(col.date()) for col in cashflow.columns]
            return f"{cashflow.to_json(indent=2)}"
        return f"{cashflow}"

    def get_earning_dates(self, symbol: str, limit: int = 12) -> str:
        """Get earning dates.


        Args:
            symbol (str): Stock symbol in Yahoo Finance format.
            limit (int): max amount of upcoming and recent earnings dates to return. Default value 12 should return next 4 quarters and last 8 quarters. Increase if more history is needed.
        """

        stock = Ticker(ticker=symbol, session=self.session)
        earning_dates = stock.get_earnings_dates(limit=limit)

        if isinstance(earning_dates, pd.DataFrame):
            earning_dates.index = earning_dates.index.date.astype(str)  # type: ignore
            return f"{earning_dates.to_json(indent=2)}"
        return f"{earning_dates}"

    def get_news(self, symbol: str) -> str:
        """Get news for a given stock symbol.

        Args:
            symbol (str): Stock symbol in Yahoo Finance format.
        """
        stock = Ticker(ticker=symbol, session=self.session)
        return json.dumps(stock.news, indent=2)
    
    def generate_market_dashboard(self, indices: str = "^GSPC,^DJI,^IXIC") -> str:
        """Generate a market sentiment dashboard with real-time index performance, fear/greed indicators.
        
        Args:
            indices (str): Comma-separated list of index symbols (default: "^GSPC,^DJI,^IXIC")
        """
        indices_list = indices.split(",")
        return generate_market_sentiment_dashboard(indices_list)

    def generate_portfolio_report(self, symbols: str = "AAPL,MSFT,GOOGL,AMZN,NVDA") -> str:
        """Generate a portfolio performance tracking report for the specified stocks.
        
        Args:
            symbols (str): Comma-separated list of stock symbols (default: "AAPL,MSFT,GOOGL,AMZN,NVDA")
        """
        symbols_list = symbols.split(",")
        return generate_portfolio_tracking(symbols_list)

    def generate_stock_technical_analysis(self, symbol: str = "TSLA") -> str:
        """Generate a deep technical analysis report for a stock, including price trends, 
        moving averages, and support/resistance levels.
        
        Args:
            symbol (str): Stock symbol in Yahoo Finance format (default: "TSLA")
        """
        return generate_stock_analysis(symbol)

    def compare_stocks(self, symbols: str) -> str:
        """Compare multiple stocks with key metrics and performance.
        
        Args:
            symbols (str): Comma-separated list of stock symbols to compare
        """
        symbols_list = symbols.split(",")
        comparison_data = {}
        
        for symbol in symbols_list:
            symbol = symbol.strip()
            try:
                stock = Ticker(ticker=symbol, session=self.session)
                info = stock.info
                
                comparison_data[symbol] = {
                    "current_price": info.get("regularMarketPrice", info.get("currentPrice", "N/A")),
                    "market_cap": info.get("marketCap", "N/A"),
                    "pe_ratio": info.get("trailingPE", "N/A"),
                    "forward_pe": info.get("forwardPE", "N/A"),
                    "price_to_book": info.get("priceToBook", "N/A"),
                    "dividend_yield": info.get("dividendYield", "N/A"),
                    "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                    "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
                    "volume": info.get("regularMarketVolume", "N/A"),
                    "avg_volume": info.get("averageVolume", "N/A"),
                    "beta": info.get("beta", "N/A"),
                    "sector": info.get("sector", "N/A"),
                    "industry": info.get("industry", "N/A")
                }
            except Exception as e:
                comparison_data[symbol] = {"error": str(e)}
        
        return json.dumps(comparison_data, indent=2)

    def get_financial_ratios(self, symbol: str) -> str:
        """Get comprehensive financial ratios and metrics for a stock.
        
        Args:
            symbol (str): Stock symbol in Yahoo Finance format
        """
        try:
            stock = Ticker(ticker=symbol, session=self.session)
            info = stock.info
            
            ratios = {
                "valuation_ratios": {
                    "pe_ratio": info.get("trailingPE", "N/A"),
                    "forward_pe": info.get("forwardPE", "N/A"),
                    "peg_ratio": info.get("pegRatio", "N/A"),
                    "price_to_book": info.get("priceToBook", "N/A"),
                    "price_to_sales": info.get("priceToSalesTrailing12Months", "N/A"),
                    "enterprise_value": info.get("enterpriseValue", "N/A"),
                    "ev_to_ebitda": info.get("enterpriseToEbitda", "N/A"),
                    "ev_to_revenue": info.get("enterpriseToRevenue", "N/A")
                },
                "profitability_ratios": {
                    "profit_margin": info.get("profitMargins", "N/A"),
                    "operating_margin": info.get("operatingMargins", "N/A"),
                    "return_on_assets": info.get("returnOnAssets", "N/A"),
                    "return_on_equity": info.get("returnOnEquity", "N/A"),
                    "gross_margin": info.get("grossMargins", "N/A")
                },
                "financial_health": {
                    "current_ratio": info.get("currentRatio", "N/A"),
                    "quick_ratio": info.get("quickRatio", "N/A"),
                    "debt_to_equity": info.get("debtToEquity", "N/A"),
                    "total_cash": info.get("totalCash", "N/A"),
                    "total_debt": info.get("totalDebt", "N/A"),
                    "free_cashflow": info.get("freeCashflow", "N/A")
                },
                "growth_metrics": {
                    "revenue_growth": info.get("revenueGrowth", "N/A"),
                    "earnings_growth": info.get("earningsGrowth", "N/A"),
                    "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth", "N/A")
                },
                "dividend_info": {
                    "dividend_yield": info.get("dividendYield", "N/A"),
                    "dividend_rate": info.get("dividendRate", "N/A"),
                    "payout_ratio": info.get("payoutRatio", "N/A"),
                    "five_year_avg_dividend_yield": info.get("fiveYearAvgDividendYield", "N/A")
                }
            }
            
            return json.dumps(ratios, indent=2)
        except Exception as e:
            return f"Error fetching financial ratios for {symbol}: {str(e)}"

    def get_crypto_price(self, symbol: str) -> str:
        """Get current cryptocurrency price using Yahoo Finance crypto symbols.
        
        Args:
            symbol (str): Crypto symbol in Yahoo Finance format (e.g., BTC-USD, ETH-USD, ADA-USD)
        """
        try:
            # Ensure symbol has -USD suffix if not provided
            if "-USD" not in symbol and symbol not in ["BTC", "ETH", "ADA", "XRP", "LTC", "BCH", "BNB", "SOL", "DOT", "DOGE"]:
                crypto_symbol = symbol
            else:
                crypto_symbol = f"{symbol}-USD" if "-" not in symbol else symbol
            
            crypto = Ticker(ticker=crypto_symbol, session=self.session)
            info = crypto.info
            
            crypto_data = {
                "symbol": crypto_symbol,
                "current_price": info.get("regularMarketPrice", info.get("currentPrice", "N/A")),
                "previous_close": info.get("previousClose", "N/A"),
                "volume": info.get("regularMarketVolume", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
                "change": info.get("regularMarketChange", "N/A"),
                "change_percent": info.get("regularMarketChangePercent", "N/A")
            }
            
            return json.dumps(crypto_data, indent=2)
        except Exception as e:
            return f"Error fetching crypto price for {symbol}: {str(e)}"

    def get_currency_rate(self, from_currency: str, to_currency: str) -> str:
        """Get currency exchange rate using Yahoo Finance.
        
        Args:
            from_currency (str): Source currency code (e.g., USD, EUR, GBP)
            to_currency (str): Target currency code (e.g., USD, EUR, GBP)
        """
        try:
            if from_currency == to_currency:
                return json.dumps({"rate": 1.0, "from": from_currency, "to": to_currency}, indent=2)
            
            symbol = f"{from_currency}{to_currency}=X"
            currency = Ticker(ticker=symbol, session=self.session)
            info = currency.info
            
            rate_data = {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "exchange_rate": info.get("regularMarketPrice", info.get("currentPrice", "N/A")),
                "previous_close": info.get("previousClose", "N/A"),
                "change": info.get("regularMarketChange", "N/A"),
                "change_percent": info.get("regularMarketChangePercent", "N/A"),
                "last_updated": info.get("regularMarketTime", "N/A")
            }
            
            return json.dumps(rate_data, indent=2)
        except Exception as e:
            return f"Error fetching currency rate {from_currency}/{to_currency}: {str(e)}"

    def get_market_summary(self) -> str:
        """Get a comprehensive market summary with major indices and metrics.
        """
        try:
            indices = ["^GSPC", "^DJI", "^IXIC", "^RUT", "^VIX"]
            market_data = {}
            
            for index in indices:
                try:
                    ticker = Ticker(ticker=index, session=self.session)
                    info = ticker.info
                    
                    name_map = {
                        "^GSPC": "S&P 500",
                        "^DJI": "Dow Jones",
                        "^IXIC": "NASDAQ",
                        "^RUT": "Russell 2000",
                        "^VIX": "VIX"
                    }
                    
                    market_data[name_map.get(index, index)] = {
                        "symbol": index,
                        "current_price": info.get("regularMarketPrice", info.get("currentPrice", "N/A")),
                        "change": info.get("regularMarketChange", "N/A"),
                        "change_percent": info.get("regularMarketChangePercent", "N/A"),
                        "previous_close": info.get("previousClose", "N/A"),
                        "volume": info.get("regularMarketVolume", "N/A")
                    }
                except Exception:
                    continue
            
            return json.dumps(market_data, indent=2)
        except Exception as e:
            return f"Error fetching market summary: {str(e)}"

    # --- PORTFOLIO MANAGEMENT SYSTEM --- #
    
    def create_portfolio(self, portfolio_data: str) -> str:
        """Create a custom portfolio with symbols and weights.
        
        Args:
            portfolio_data (str): JSON string with format: {"AAPL": 0.3, "MSFT": 0.25, "GOOGL": 0.2, "TSLA": 0.25}
        """
        try:
            weights = json.loads(portfolio_data)
            
            # Validate weights sum to 1.0 (or close to it)
            total_weight = sum(weights.values())
            if abs(total_weight - 1.0) > 0.01:
                return f"Error: Portfolio weights sum to {total_weight:.3f}, should be 1.0"
            
            portfolio_analysis = {
                "portfolio_composition": weights,
                "total_weight": total_weight,
                "number_of_holdings": len(weights),
                "analysis": {}
            }
            
            total_value = 0
            for symbol, weight in weights.items():
                try:
                    stock = Ticker(ticker=symbol, session=self.session)
                    info = stock.info
                    price = info.get("regularMarketPrice", info.get("currentPrice", 0))
                    
                    portfolio_analysis["analysis"][symbol] = {
                        "weight": weight,
                        "current_price": price,
                        "market_cap": info.get("marketCap", "N/A"),
                        "pe_ratio": info.get("trailingPE", "N/A"),
                        "sector": info.get("sector", "N/A"),
                        "beta": info.get("beta", "N/A"),
                        "dividend_yield": info.get("dividendYield", "N/A")
                    }
                    
                except Exception as e:
                    portfolio_analysis["analysis"][symbol] = {"error": str(e)}
            
            return json.dumps(portfolio_analysis, indent=2)
        except Exception as e:
            return f"Error creating portfolio: {str(e)}"

    def analyze_portfolio_performance(self, portfolio_data: str, period: str = "1y") -> str:
        """Analyze portfolio performance over a specified period.
        
        Args:
            portfolio_data (str): JSON string with portfolio weights
            period (str): Analysis period (1mo, 3mo, 6mo, 1y, 2y, 5y)
        """
        try:
            weights = json.loads(portfolio_data)
            
            # Get historical data for all symbols
            portfolio_data_hist = {}
            for symbol in weights.keys():
                try:
                    stock = Ticker(ticker=symbol, session=self.session)
                    hist = stock.history(period=period)
                    if not hist.empty:
                        portfolio_data_hist[symbol] = hist['Close']
                except Exception:
                    continue
            
            if not portfolio_data_hist:
                return "Error: No valid historical data found for portfolio symbols"
            
            # Create portfolio DataFrame
            portfolio_df = pd.DataFrame(portfolio_data_hist)
            portfolio_df = portfolio_df.dropna()
            
            # Calculate portfolio returns
            returns = portfolio_df.pct_change().dropna()
            portfolio_returns = (returns * pd.Series(weights)).sum(axis=1)
            
            # Calculate metrics
            total_return = (portfolio_df.iloc[-1] * pd.Series(weights)).sum() / (portfolio_df.iloc[0] * pd.Series(weights)).sum() - 1
            annualized_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
            volatility = portfolio_returns.std() * np.sqrt(252)
            sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
            max_drawdown = ((portfolio_df.cumsum() / portfolio_df.cumsum().cummax()) - 1).min()
            
            analysis = {
                "portfolio_weights": weights,
                "analysis_period": period,
                "performance_metrics": {
                    "total_return": f"{total_return:.4f}",
                    "annualized_return": f"{annualized_return:.4f}",
                    "volatility": f"{volatility:.4f}",
                    "sharpe_ratio": f"{sharpe_ratio:.4f}",
                    "max_drawdown": f"{max_drawdown:.4f}"
                },
                "individual_performance": {}
            }
            
            # Individual stock performance
            for symbol in weights.keys():
                if symbol in portfolio_df.columns:
                    stock_return = portfolio_df[symbol].iloc[-1] / portfolio_df[symbol].iloc[0] - 1
                    analysis["individual_performance"][symbol] = {
                        "weight": weights[symbol],
                        "total_return": f"{stock_return:.4f}",
                        "contribution": f"{stock_return * weights[symbol]:.4f}"
                    }
            
            return json.dumps(analysis, indent=2)
        except Exception as e:
            return f"Error analyzing portfolio performance: {str(e)}"

    # --- TECHNICAL INDICATORS --- #
    
    def get_technical_indicators(self, symbol: str, period: str = "6mo") -> str:
        """Calculate technical indicators (RSI, MACD, Moving Averages) for a stock.
        
        Args:
            symbol (str): Stock symbol in Yahoo Finance format
            period (str): Period for analysis (1mo, 3mo, 6mo, 1y, 2y)
        """
        try:
            stock = Ticker(ticker=symbol, session=self.session)
            hist = stock.history(period=period)
            
            if hist.empty:
                return f"No historical data found for {symbol}"
            
            # Calculate Moving Averages
            hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
            hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
            hist['EMA_12'] = hist['Close'].ewm(span=12).mean()
            hist['EMA_26'] = hist['Close'].ewm(span=26).mean()
            
            # Calculate RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            hist['RSI'] = 100 - (100 / (1 + rs))
            
            # Calculate MACD
            hist['MACD'] = hist['EMA_12'] - hist['EMA_26']
            hist['MACD_Signal'] = hist['MACD'].ewm(span=9).mean()
            hist['MACD_Histogram'] = hist['MACD'] - hist['MACD_Signal']
            
            # Get latest values
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            indicators = {
                "symbol": symbol,
                "analysis_date": str(latest.name.date()),
                "current_price": f"{latest['Close']:.2f}",
                "moving_averages": {
                    "sma_20": f"{latest['SMA_20']:.2f}" if not pd.isna(latest['SMA_20']) else "N/A",
                    "sma_50": f"{latest['SMA_50']:.2f}" if not pd.isna(latest['SMA_50']) else "N/A",
                    "ema_12": f"{latest['EMA_12']:.2f}" if not pd.isna(latest['EMA_12']) else "N/A",
                    "ema_26": f"{latest['EMA_26']:.2f}" if not pd.isna(latest['EMA_26']) else "N/A"
                },
                "rsi": {
                    "current": f"{latest['RSI']:.2f}" if not pd.isna(latest['RSI']) else "N/A",
                    "signal": "Overbought" if latest['RSI'] > 70 else "Oversold" if latest['RSI'] < 30 else "Neutral"
                },
                "macd": {
                    "macd": f"{latest['MACD']:.4f}" if not pd.isna(latest['MACD']) else "N/A",
                    "signal": f"{latest['MACD_Signal']:.4f}" if not pd.isna(latest['MACD_Signal']) else "N/A",
                    "histogram": f"{latest['MACD_Histogram']:.4f}" if not pd.isna(latest['MACD_Histogram']) else "N/A",
                    "trend": "Bullish" if latest['MACD'] > latest['MACD_Signal'] else "Bearish"
                },
                "price_position": {
                    "above_sma_20": latest['Close'] > latest['SMA_20'] if not pd.isna(latest['SMA_20']) else False,
                    "above_sma_50": latest['Close'] > latest['SMA_50'] if not pd.isna(latest['SMA_50']) else False
                }
            }
            
            return json.dumps(indicators, indent=2)
        except Exception as e:
            return f"Error calculating technical indicators for {symbol}: {str(e)}"

    # --- OPTIONS DATA --- #
    
    def get_options_chain(self, symbol: str, expiry_date: Optional[str] = None) -> str:
        """Get options chain data for a stock.
        
        Args:
            symbol (str): Stock symbol in Yahoo Finance format
            expiry_date (str, optional): Specific expiry date (YYYY-MM-DD format)
        """
        try:
            stock = Ticker(ticker=symbol, session=self.session)
            
            # Get available expiry dates
            expiry_dates = stock.options
            if not expiry_dates:
                return f"No options data available for {symbol}"
            
            if expiry_date:
                if expiry_date not in expiry_dates:
                    return f"Expiry date {expiry_date} not available. Available dates: {list(expiry_dates)}"
                selected_expiry = expiry_date
            else:
                # Use nearest expiry
                selected_expiry = expiry_dates[0]
            
            # Get options chain
            opt_chain = stock.option_chain(selected_expiry)
            
            options_data = {
                "symbol": symbol,
                "expiry_date": selected_expiry,
                "available_expiries": list(expiry_dates),
                "calls": {
                    "count": len(opt_chain.calls),
                    "data": opt_chain.calls.to_dict('records')[:10]  # Limit to 10 for readability
                },
                "puts": {
                    "count": len(opt_chain.puts),
                    "data": opt_chain.puts.to_dict('records')[:10]  # Limit to 10 for readability
                }
            }
            
            return json.dumps(options_data, indent=2, default=str)
        except Exception as e:
            return f"Error fetching options chain for {symbol}: {str(e)}"

    # --- ECONOMIC CALENDAR --- #
    
    def get_earnings_calendar(self, days_ahead: int = 30) -> str:
        """Get upcoming earnings calendar for major stocks.
        
        Args:
            days_ahead (int): Number of days to look ahead for earnings
        """
        try:
            # Major stocks to check for earnings
            major_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "CRM", "ORCL"]
            
            earnings_calendar = {
                "calendar_period": f"Next {days_ahead} days",
                "generated_date": str(datetime.now().date()),
                "earnings_events": []
            }
            
            for symbol in major_stocks:
                try:
                    stock = Ticker(ticker=symbol, session=self.session)
                    earnings = stock.get_earnings_dates(limit=4)
                    
                    if earnings is not None and not earnings.empty:
                        # Filter for upcoming earnings
                        upcoming = earnings[earnings.index >= datetime.now().date()]
                        if not upcoming.empty:
                            next_earnings = upcoming.iloc[0]
                            earnings_calendar["earnings_events"].append({
                                "symbol": symbol,
                                "earnings_date": str(upcoming.index[0]),
                                "eps_estimate": next_earnings.get("EPS Estimate", "N/A"),
                                "reported_eps": next_earnings.get("Reported EPS", "N/A"),
                                "surprise_percent": next_earnings.get("Surprise(%)", "N/A")
                            })
                except Exception:
                    continue
            
            # Sort by date
            earnings_calendar["earnings_events"].sort(key=lambda x: x["earnings_date"])
            
            return json.dumps(earnings_calendar, indent=2, default=str)
        except Exception as e:
            return f"Error fetching earnings calendar: {str(e)}"

    # --- SECTOR ETFS TRACKING --- #
    
    def get_sector_performance(self) -> str:
        """Get performance of major sector ETFs for sector rotation analysis.
        """
        try:
            sector_etfs = {
                "XLK": "Technology",
                "XLF": "Financial", 
                "XLV": "Healthcare",
                "XLE": "Energy",
                "XLI": "Industrial",
                "XLY": "Consumer Discretionary",
                "XLP": "Consumer Staples",
                "XLU": "Utilities",
                "XLB": "Materials",
                "XLRE": "Real Estate",
                "XLC": "Communication Services"
            }
            
            sector_data = {
                "analysis_date": str(datetime.now().date()),
                "sector_performance": {}
            }
            
            for etf_symbol, sector_name in sector_etfs.items():
                try:
                    etf = Ticker(ticker=etf_symbol, session=self.session)
                    info = etf.info
                    hist = etf.history(period="1mo")
                    
                    if not hist.empty:
                        month_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
                        
                        sector_data["sector_performance"][sector_name] = {
                            "symbol": etf_symbol,
                            "current_price": info.get("regularMarketPrice", info.get("currentPrice", "N/A")),
                            "change": info.get("regularMarketChange", "N/A"),
                            "change_percent": info.get("regularMarketChangePercent", "N/A"),
                            "month_return": f"{month_return:.2f}%",
                            "volume": info.get("regularMarketVolume", "N/A"),
                            "aum": info.get("totalAssets", "N/A")
                        }
                except Exception:
                    sector_data["sector_performance"][sector_name] = {
                        "symbol": etf_symbol,
                        "error": "Data unavailable"
                    }
            
            return json.dumps(sector_data, indent=2)
        except Exception as e:
            return f"Error fetching sector performance: {str(e)}"

    # --- CORRELATION ANALYSIS --- #
    
    def calculate_correlation_matrix(self, symbols: str, period: str = "1y") -> str:
        """Calculate correlation matrix for portfolio diversification analysis.
        
        Args:
            symbols (str): Comma-separated list of stock symbols
            period (str): Analysis period (1mo, 3mo, 6mo, 1y, 2y)
        """
        try:
            symbols_list = [s.strip() for s in symbols.split(",")]
            
            # Get historical data
            price_data = {}
            for symbol in symbols_list:
                try:
                    stock = Ticker(ticker=symbol, session=self.session)
                    hist = stock.history(period=period)
                    if not hist.empty:
                        price_data[symbol] = hist['Close']
                except Exception:
                    continue
            
            if len(price_data) < 2:
                return "Error: Need at least 2 valid symbols for correlation analysis"
            
            # Create DataFrame and calculate correlations
            df = pd.DataFrame(price_data).dropna()
            returns = df.pct_change().dropna()
            correlation_matrix = returns.corr()
            
            # Prepare results
            correlation_analysis = {
                "symbols": list(correlation_matrix.columns),
                "analysis_period": period,
                "correlation_matrix": correlation_matrix.to_dict(),
                "diversification_insights": {},
                "high_correlations": [],
                "low_correlations": []
            }
            
            # Find high and low correlations
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    symbol1 = correlation_matrix.columns[i]
                    symbol2 = correlation_matrix.columns[j]
                    corr_value = correlation_matrix.iloc[i, j]
                    
                    if corr_value > 0.7:
                        correlation_analysis["high_correlations"].append({
                            "pair": f"{symbol1}-{symbol2}",
                            "correlation": f"{corr_value:.3f}",
                            "note": "High correlation - limited diversification benefit"
                        })
                    elif corr_value < 0.2:
                        correlation_analysis["low_correlations"].append({
                            "pair": f"{symbol1}-{symbol2}",
                            "correlation": f"{corr_value:.3f}",
                            "note": "Low correlation - good diversification potential"
                        })
            
            return json.dumps(correlation_analysis, indent=2, default=str)
        except Exception as e:
            return f"Error calculating correlation matrix: {str(e)}"

    # --- RISK METRICS --- #
    
    def calculate_risk_metrics(self, symbols: str, period: str = "1y") -> str:
        """Calculate comprehensive risk metrics (VaR, Sharpe Ratio, Max Drawdown).
        
        Args:
            symbols (str): Comma-separated list of stock symbols
            period (str): Analysis period for risk calculation
        """
        try:
            symbols_list = [s.strip() for s in symbols.split(",")]
            
            risk_analysis = {
                "analysis_date": str(datetime.now().date()),
                "analysis_period": period,
                "individual_risk_metrics": {}
            }
            
            for symbol in symbols_list:
                try:
                    stock = Ticker(ticker=symbol, session=self.session)
                    hist = stock.history(period=period)
                    
                    if hist.empty:
                        continue
                    
                    # Calculate returns
                    returns = hist['Close'].pct_change().dropna()
                    
                    # Risk metrics calculations
                    mean_return = returns.mean() * 252  # Annualized
                    volatility = returns.std() * np.sqrt(252)  # Annualized
                    sharpe_ratio = mean_return / volatility if volatility > 0 else 0
                    
                    # VaR (5% confidence level)
                    var_5 = np.percentile(returns, 5)
                    
                    # Maximum Drawdown
                    cumulative = (1 + returns).cumprod()
                    rolling_max = cumulative.expanding().max()
                    drawdown = (cumulative - rolling_max) / rolling_max
                    max_drawdown = drawdown.min()
                    
                    # Beta calculation (vs S&P 500)
                    try:
                        sp500 = Ticker("^GSPC", session=self.session)
                        sp500_hist = sp500.history(period=period)
                        sp500_returns = sp500_hist['Close'].pct_change().dropna()
                        
                        # Align dates
                        aligned_data = pd.DataFrame({
                            'stock': returns,
                            'market': sp500_returns
                        }).dropna()
                        
                        if len(aligned_data) > 30:
                            covariance = aligned_data['stock'].cov(aligned_data['market'])
                            market_variance = aligned_data['market'].var()
                            beta = covariance / market_variance if market_variance > 0 else 0
                        else:
                            beta = "N/A"
                    except Exception:
                        beta = "N/A"
                    
                    risk_analysis["individual_risk_metrics"][symbol] = {
                        "annualized_return": f"{mean_return:.4f}",
                        "annualized_volatility": f"{volatility:.4f}",
                        "sharpe_ratio": f"{sharpe_ratio:.4f}",
                        "var_5_percent": f"{var_5:.4f}",
                        "max_drawdown": f"{max_drawdown:.4f}",
                        "beta": f"{beta:.3f}" if isinstance(beta, (int, float)) else beta,
                        "risk_level": "High" if volatility > 0.25 else "Medium" if volatility > 0.15 else "Low"
                    }
                    
                except Exception as e:
                    risk_analysis["individual_risk_metrics"][symbol] = {"error": str(e)}
            
            return json.dumps(risk_analysis, indent=2)
        except Exception as e:
            return f"Error calculating risk metrics: {str(e)}"

    # --- EARNINGS ANALYSIS --- #
    
    def analyze_earnings_impact(self, symbol: str, periods_back: int = 4) -> str:
        """Analyze stock performance around earnings announcements.
        
        Args:
            symbol (str): Stock symbol to analyze
            periods_back (int): Number of past earnings periods to analyze
        """
        try:
            stock = Ticker(ticker=symbol, session=self.session)
            
            # Get earnings dates
            earnings_dates = stock.get_earnings_dates(limit=periods_back * 2)
            if earnings_dates is None or earnings_dates.empty:
                return f"No earnings data found for {symbol}"
            
            # Get historical price data
            hist = stock.history(period="2y")
            if hist.empty:
                return f"No price data found for {symbol}"
            
            earnings_analysis = {
                "symbol": symbol,
                "analysis_date": str(datetime.now().date()),
                "earnings_impact_analysis": []
            }
            
            # Analyze each earnings date
            for earnings_date, earnings_data in earnings_dates.head(periods_back).iterrows():
                try:
                    # Get price data around earnings date
                    earnings_date_pd = pd.to_datetime(earnings_date)
                    
                    # Find the closest trading day
                    available_dates = hist.index.date
                    closest_date = min(available_dates, key=lambda x: abs((pd.to_datetime(x) - earnings_date_pd).days))
                    closest_date_idx = hist.index.get_loc(pd.to_datetime(closest_date))
                    
                    # Get prices before and after earnings
                    if closest_date_idx >= 5 and closest_date_idx < len(hist) - 5:
                        pre_earnings_price = hist.iloc[closest_date_idx - 1]['Close']
                        earnings_day_price = hist.iloc[closest_date_idx]['Close']
                        post_earnings_1d = hist.iloc[closest_date_idx + 1]['Close']
                        post_earnings_5d = hist.iloc[closest_date_idx + 5]['Close']
                        
                        # Calculate impact
                        day_of_impact = (earnings_day_price - pre_earnings_price) / pre_earnings_price
                        next_day_impact = (post_earnings_1d - pre_earnings_price) / pre_earnings_price
                        five_day_impact = (post_earnings_5d - pre_earnings_price) / pre_earnings_price
                        
                        earnings_analysis["earnings_impact_analysis"].append({
                            "earnings_date": str(earnings_date.date()),
                            "reported_eps": earnings_data.get("Reported EPS", "N/A"),
                            "eps_estimate": earnings_data.get("EPS Estimate", "N/A"),
                            "surprise_percent": earnings_data.get("Surprise(%)", "N/A"),
                            "price_impact": {
                                "day_of_earnings": f"{day_of_impact:.4f}",
                                "next_day": f"{next_day_impact:.4f}",
                                "five_days_after": f"{five_day_impact:.4f}"
                            },
                            "pre_earnings_price": f"{pre_earnings_price:.2f}",
                            "post_earnings_price_1d": f"{post_earnings_1d:.2f}"
                        })
                        
                except Exception:
                    continue
            
            # Calculate average impact
            if earnings_analysis["earnings_impact_analysis"]:
                impacts = earnings_analysis["earnings_impact_analysis"]
                avg_day_impact = np.mean([float(e["price_impact"]["day_of_earnings"]) for e in impacts])
                avg_next_day = np.mean([float(e["price_impact"]["next_day"]) for e in impacts])
                
                earnings_analysis["average_impact"] = {
                    "average_day_of_earnings": f"{avg_day_impact:.4f}",
                    "average_next_day": f"{avg_next_day:.4f}",
                    "historical_volatility": "High" if abs(avg_day_impact) > 0.05 else "Medium" if abs(avg_day_impact) > 0.02 else "Low"
                }
            
            return json.dumps(earnings_analysis, indent=2, default=str)
        except Exception as e:
            return f"Error analyzing earnings impact for {symbol}: {str(e)}"

    # --- NEWS SENTIMENT ANALYSIS --- #
    
    def analyze_news_sentiment(self, symbol: str) -> str:
        """Analyze sentiment of recent news for a stock.
        
        Args:
            symbol (str): Stock symbol to analyze news sentiment
        """
        try:
            stock = Ticker(ticker=symbol, session=self.session)
            news = stock.news
            
            if not news:
                return f"No recent news found for {symbol}"
            
            # Simple sentiment analysis based on keywords
            positive_keywords = ['growth', 'profit', 'revenue', 'beat', 'strong', 'positive', 'bullish', 'upgrade', 'buy', 'outperform']
            negative_keywords = ['loss', 'decline', 'weak', 'negative', 'bearish', 'downgrade', 'sell', 'underperform', 'concern', 'risk']
            
            sentiment_analysis = {
                "symbol": symbol,
                "analysis_date": str(datetime.now().date()),
                "news_count": len(news),
                "articles_analyzed": [],
                "overall_sentiment": {
                    "positive_articles": 0,
                    "negative_articles": 0,
                    "neutral_articles": 0
                }
            }
            
            for article in news[:10]:  # Analyze first 10 articles
                title = article.get('title', '').lower()
                summary = article.get('summary', '').lower()
                text = f"{title} {summary}"
                
                positive_score = sum(1 for word in positive_keywords if word in text)
                negative_score = sum(1 for word in negative_keywords if word in text)
                
                if positive_score > negative_score:
                    sentiment = "Positive"
                    sentiment_analysis["overall_sentiment"]["positive_articles"] += 1
                elif negative_score > positive_score:
                    sentiment = "Negative"
                    sentiment_analysis["overall_sentiment"]["negative_articles"] += 1
                else:
                    sentiment = "Neutral"
                    sentiment_analysis["overall_sentiment"]["neutral_articles"] += 1
                
                sentiment_analysis["articles_analyzed"].append({
                    "title": article.get('title', 'No title'),
                    "publisher": article.get('publisher', 'Unknown'),
                    "published_date": str(datetime.fromtimestamp(article.get('providerPublishTime', 0)).date()),
                    "sentiment": sentiment,
                    "sentiment_score": f"P:{positive_score}, N:{negative_score}",
                    "url": article.get('link', '')
                })
            
            # Calculate overall sentiment
            total_articles = len(sentiment_analysis["articles_analyzed"])
            if total_articles > 0:
                positive_ratio = sentiment_analysis["overall_sentiment"]["positive_articles"] / total_articles
                negative_ratio = sentiment_analysis["overall_sentiment"]["negative_articles"] / total_articles
                
                if positive_ratio > 0.6:
                    overall_sentiment = "Bullish"
                elif negative_ratio > 0.6:
                    overall_sentiment = "Bearish"
                else:
                    overall_sentiment = "Mixed"
                
                sentiment_analysis["sentiment_summary"] = {
                    "overall_sentiment": overall_sentiment,
                    "positive_ratio": f"{positive_ratio:.2f}",
                    "negative_ratio": f"{negative_ratio:.2f}",
                    "confidence": "High" if max(positive_ratio, negative_ratio) > 0.7 else "Medium" if max(positive_ratio, negative_ratio) > 0.5 else "Low"
                }
            
            return json.dumps(sentiment_analysis, indent=2, default=str)
        except Exception as e:
            return f"Error analyzing news sentiment for {symbol}: {str(e)}"

# Instantiate AFTER class definition
mcp_instance = FastMCP()
yf_instance = YahooFinance()

# --- Tool Definitions using FastMCP --- #

@mcp_instance.tool()
def get_current_stock_price(symbol: str) -> str:
    """Get the current stock price based on stock symbol.

    Args:
        symbol (str): Stock symbol in Yahoo Finance format.
    """
    return yf_instance.get_current_stock_price(symbol)

@mcp_instance.tool()
def get_stock_price_by_date(symbol: str, date: str) -> str:
    """Get the stock price for a given stock symbol on a specific date.

    Args:
        symbol (str): Stock symbol in Yahoo Finance format.
        date (str): The date in YYYY-MM-DD format.
    """
    return yf_instance.get_stock_price_by_date(symbol, date)

@mcp_instance.tool()
def get_stock_price_date_range(symbol: str, start_date: str, end_date: str) -> str:
    """Get the stock prices for a given date range for a given stock symbol.

    Args:
        symbol (str): Stock symbol in Yahoo Finance format.
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
    """
    return yf_instance.get_stock_price_date_range(symbol, start_date, end_date)

@mcp_instance.tool()
def get_historical_stock_prices(
    symbol: str,
    period: Literal[
        "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
    ] = "1mo",
    interval: Literal["1d", "5d", "1wk", "1mo", "3mo"] = "1d",
) -> str:
    """Get historical stock prices for a given stock symbol.

    Args:
        symbol (str): Stock symbol in Yahoo Finance format.
        period (str): The period for historical data. Defaults to "1mo".
                Valid periods: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
        interval (str): The interval beween data points. Defaults to "1d".
                Valid intervals: "1d", "5d", "1wk", "1mo", "3mo"
    """
    return yf_instance.get_historical_stock_prices(symbol, period, interval)

@mcp_instance.tool()
def get_dividends(symbol: str) -> str:
    """Get dividends for a given stock symbol.

    Args:
        symbol (str): Stock symbol in Yahoo Finance format.
    """
    return yf_instance.get_dividends(symbol)

@mcp_instance.tool()
def get_income_statement(
    symbol: str, freq: Literal["yearly", "quarterly", "trainling"] = "yearly"
) -> str:
    """Get income statement for a given stock symbol.

    Args:
        symbol (str): Stock symbol in Yahoo Finance format.
        freq (str): At what frequency to get cashflow statements. Defaults to "yearly".
                Valid freqencies: "yearly", "quarterly", "trainling"
    """
    return yf_instance.get_income_statement(symbol, freq)

@mcp_instance.tool()
def get_cashflow(
    symbol: str, freq: Literal["yearly", "quarterly", "trainling"] = "yearly"
) -> str:
    """Get cashflow for a given stock symbol.

    Args:
        symbol (str): Stock symbol in Yahoo Finance format.
        freq (str): At what frequency to get cashflow statements. Defaults to "yearly".
                Valid freqencies: "yearly", "quarterly", "trainling"
    """
    # Note: Original function didn't specify return type, assuming str
    return str(yf_instance.get_cashflow(symbol, freq))

@mcp_instance.tool()
def get_earning_dates(symbol: str, limit: int = 12) -> str:
    """Get earning dates.

    Args:
        symbol (str): Stock symbol in Yahoo Finance format.
        limit (int): max amount of upcoming and recent earnings dates to return. Default value 12 should return next 4 quarters and last 8 quarters. Increase if more history is needed.
    """
    return yf_instance.get_earning_dates(symbol, limit)

@mcp_instance.tool()
def get_news(symbol: str) -> str:
    """Get news for a given stock symbol.

    Args:
        symbol (str): Stock symbol in Yahoo Finance format.
    """
    return yf_instance.get_news(symbol)

# --- Visualization Tools (Potential adjustment needed for return type) --- #

# Note: FastMCP might handle return types differently. If images don't work,
# we might need to return ImageContent explicitly.
@mcp_instance.tool()
def generate_market_dashboard(indices: str = "^GSPC,^DJI,^IXIC") -> Any:
    """Generate a market sentiment dashboard image (base64 PNG).

    Args:
        indices (str): Comma-separated list of index symbols (default: "^GSPC,^DJI,^IXIC")
    """
    # For now, return the base64 string. May need adjustment.
    image_base64 = yf_instance.generate_market_dashboard(indices)
    # return ImageContent(type="image", image={"format": "png", "base64": image_base64})
    return image_base64

@mcp_instance.tool()
def generate_portfolio_report(symbols: str = "AAPL,MSFT,GOOGL,AMZN,NVDA") -> Any:
    """Generate a portfolio performance tracking report image (base64 PNG).

    Args:
        symbols (str): Comma-separated list of stock symbols (default: "AAPL,MSFT,GOOGL,AMZN,NVDA")
    """
    image_base64 = yf_instance.generate_portfolio_report(symbols)
    # return ImageContent(type="image", image={"format": "png", "base64": image_base64})
    return image_base64

@mcp_instance.tool()
def generate_stock_technical_analysis(symbol: str = "TSLA") -> Any:
    """Generate a deep technical analysis report image (base64 PNG).

    Args:
        symbol (str): Stock symbol in Yahoo Finance format (default: "TSLA")
    """
    image_base64 = yf_instance.generate_stock_technical_analysis(symbol)
    # return ImageContent(type="image", image={"format": "png", "base64": image_base64})
    return image_base64

# --- New Advanced Analysis Tools --- #

@mcp_instance.tool()
def compare_stocks(symbols: str) -> str:
    """Compare multiple stocks with comprehensive metrics and analysis.

    Args:
        symbols (str): Comma-separated list of stock symbols to compare
    """
    return yf_instance.compare_stocks(symbols)

@mcp_instance.tool()
def get_financial_ratios(symbol: str) -> str:
    """Get comprehensive financial ratios and metrics for detailed stock analysis.

    Args:
        symbol (str): Stock symbol in Yahoo Finance format
    """
    return yf_instance.get_financial_ratios(symbol)

@mcp_instance.tool()
def get_crypto_price(symbol: str) -> str:
    """Get current cryptocurrency price and market data.

    Args:
        symbol (str): Crypto symbol (e.g., BTC, ETH, BTC-USD, ETH-USD)
    """
    return yf_instance.get_crypto_price(symbol)

@mcp_instance.tool()
def get_currency_rate(from_currency: str, to_currency: str) -> str:
    """Get real-time currency exchange rates.

    Args:
        from_currency (str): Source currency code (e.g., USD, EUR, GBP)
        to_currency (str): Target currency code (e.g., USD, EUR, GBP)
    """
    return yf_instance.get_currency_rate(from_currency, to_currency)

@mcp_instance.tool()
def get_market_summary() -> str:
    """Get comprehensive market summary with major indices and VIX.
    """
    return yf_instance.get_market_summary()

# --- NEW ADVANCED FEATURES --- #

# Portfolio Management Tools
@mcp_instance.tool()
def create_portfolio(portfolio_data: str) -> str:
    """Create a custom portfolio with symbols and weights.
    
    Args:
        portfolio_data (str): JSON string with format: {"AAPL": 0.3, "MSFT": 0.25, "GOOGL": 0.2, "TSLA": 0.25}
    """
    return yf_instance.create_portfolio(portfolio_data)

@mcp_instance.tool()
def analyze_portfolio_performance(portfolio_data: str, period: str = "1y") -> str:
    """Analyze portfolio performance with comprehensive metrics.
    
    Args:
        portfolio_data (str): JSON string with portfolio weights
        period (str): Analysis period (1mo, 3mo, 6mo, 1y, 2y, 5y)
    """
    return yf_instance.analyze_portfolio_performance(portfolio_data, period)

# Technical Analysis Tools
@mcp_instance.tool()
def get_technical_indicators(symbol: str, period: str = "6mo") -> str:
    """Calculate technical indicators (RSI, MACD, Moving Averages) for a stock.
    
    Args:
        symbol (str): Stock symbol in Yahoo Finance format
        period (str): Period for analysis (1mo, 3mo, 6mo, 1y, 2y)
    """
    return yf_instance.get_technical_indicators(symbol, period)

# Options Trading Tools
@mcp_instance.tool()
def get_options_chain(symbol: str, expiry_date: str = None) -> str:
    """Get options chain data for a stock with calls and puts.
    
    Args:
        symbol (str): Stock symbol in Yahoo Finance format
        expiry_date (str, optional): Specific expiry date (YYYY-MM-DD format)
    """
    return yf_instance.get_options_chain(symbol, expiry_date)

# Economic Calendar Tools
@mcp_instance.tool()
def get_earnings_calendar(days_ahead: int = 30) -> str:
    """Get upcoming earnings calendar for major stocks.
    
    Args:
        days_ahead (int): Number of days to look ahead for earnings
    """
    return yf_instance.get_earnings_calendar(days_ahead)

# Sector Analysis Tools
@mcp_instance.tool()
def get_sector_performance() -> str:
    """Get performance of major sector ETFs for sector rotation analysis.
    """
    return yf_instance.get_sector_performance()

# Portfolio Optimization Tools
@mcp_instance.tool()
def calculate_correlation_matrix(symbols: str, period: str = "1y") -> str:
    """Calculate correlation matrix for portfolio diversification analysis.
    
    Args:
        symbols (str): Comma-separated list of stock symbols
        period (str): Analysis period (1mo, 3mo, 6mo, 1y, 2y)
    """
    return yf_instance.calculate_correlation_matrix(symbols, period)

# Risk Management Tools
@mcp_instance.tool()
def calculate_risk_metrics(symbols: str, period: str = "1y") -> str:
    """Calculate comprehensive risk metrics (VaR, Sharpe Ratio, Max Drawdown).
    
    Args:
        symbols (str): Comma-separated list of stock symbols
        period (str): Analysis period for risk calculation
    """
    return yf_instance.calculate_risk_metrics(symbols, period)

# Earnings Analysis Tools
@mcp_instance.tool()
def analyze_earnings_impact(symbol: str, periods_back: int = 4) -> str:
    """Analyze stock performance around earnings announcements.
    
    Args:
        symbol (str): Stock symbol to analyze
        periods_back (int): Number of past earnings periods to analyze
    """
    return yf_instance.analyze_earnings_impact(symbol, periods_back)

# News Sentiment Tools
@mcp_instance.tool()
def analyze_news_sentiment(symbol: str) -> str:
    """Analyze sentiment of recent news for a stock.
    
    Args:
        symbol (str): Stock symbol to analyze news sentiment
    """
    return yf_instance.analyze_news_sentiment(symbol)


def main():
    # Run the server using stdio transport
    mcp_instance.run(transport='stdio')
