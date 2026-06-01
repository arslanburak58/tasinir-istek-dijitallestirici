# Buluta Yükleme (Streamlit Community Cloud) — Telefondan Kullanım

Amaç: uygulamayı internete koyup telefondan (her yerden) açmak. API anahtarın
**GitHub'a gitmez**; yalnızca Streamlit Cloud'un şifreli "Secrets" alanında durur.
Parola (APP_PAROLA) ile linki güvenle paylaşabilirsin — parolayı bilmeyen senin
API kredini harcayamaz.

## Tek seferlik kurulum

1. **https://share.streamlit.io** adresine git, **GitHub ile giriş yap**
   (arslanburak58 hesabı).
2. **Create app → Deploy from GitHub**. İlk seferde Streamlit'in gizli depona
   erişmesi için izin iste/onayla (Authorize streamlit).
3. Alanları doldur:
   - **Repository:** `arslanburak58/tasinir-istek-dijitallestirici`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. **Advanced settings → Secrets** kutusuna şunu yapıştır (gerçek değerlerle):
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-...(kendi anahtarın)"
   APP_PAROLA = "sectigin-guclu-parola"
   ```
   > Anahtarını `Desktop/exceller/.env` dosyasından kopyalayabilirsin
   > (`ANTHROPIC_API_KEY=` kısmından sonrası).
5. **Deploy** de. Birkaç dakikada `https://....streamlit.app` adresin hazır olur.

## Telefondan kullanım
- Adresi telefon tarayıcısında aç → **parolayı gir**.
- "Fotoğrafları yükle" alanında telefonda **"Fotoğraf Çek"** seçeneği çıkar;
  belgeyi çekip yükle → çıkar → düzelt → onayla → Excel'i indir.

## Paylaşma
- Linki + parolayı güvendiğin kişilere ver. Parolayı değiştirmek istersen
  Streamlit panelinde **Settings → Secrets**'tan `APP_PAROLA`'yı güncelle.

## Kod güncelleme
- Kodu değiştirip GitHub'a push edersen Streamlit Cloud **otomatik yeniden
  dağıtır**; ekstra işlem gerekmez.
