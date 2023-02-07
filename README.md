# Afad Toplanma Alanı Açık Veri
https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama adresindeki veri kaynağına ihtiyaç duyan uygulamaların daha hızlı geliştirilmesine olanak sağlamak için çok kısa sürede ortaya çıkartılmış bir script. Kahramanmaraş merkezli deprem bölgesi verileri halihazırda çekilmiş/çekiliyor olup `/iller` klasörü altında yayınlanmaktadır. JSON formatındaki değişiklik ihtiyaçlarınız için scripte müdahale edebilir ya da doğrudan [bana](https://t.me/z4r4r) ulaşabilirsiniz. 

Toplanma bölgeleri her bir mahalle için en fazla beş adet olacak şekilde derlenmiş olup toplanma bölgelerinin seçimi için ilgili mahalle sınırlarının en uzak dört noktası ve merkez konumu baz alınmıştır.


JSON formatı aşağıdaki yapıda kurgulanmıştır:
```
{
  "Adana": {
    "ilId": 1,
    "ilceler": {
      "ALADAĞ": {
        "ilceId": 1757,
        "mahalleler": {
          "AKÖREN": {
            "mahalleId": 176887,
            "sokaklar": {
              "AKDERE": {
                "sokakId": 84669019
              },
              "AKÖREN  KÜME EVLERİ": {
                "sokakId": 16268732
              },
              "YOĞURTOĞLU": {
                "sokakId": 63207906
              }
            },
            "toplanmaAlanlari": {
              "151429686": {
                "tesis_adi": "REYHANLI KUŞAKLI MAHALLESİ İLKOKUL BAHÇESİ TOPLANMA ALANI",
                "il_adi": "HATAY",
                "sokak_adi": "6317.",
                "acik_adres": "KUŞAKLI MAHALLESİ",
                "ilce_adi": "REYHANLI",
                "mahalle_adi": "KUŞAKLI",
                "x": 36.67477487619327,
                "y": 36.28320757330296,
                "tabela_kod": "3110-030-01",
                "id": 151429686
              },
              "151429689": {
                "tesis_adi": "REYHANLI OĞULPINAR MAHALLESİ HALISAHA TOPLANMA ALANLARI",
                "il_adi": "HATAY",
                "sokak_adi": "4071.",
                "acik_adres": "OĞULPINAR MAHALLESİ",
                "ilce_adi": "REYHANLI",
                "mahalle_adi": "OĞULPINAR",
                "x": 36.652208460814215,
                "y": 36.26685796196005,
                "tabela_kod": "3110-034-01",
                "id": 151429689
              },
              "151429693": {
                "tesis_adi": "REYHANLI CİLVEGÖZÜ MAHALLESİ TOPLANMA ALANI",
                "il_adi": "HATAY",
                "sokak_adi": "ERTUĞRUL GAZİ",
                "acik_adres": "CİLVEGÖZÜ MAHALLESİ ",
                "ilce_adi": "REYHANLI",
                "mahalle_adi": "CİLVEGÖZÜ",
                "x": 36.651081945337175,
                "y": 36.24053988956001,
                "tabela_kod": "3110-010-01",
                "id": 151429693
              }
            }
          }
        }
      }
    }
  }
}
```

Katkıda bulunmak için pull request açabilir, hata bildirimleriniz için issue oluşturabilirsiniz.
