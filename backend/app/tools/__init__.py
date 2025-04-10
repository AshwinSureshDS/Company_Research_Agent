# backend/app/tools/__init__.py
from .serper import search_company
from .news import get_company_news
from .wiki import get_company_wiki
from .jina_reader import extract_article_content

# Update your tool functions to use the decorator pattern
from agno.tools import tool

@tool(name="search_company", description="Search for general information about a company")
def search_company_wrapper(company_name: str):
    return search_company(company_name)

@tool(name="get_company_news", description="Get the latest news articles about a company")
def get_company_news_wrapper(company_name: str, page_size: int = 5):
    return get_company_news(company_name, page_size)

@tool(name="get_company_wiki", description="Get Wikipedia information about a company")
def get_company_wiki_wrapper(company_name: str):
    return get_company_wiki(company_name)

@tool(name="extract_article_content", description="Extract the content from a news article URL")
def extract_article_content_wrapper(url: str):
    return extract_article_content(url)