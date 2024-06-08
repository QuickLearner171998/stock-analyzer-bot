from bs4 import BeautifulSoup
import re
import requests
import yfinance as yf
import anthropic
import warnings
import os

warnings.filterwarnings("ignore")

from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)


# Fetch stock data from Yahoo Finance
def get_stock_price(ticker, history=5):
    # time.sleep(4) #To avoid rate limit error
    if "." in ticker:
        ticker = ticker.split(".")[0]
    ticker = ticker + ".NS"
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y")
    df = df[["Close", "Volume"]]
    df.index = [str(x).split()[0] for x in list(df.index)]
    df.index.rename("Date", inplace=True)
    df = df[-history:]
    # print(df.columns)

    return df.to_string()


# Script to scrap top5 googgle news for given company name
def google_query(search_term):
    if "news" not in search_term:
        search_term = search_term + " stock news"
    url = f"https://www.google.com/search?q={search_term}&cr=countryIN"
    url = re.sub(r"\s", "+", url)
    return url


def get_recent_stock_news(company_name):
    # time.sleep(4) #To avoid rate limit error
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    }

    g_query = google_query(company_name)
    res = requests.get(g_query, headers=headers).text
    soup = BeautifulSoup(res, "html.parser")
    news = []
    for n in soup.find_all("div", "n0jPhd ynAwRc tNxQIb nDgy9d"):
        news.append(n.text)
    for n in soup.find_all("div", "IJl0Z"):
        news.append(n.text)

    if len(news) > 6:
        news = news[:4]
    else:
        news = news
    news_string = ""
    for i, n in enumerate(news):
        news_string += f"{i}. {n}\n"
    top5_news = "Recent News:\n\n" + news_string

    return top5_news


# Fetch financial statements from Yahoo Finance
def get_financial_statements(ticker):
    # time.sleep(4) #To avoid rate limit error
    if "." in ticker:
        ticker = ticker.split(".")[0]
    else:
        ticker = ticker
    ticker = ticker + ".NS"
    company = yf.Ticker(ticker)
    balance_sheet = company.balance_sheet
    if balance_sheet.shape[1] >= 3:
        balance_sheet = balance_sheet.iloc[:, :3]  # Remove 4th years data
    balance_sheet = balance_sheet.dropna(how="any")
    balance_sheet = balance_sheet.to_string()
    return balance_sheet


def get_stock_ticker(query):
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0,
        system="You are an Indian Financial expert. You have to extract the indian NSE/BSE stock ticker of the company and company name from input text. Keep the output very clean and in the format - {symbol}\\n{name}",
        messages=[{"role": "user", "content": [{"type": "text", "text": query}]}],
    )

    output = message.content[0].text

    company_ticker, company_name = output.split("\n")
    return company_name, company_ticker


def anazlyze_stock(query, detailed=False):
    company_name, ticker = get_stock_ticker(query)

    stock_data = get_stock_price(ticker, history=10)
    stock_financials = get_financial_statements(ticker)
    stock_news = get_recent_stock_news(company_name)

    available_information = f"Stock Price: {stock_data}\n\nStock Financials: {stock_financials}\n\nStock News: {stock_news}"

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0,
        system="You are an Indian Stock Market expert.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Give detail stock analysis, Use the available data and provide investment recommendation. \
             The user is fully aware about the investment risk, dont include any kind of warning like 'It is recommended to conduct further research and analysis or consult with a financial advisor before making an investment decision' in the answer \
             User question: {query} \
             You have the following information available about {company_name}. Write (5-8) pointwise investment analysis to answer user query, At the end conclude with proper explaination.Try to Give positives and negatives  : \
              {available_information} ",
                    }
                ],
            }
        ],
    )

    analysis = message.content[0].text

    if detailed:
        return company_name, stock_data, stock_financials, stock_news, analysis

    return company_name, "", "", "", analysis
