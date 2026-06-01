# Proje: Taşınır İstek Belgesi Dijitalleştirici

## Değişmez kurallar
- Excel yazımında ASLA pandas.to_excel kullanma. Sadece openpyxl ile boş
  şablonu yükle ve sayfa klonlayarak doldur. Biçimlendirme korunmalı.
- Model adını, birim/isim varsayılanlarını, KODU varsayılanını koda gömme;
  hepsi config.py / .env içinde olsun.
- İnsan onay adımı olmadan Excel dosyası üretme. Üretim akışı:
  yükle -> Vision çıkar (her fotoğraf) -> Pydantic valide -> kullanıcı
  düzeltir/onaylar -> normalize (köy adı) -> köy bazında topla/birleştir ->
  köy başına sayfa yaz -> tek dosya. Her çalıştırma yeni dosya.
- Vision çıktısı yapılandırılmış (JSON/tool use) olmalı; her kritik alan
  için 0-1 güven skoru. Serbest metin parse etme.
- API anahtarını loglamaya, ekrana, dosyaya yazma.
- Test yazmadan ve çalıştırmadan "bitti" deme. excel_writer için altın
  örnek (golden file) testi zorunlu.

## Mimari
- core/ saf mantık (UI'dan bağımsız), app.py sadece Streamlit.
- Yan etkiler (API çağrısı, dosya yazımı) açıkça izole edilsin.

## Şablon notu (analizden)
- Kaynak dosyanın veri alanı düzensiz (karışık 1-2 satır merge). Bu yüzden
  scripts/build_template.py tek seferlik TEMİZ bir şablon üretir: başlık
  bandı (r1-6) korunur, veri alanı r7'den 25 satırlık düzenli grid olarak
  yeniden kurulur, footer config'ten basılır (Kıvanç AKTAN yok, Mevlüt DUMAN).
- excel_writer SADECE bu temiz şablonu (templates/bos_sablon.xlsx) klonlar.
  Hücre haritası: A=sıra, B=KODU, C:D=f"{koy}\n{malzeme}" (wrap), E=birim,
  F=miktar, G=boş. Veri r7'den başlar.

## Dil
- Arayüz ve kullanıcıya dönük metinler Türkçe. Kod/yorum İngilizce olabilir.
