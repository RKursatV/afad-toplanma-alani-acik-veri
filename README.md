# Afad Toplanma Alanı Açık Veri
https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama adresindeki veri kaynağına ihtiyaç duyan uygulamaların daha hızlı geliştirilmesine olanak sağlamak için ortaya çıkartılmış bir script. Veriler il başına bir JSON ve bir GeoJSON dosyası olarak `/iller` klasörü altında yayınlanmaktadır. JSON formatındaki değişiklik ihtiyaçlarınız için scripte müdahale edebilir ya da doğrudan [bana](https://t.me/z4r4r) ulaşabilirsiniz.

Toplanma bölgeleri her bir mahalle için en fazla beş adet olacak şekilde derlenmiş olup toplanma bölgelerinin seçimi için ilgili mahalle sınırlarının en uzak dört noktası ve merkez konumu baz alınmıştır.

## Kullanım

```bash
pip install -r requirements.txt

python collect.py                        # cities.json'daki tüm iller (mevcut dosyalar atlanır)
python collect.py --only Hatay,Adana     # sadece belirtilen iller
python collect.py --force                # mevcut il dosyalarının üzerine yaz
python collect.py --workers 2            # paralel istek sayısını düşür
```

İl başına iki dosya üretilir: `iller/<İl>.json` (aşağıdaki v2 şeması) ve `iller/<İl>.geojson` (toplanma alanlarının poligon geometrileriyle birlikte standart FeatureCollection — QGIS, Leaflet, kepler.gl vb. araçlara doğrudan yüklenebilir). İlerleme `collection.log` dosyasına yazılır. e-Devlet'in önündeki güvenlik duvarı yoğun istekleri zaman zaman engellediğinden istekler otomatik olarak yavaşlatılıp yeniden denenir; toplama işlemi bu nedenle uzun sürebilir.

## JSON şeması (v2)

```jsonc
{
  "sema": 2,
  "kaynak": "https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama",
  "toplanmaTarihi": "2026-07-18T21:30:00+03:00",
  "il": { "id": 1, "ad": "Adana" },
  "ilceler": [
    {
      "id": 1757,
      "ad": "ALADAĞ",
      "mahalleler": [
        {
          "id": 176887,
          "ad": "AKÖREN",
          "sokaklar": ["AKDERE", "AKÖREN  KÜME EVLERİ", "..."],
          "toplanmaAlanlari": [151580311, 59185333, 151580314]
        }
      ]
    }
  ],
  "alanlar": {
    "151580311": {
      "ad": "C TİPİ MESİRE ALANI DİNLENME VE OYUN PARKI",
      "tabelaKod": "1-1757-251-4",
      "adres": "SİNANPAŞA MAH. AGKA KİSE KÜME EVLERİ NO:34",
      "il": "ADANA",
      "ilce": "ALADAĞ",
      "mahalle": "SİNANPAŞA",
      "sokak": "AĞCA KİSE",
      "enlem": 37.54400884673552,
      "boylam": 35.40526642666356,
      "geometri": { "type": "Polygon", "coordinates": [ "..." ] }
    }
  }
}
```

- Mahalledeki `toplanmaAlanlari` listesi, il seviyesindeki `alanlar` sözlüğüne id ile referans verir; aynı alan birden çok mahalleye hizmet veriyorsa tek bir kez saklanır.
- `geometri`, alanın sınır poligonunu GeoJSON geometrisi olarak içerir; `enlem`/`boylam` alanın merkez noktasıdır.
- Eski (v1) şemadaki `sokakId` alanları kaldırılmıştır: e-Devlet hizmet sayfası yenilendiği için sokak id'leri kaynak tarafından artık `0` olarak dönmektedir, sokaklar yalnızca ad listesi olarak saklanır.

> **Uyarı:** v2 şeması v1 ile geriye dönük uyumlu değildir. `iller/` altındaki eski v1 dosyaları, iller yeniden toplandıkça v2 formatıyla değiştirilecektir; v1 formatına ihtiyaç duyanlar git geçmişinden erişebilir.

Katkıda bulunmak için pull request açabilir, hata bildirimleriniz için issue oluşturabilirsiniz.
