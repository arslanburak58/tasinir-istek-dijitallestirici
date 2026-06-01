"""Streamlit arayüzü — sadece UI. İş mantığı core/ içinde.

Akış: yükle -> Vision çıkar -> düzelt/onayla -> köy eşleştir -> tarih onayı
-> Excel üret -> indir. Onaysız Excel üretilmez; her çalıştırma yeni dosya.
"""
import datetime as _dt

import pandas as pd
import streamlit as st

import config
from core import excel_writer, normalize, ogrenme, vision
from core.schema import Kalem

st.set_page_config(page_title="Taşınır İstek Belgesi Dijitalleştirici", layout="wide")
st.title("Taşınır İstek Belgesi Dijitalleştirici")

ss = st.session_state
ss.setdefault("rows", None)
ss.setdefault("giris_ok", False)


def _hafiza() -> dict:
    """Load the persistent correction memory once per session."""
    if "hafiza" not in ss:
        ss.hafiza, ss.hafiza_sha = ogrenme.yukle()
    return ss.hafiza


def _parola_kontrol():
    """If APP_PAROLA is configured, require it before using the app. This keeps
    your API credits safe when the URL is shared."""
    if not config.APP_PAROLA:
        return True  # no password configured -> open (local use)
    if ss.giris_ok:
        return True
    st.subheader("🔒 Giriş")
    girilen = st.text_input("Parola", type="password")
    if st.button("Giriş yap"):
        if girilen == config.APP_PAROLA:
            ss.giris_ok = True
            st.rerun()
        else:
            st.error("Parola yanlış.")
    st.stop()


_parola_kontrol()

_s = ogrenme.sayilar(_hafiza())
_depo = "GitHub (kalıcı)" if ogrenme.aktif_github() else "yerel/oturum"
st.caption(f"🧠 Öğrenilen düzeltmeler — köy: {_s['koy']} · malzeme: {_s['malzeme']} · "
           f"birim: {_s['birim']}  •  depo: {_depo}")

KOLONLAR = ["koy", "malzeme_adi", "miktar", "olcu_birimi", "kodu",
            "guven_koy", "guven_malzeme", "guven_miktar"]
GORUNUR = ["koy", "malzeme_adi", "miktar", "olcu_birimi", "kodu",
           "guven_koy", "guven_malzeme", "guven_miktar"]


def _dusuk(row) -> bool:
    return min(row["guven_koy"], row["guven_malzeme"], row["guven_miktar"]) < config.GUVEN_DUSUK_ESIK


# ---------------------------------------------------------------- 1) Yükleme
st.header("1) Fotoğrafları yükle")
files = st.file_uploader(
    "Taşınır İstek Belgesi fotoğrafları (birden fazla seçebilirsiniz)",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
)

if files and st.button("Fotoğrafları çıkar", type="primary"):
    rows = []
    bar = st.progress(0.0, text="Çıkarılıyor...")
    for i, f in enumerate(files):
        try:
            tutanak = vision.cikar(f.getvalue(), media_type=f.type, dosya_adi=f.name)
            ogrenme.uygula(tutanak.kalemler, _hafiza())  # auto-fix known corrections
            for k in tutanak.kalemler:
                rows.append(k.model_dump())
        except Exception as e:  # noqa: BLE001 - surface to user
            st.error(f"{f.name}: çıkarma hatası — {e}")
        bar.progress((i + 1) / len(files), text=f"{i + 1}/{len(files)} fotoğraf")
    bar.empty()
    ss.rows = rows
    if not rows:
        st.warning("Hiç kalem çıkarılamadı.")

# ------------------------------------------------- 2) İnceleme / düzeltme
if ss.rows is not None and len(ss.rows) > 0:
    st.header("2) İncele ve düzelt")
    df = pd.DataFrame(ss.rows, columns=KOLONLAR)
    # snapshot of values as shown (post-memory) -> used to learn further edits
    df["_orig_koy"] = df["koy"]
    df["_orig_malzeme"] = df["malzeme_adi"]
    df["_orig_birim"] = df["olcu_birimi"]
    n_dusuk = int(df.apply(_dusuk, axis=1).sum())
    if n_dusuk:
        st.warning(f"⚠️ {n_dusuk} kalemde düşük güven var — özellikle kırmızı satırları kontrol edin.")

    def _vurgu(row):
        return ["background-color: #ffe5e5" if _dusuk(row) else "" for _ in row]

    st.caption("Aşağıdaki tabloyu doğrudan düzenleyebilirsiniz.")
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_order=GORUNUR,  # hide _orig_* (kept in returned data for learning)
        column_config={
            "koy": "Köy",
            "malzeme_adi": "Malzeme",
            "miktar": st.column_config.NumberColumn("Miktar", min_value=0),
            "olcu_birimi": "Ölçü Birimi",
            "kodu": "Kodu",
            "guven_koy": st.column_config.NumberColumn("Güven(köy)", disabled=True, format="%.2f"),
            "guven_malzeme": st.column_config.NumberColumn("Güven(malzeme)", disabled=True, format="%.2f"),
            "guven_miktar": st.column_config.NumberColumn("Güven(miktar)", disabled=True, format="%.2f"),
        },
        key="editor",
    )
    with st.expander("Renkli önizleme (düşük güven = kırmızı)"):
        st.dataframe(df.style.apply(_vurgu, axis=1), use_container_width=True)

    edited = edited.dropna(subset=["koy", "malzeme_adi"]).reset_index(drop=True)

    # ------------------------------------------- 3) Köy eşleştirme onayı
    st.header("3) Köy eşleştirme")
    ham_koyler = sorted({str(k).strip() for k in edited["koy"].tolist() if str(k).strip()})
    bilinenler = normalize.bilinen_koyler()
    koy_haritasi = {}
    belirsizler = []
    for ham in ham_koyler:
        es = normalize.koy_snap(ham)
        if es.kullanici_onayi_gerek:
            belirsizler.append((ham, es))
        elif es.yeni_koy:
            koy_haritasi[ham] = es.onerilen
            st.caption(f"🆕 '{ham}' → **{es.onerilen}** (listede yok, yeni sekme)")
        else:
            koy_haritasi[ham] = es.onerilen
            st.caption(f"✅ '{ham}' → {es.onerilen} (skor {es.skor:.0f})")

    if belirsizler:
        st.warning(f"⚠️ {len(belirsizler)} köy belirsiz — onaylayın "
                   "(varsayılan: ham adı koru, yanlış köye çevirme yok).")
    for ham, es in belirsizler:
        yeni_etiket = f"🆕 Yeni köy: {es.onerilen}"
        secenekler = [yeni_etiket] + es.adaylar + [b for b in bilinenler if b not in es.adaylar]
        secim = st.selectbox(
            f"'{ham}' (en yakın: {es.adaylar[0]} • skor {es.skor:.0f}). Hangisi?",
            options=secenekler,
            index=0,
            key=f"koy_{ham}",
        )
        koy_haritasi[ham] = es.onerilen if secim == yeni_etiket else secim

    # ------------------------------------------- 4) Tarih / No onayı
    st.header("4) Tarih ve belge no")
    bugun = _dt.date.today()
    st.info(f"Belgeye bugünün tarihi yazılacak: **{bugun.strftime('%d.%m.%Y')}**. "
            "Değiştirmek ister misiniz?")
    secim_tarih = st.radio(
        "Tarih",
        [f"Bugünü kullan ({bugun.strftime('%d.%m.%Y')})", "Farklı tarih gir"],
        index=0, horizontal=True,
    )
    if secim_tarih.startswith("Farklı"):
        sel = st.date_input("Belge tarihi", value=bugun, format="DD.MM.YYYY")
        tarih_str = sel.strftime("%d.%m.%Y")
    else:
        tarih_str = bugun.strftime("%d.%m.%Y")
    no = st.text_input("Belge No (opsiyonel)", value="")

    # ------------------------------------------- 5) Üret / indir
    st.header("5) Excel üret")
    onay = st.checkbox("Verileri ve eşleştirmeleri kontrol ettim, onaylıyorum.")
    if st.button("Excel oluştur", type="primary", disabled=not onay):
        kalemler = [
            Kalem(
                koy=str(r["koy"]),
                malzeme_adi=str(r["malzeme_adi"]),
                miktar=float(r["miktar"] or 0),
                olcu_birimi=(str(r["olcu_birimi"]).strip() or None) if pd.notna(r["olcu_birimi"]) else None,
                kodu=(str(r["kodu"]).strip() or None) if pd.notna(r["kodu"]) else None,
                guven_koy=float(r["guven_koy"]), guven_malzeme=float(r["guven_malzeme"]),
                guven_miktar=float(r["guven_miktar"]),
            )
            for _, r in edited.iterrows()
        ]
        sayfalar = normalize.topla(kalemler, koy_haritasi=koy_haritasi)
        yol = excel_writer.yaz(sayfalar, tarih=tarih_str, no=no or None)
        st.success(f"Oluşturuldu: {yol.name}  ({len(sayfalar)} köy sekmesi)")
        with open(yol, "rb") as fh:
            st.download_button(
                "Excel'i indir",
                data=fh.read(),
                file_name=yol.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        # --- Learn from this session's corrections and persist ---
        data = _hafiza()
        degisti = 0
        for _, r in edited.iterrows():
            cur_koy = str(r["koy"]).strip()
            final_koy = koy_haritasi.get(cur_koy, cur_koy)
            degisti += ogrenme.ekle(data, "koy", str(r.get("_orig_koy", "")), final_koy)
            degisti += ogrenme.ekle(data, "malzeme", str(r.get("_orig_malzeme", "")), str(r["malzeme_adi"]))
            cur_b = str(r["olcu_birimi"]).strip() if pd.notna(r["olcu_birimi"]) else ""
            degisti += ogrenme.ekle(data, "birim", str(r.get("_orig_birim", "")), cur_b)
        if degisti:
            try:
                ss.hafiza_sha = ogrenme.kaydet(data, ss.get("hafiza_sha"))
                st.info(f"🧠 {degisti} yeni düzeltme hafızaya kaydedildi "
                        "(bir dahaki sefere otomatik uygulanacak).")
            except Exception as e:  # noqa: BLE001
                st.warning(f"Düzeltmeler bu oturumda öğrenildi ama kalıcı kaydedilemedi: {e}")
