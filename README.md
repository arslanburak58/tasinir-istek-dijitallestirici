# Taşınır İstek Belgesi Dijitalleştirici

El yazısı "Taşınır İstek Belgesi" fotoğraflarından köy, malzeme, miktar ve
ölçü birimini Vision LLM ile çıkarıp, şablona sadık, **köy başına ayrı sekmeli**
tek bir Excel üretir.

## Kurulum

```bash
pip install -r requirements.txt

# API anahtarını gir
cp .env.example .env
#  .env içine ANTHROPIC_API_KEY=... yaz

# Tek seferlik: temiz şablonu ve köy listesini üret
python scripts/build_template.py
```

`build_template.py`, `~/Downloads/taşınır istek belgesi.xlsx` kaynağından
`templates/bos_sablon.xlsx` (temiz tek form) ve `data/koy_listesi.csv`
(375 köy) üretir. Kaynak yolu `.env` içindeki `SOURCE_XLSX` ile değiştirilebilir.

## Çalıştırma

```bash
streamlit run app.py
```

Akış: **fotoğrafları yükle → çıkar → tablo üzerinde düzelt → köy eşleştirmesini
onayla → tarih onayı (varsayılan bugün) → Excel oluştur → indir.** Onaysız Excel
üretilmez; her çalıştırma sıfırdan yeni bir dosya yazar.

## Testler

```bash
pytest -q
```

## Mimari

| Dosya | Sorumluluk |
|-------|-----------|
| `config.py` | Tüm varsayılanlar (model, KODU, birim, footer isimleri, eşikler) |
| `core/schema.py` | Pydantic `Kalem`/`Tutanak` + tool-use JSON şeması |
| `core/vision.py` | Anthropic Vision + tool use, opus fallback |
| `core/normalize.py` | rapidfuzz köy snap, birim normalize, köy bazında toplama |
| `core/excel_writer.py` | openpyxl ile şablon klonlama + hücre haritası (pandas yok) |
| `app.py` | Streamlit arayüzü (yalnızca UI) |
| `scripts/build_template.py` | Tek seferlik temiz şablon + köy listesi üretimi |

### Önemli kurallar
- Excel yazımında **pandas yok**; sadece `openpyxl` + `copy_worksheet`.
- Kaynak dosyanın veri alanı düzensiz olduğu için **temiz şablon** türetilir:
  başlık bandı korunur, veri alanı r7'den 25 satırlık düzenli grid olur,
  footer config'ten basılır (Kıvanç AKTAN çıkarıldı, **Mevlüt DUMAN** eklendi).
- Hücre haritası: `A`=sıra, `B`=KODU, `C:D`=`{koy}\n{malzeme}` (wrap), `E`=birim,
  `F`=miktar, `G`=boş. 25 kalemi aşan köy → ikinci sayfa "KöyAdı 2".
