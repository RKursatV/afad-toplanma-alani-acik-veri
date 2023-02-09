from types import MappingProxyType
from typing import Final

BASE_URL: Final = "https://www.turkiye.gov.tr"
ACIL_TOPLAMA_URL: Final = "afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama"

DATA_HEADER: Final = MappingProxyType(
    {
        "Host": "www.turkiye.gov.tr",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Sec-Ch-Ua": '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Dnt": "1",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "*/*",
        "Origin": "https://www.turkiye.gov.tr",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama",
        "Accept-Language": "en-US,en;q=0.9,tr-TR;q=0.8,tr;q=0.7,da;q=0.6,so;q=0.5,hu;q=0.4,ru;q=0.3",
        "Connection": "close",
    }
)

TOKEN_HEADER: Final = MappingProxyType(
    {
        "Host": "www.turkiye.gov.tr",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Dnt": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Language": "en-US,en;q=0.9,tr-TR;q=0.8,tr;q=0.7,da;q=0.6,so;q=0.5,hu;q=0.4,ru;q=0.3",
        "Connection": "close",
    }
)


QUERY_POINT_HEADER: Final = MappingProxyType(
    {
        "Host": "www.turkiye.gov.tr",
        "Sec-Ch-Ua": '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        "Dnt": "1",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Origin": "https://www.turkiye.gov.tr",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama?harita=goster",
        "Accept-Language": "en-US,en;q=0.9,tr-TR;q=0.8,tr;q=0.7,da;q=0.6,so;q=0.5,hu;q=0.4,ru;q=0.3",
        "Connection": "close",
    }
)

MAP_HEADER: Final = MappingProxyType(
    {
        "Host": "www.turkiye.gov.tr",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Origin": "https://www.turkiye.gov.tr",
        "Dnt": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama",
        "Accept-Language": "en-US,en;q=0.9,tr-TR;q=0.8,tr;q=0.7,da;q=0.6,so;q=0.5,hu;q=0.4,ru;q=0.3",
        "Connection": "close",
    }
)
