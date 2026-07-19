"""
AFAD Acil Toplanma Alanı Scraper

e-Devlet üzerindeki "Afet ve Acil Durum Toplanma Alanı Sorgulama" hizmetinden
(https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama)
toplanma alanı verilerini çeker.

Hizmetin güncel (2026) akışı:
  1. GET  ?bolge=Secimi                 -> sayfadaki data-token + oturum çerezleri
  2. POST ?bolge=Secimi&submit          -> ilKodu=X ile ilçeler, ilceKodu=X ile
                                           mahalleler, mahalleKodu=X ile sokaklar (JSON)
  3. POST ?bolge=Secimi&submit (form)   -> btn=Sorgula ile 302 sonrası harita sayfası;
                                           HTML içinde "toplanmaAlanlari = [GeoJSON]"
  4. POST ?submit                       -> islem=getAlanlarForNokta&lat=..&lng=.. ile
                                           noktaya en yakın toplanma alanları (JSON)
"""

import json
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import requests


class AFADScraperError(Exception):
    """Scraper'a özgü hatalar için temel sınıf."""


class AFADScraper:
    """e-Devlet AFAD toplanma alanı sorgulama API'sine erişim sağlar.

    Birden fazla thread tarafından paylaşılabilir; token yenileme ve istek
    hızı sınırlama kilitlerle korunur.
    """

    BASE_URL = "https://www.turkiye.gov.tr"
    SERVICE_PATH = "/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama"
    SERVICE_URL = f"{BASE_URL}{SERVICE_PATH}"
    REGION_URL = f"{SERVICE_URL}?bolge=Secimi"

    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        timeout: float = 25.0,
        max_retries: int = 4,
        backoff: float = 10.0,
        min_interval: float = 0.25,
    ) -> None:
        """
        Args:
            timeout: Tek bir HTTP isteği için saniye cinsinden zaman aşımı.
            max_retries: Bağlantı kopması/WAF engeli durumunda deneme sayısı.
            backoff: Denemeler arası temel bekleme süresi (saniye, lineer artar).
            min_interval: Ardışık iki istek arasındaki en az süre (saniye).
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.min_interval = min_interval

        self._token_lock = threading.Lock()
        self._throttle_lock = threading.Lock()
        self._last_request = 0.0

        self.session: requests.Session
        self.token: str
        self._new_session()

    # ------------------------------------------------------------------ #
    # Oturum ve token yönetimi
    # ------------------------------------------------------------------ #

    def _new_session(self) -> None:
        """Yeni bir oturum açar ve token alır (WAF engellerinden kurtulmak için)."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.USER_AGENT,
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self.token = self._fetch_token()

    def _fetch_token(self) -> str:
        response = self.session.get(self.REGION_URL, timeout=self.timeout)
        response.raise_for_status()
        match = re.search(r'data-token="([^"]*)"', response.text)
        if not match:
            raise AFADScraperError("Kimlik doğrulama jetonu sayfada bulunamadı")
        return match.group(1)

    def refresh_token(self) -> None:
        """Token'ı yeniler; eşzamanlı çağrılarda tek yenileme yapılır."""
        with self._token_lock:
            self.token = self._fetch_token()

    # ------------------------------------------------------------------ #
    # HTTP katmanı
    # ------------------------------------------------------------------ #

    def _throttle(self) -> None:
        """İstekler arasında en az `min_interval` saniye olmasını sağlar."""
        with self._throttle_lock:
            wait = self._last_request + self.min_interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()

    def _post(
        self,
        url: str,
        body: str,
        extra_headers: Optional[Dict[str, str]] = None,
        allow_redirects: bool = False,
    ) -> requests.Response:
        """POST isteği atar; bağlantı kopmalarında oturumu tazeleyip yeniden dener.

        e-Devlet'in önündeki WAF, şüpheli bulduğu istekleri yanıt vermeden
        kapatıyor (RemoteDisconnected). Bu durumda bekleyip yeni oturum +
        yeni token ile devam etmek gerekiyor.
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": self.BASE_URL,
            **(extra_headers or {}),
        }

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            self._throttle()
            try:
                return self.session.post(
                    url,
                    data=body.encode("utf-8"),
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=allow_redirects,
                )
            except requests.RequestException as error:
                last_error = error
                time.sleep(self.backoff * (attempt + 1))
                with self._token_lock:
                    try:
                        self._new_session()
                    except requests.RequestException:
                        pass  # bir sonraki turda tekrar denenecek

        raise AFADScraperError(
            f"{self.max_retries} denemeye rağmen istek tamamlanamadı: {last_error}"
        )

    def _form_body(self, params: Dict[str, Any]) -> str:
        # Token, sitedeki JS ile aynı şekilde ham (URL-encode edilmeden) gönderiliyor.
        body = f"token={self.token}&ajax=1&pn={self.SERVICE_PATH}"
        for key, value in params.items():
            body += f"&{key}={quote(str(value))}"
        return body

    def _ajax(
        self,
        params: Dict[str, Any],
        url: Optional[str] = None,
        referer: Optional[str] = None,
    ) -> Dict[str, Any]:
        """AJAX uç noktasına istek atıp JSON yanıtı döndürür.

        Yanıt JSON değilse token süresi dolmuş demektir; token yenilenip
        sınırlı sayıda tekrar denenir. (Bazı uç noktalar JSON gövdeyi
        text/html içerik türüyle döndürdüğünden Content-Type'a bakılmaz.)
        """
        url = url or f"{self.REGION_URL}&submit"
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": referer or self.REGION_URL,
        }

        for _ in range(3):
            response = self._post(url, self._form_body(params), headers)
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                self.refresh_token()

        raise AFADScraperError(f"API geçerli bir JSON yanıtı döndürmedi: {params}")

    # ------------------------------------------------------------------ #
    # Genel API
    # ------------------------------------------------------------------ #

    def _combo(self, param: str, value: Any) -> List[Dict[str, Any]]:
        payload = self._ajax({param: value})
        try:
            return payload["data"]["dataArr"]
        except (KeyError, TypeError):
            raise AFADScraperError(f"Beklenmeyen yanıt formatı ({param}={value}): {payload}")

    def get_districts(self, il_code: int) -> List[Dict[str, Any]]:
        """Bir ilin ilçelerini döndürür: [{'id': .., 'name': ..}, ...]"""
        return self._combo("ilKodu", il_code)

    def get_neighborhoods(self, district_code: int) -> List[Dict[str, Any]]:
        """Bir ilçenin mahalle/köylerini döndürür."""
        return self._combo("ilceKodu", district_code)

    def get_streets(self, neighborhood_code: int) -> List[Dict[str, Any]]:
        """Bir mahallenin cadde/sokaklarını döndürür (id'ler artık 0 dönüyor)."""
        return self._combo("mahalleKodu", neighborhood_code)

    def get_neighborhood_polygons(
        self, il_code: int, district_code: int, neighborhood_code: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Mahalle sınır poligonlarını (GeoJSON Feature listesi) döndürür.

        Form gönderimi 302 ile harita sayfasına yönlendirir; oradaki
        "toplanmaAlanlari = [...]" değişkeni ayrıştırılır. Mahalle için
        tanımlı alan yoksa None döner.
        """
        headers = {"Referer": self.REGION_URL}

        for _ in range(3):
            body = (
                f"ilKodu={il_code}&ilceKodu={district_code}"
                f"&mahalleKodu={neighborhood_code}&sokakKodu="
                f"&token={self.token}&btn=Sorgula"
            )
            response = self._post(
                f"{self.REGION_URL}&submit", body, headers, allow_redirects=True
            )
            match = re.search(r"toplanmaAlanlari = (.*);", response.text)
            if match:
                if match.group(1) == "null":
                    return None
                areas = json.loads(match.group(1))
                return areas or None
            # Değişken yoksa muhtemelen token geçersizdi; yenileyip tekrar dene.
            self.refresh_token()

        raise AFADScraperError(
            f"Toplanma alanı sayfası ayrıştırılamadı "
            f"(il={il_code}, ilçe={district_code}, mahalle={neighborhood_code})"
        )

    def query_point(self, lat: float, lng: float) -> Optional[List[Dict[str, Any]]]:
        """Bir koordinata hizmet veren toplanma alanlarını (Feature listesi) döndürür."""
        payload = self._ajax(
            {"islem": "getAlanlarForNokta", "lat": lat, "lng": lng},
            url=f"{self.SERVICE_URL}?submit",
            referer=self.SERVICE_URL,
        )
        # Kapsama dışı noktalar için API JSON null döndürebiliyor.
        if not isinstance(payload, dict):
            return None
        return payload.get("features")

    def get_gathering_areas(
        self, il_code: int, district_code: int, neighborhood_code: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Bir mahalleye hizmet veren toplanma alanlarını toplar.

        Mahalle sınır poligonunun uç noktaları ve merkezi için nokta sorgusu
        yapılır (mahalle başına en fazla 5 sorgu); sonuçlar alan id'sine göre
        tekilleştirilir. Mahalle için veri yoksa None döner.
        """
        polygons = self.get_neighborhood_polygons(il_code, district_code, neighborhood_code)
        if not polygons:
            return None

        try:
            coordinates = polygons[0]["geometry"]["coordinates"]
        except (KeyError, IndexError, TypeError):
            return None

        areas_by_id: Dict[Any, Dict[str, Any]] = {}
        for lng, lat in self._extract_significant_vertices(coordinates):
            features = self.query_point(lat=lat, lng=lng)
            for feature in features or []:
                area_id = (feature.get("properties") or {}).get("id")
                areas_by_id.setdefault(area_id, feature)

        return list(areas_by_id.values()) or None

    # ------------------------------------------------------------------ #
    # Yardımcılar
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_significant_vertices(polygon: List) -> List[Tuple[float, float]]:
        """Poligonu temsil eden az sayıda nokta seçer: 4 uç nokta + merkez.

        Her köşe için ayrı sorgu atmak yerine alanın uç noktaları ve merkezi
        ile yetinerek istek sayısı azaltılır.
        """
        points = polygon[0]
        if len(points) < 6:
            return [tuple(p[:2]) for p in points]

        extremes = [
            min(points, key=lambda p: p[0]),
            max(points, key=lambda p: p[0]),
            min(points, key=lambda p: p[1]),
            max(points, key=lambda p: p[1]),
        ]
        center = (
            sum(p[0] for p in extremes) / 4,
            sum(p[1] for p in extremes) / 4,
        )
        return [tuple(p[:2]) for p in extremes] + [center]


if __name__ == "__main__":
    scraper = AFADScraper()
    print(f"Token alındı: {scraper.token[:12]}...")
    districts = scraper.get_districts(1)
    print(f"Adana ilçeleri ({len(districts)}): {[d['name'] for d in districts[:5]]}...")
