import streamlit as st
import pandas as pd
import os
from datetime import datetime

# -----------------------------------------------------------
# AYARLAR VE ŞİFRELER
# -----------------------------------------------------------
DOSYA_ADI = "izin_takip.xlsx"
ADMIN_USER = "van112"
ADMIN_PASS = "van1126565"

st.set_page_config(page_title="Personel İzin Sistemi", page_icon="🗓️", layout="wide")

# -----------------------------------------------------------
# VERITABANI YÖNETİMİ
# -----------------------------------------------------------
class DataManager:
    def __init__(self):
        self.check_db()

    def check_db(self):
        """Excel dosyası yoksa yeni sütunlarla oluşturur"""
        if not os.path.exists(DOSYA_ADI):
            # Yeni sütunlar eklendi: TC ve Gün Sayısı
            df = pd.DataFrame(columns=[
                "ID", "TC Kimlik", "Ad Soyad", "Talep Türü", 
                "Başlangıç", "Bitiş", "Gün Sayısı", 
                "Açıklama", "Talep Tarihi", "Durum"
            ])
            df.to_excel(DOSYA_ADI, index=False)

    def load_data(self):
        try:
            return pd.read_excel(DOSYA_ADI)
        except:
            return pd.DataFrame()

    def save_data(self, df):
        df.to_excel(DOSYA_ADI, index=False)

    def add_request(self, tc, ad_soyad, tur, baslangic, bitis, aciklama):
        df = self.load_data()
        new_id = 1
        if not df.empty:
            new_id = df["ID"].max() + 1
            
        # Gün farkını hesapla (Bitiş - Başlangıç + 1 gün)
        delta = (bitis - baslangic).days + 1
        
        new_data = {
            "ID": new_id,
            "TC Kimlik": tc,
            "Ad Soyad": ad_soyad,
            "Talep Türü": tur,
            "Başlangıç": baslangic.strftime("%d.%m.%Y"),
            "Bitiş": bitis.strftime("%d.%m.%Y"),
            "Gün Sayısı": delta,  # Hesaplanan gün
            "Açıklama": aciklama,
            "Talep Tarihi": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "Durum": "Beklemede ⏳"
        }
        
        new_row = pd.DataFrame([new_data])
        df = pd.concat([df, new_row], ignore_index=True)
        self.save_data(df)

db = DataManager()

# -----------------------------------------------------------
# ARAYÜZ
# -----------------------------------------------------------
st.title("🗓️ Personel İzin ve Rapor Sistemi")

giris_tabi, personel_tabi = st.tabs(["🔐 Yönetici Paneli", "👤 Personel Talep Formu"])

# --- 1. YÖNETİCİ EKRANI ---
with giris_tabi:
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = False

    if not st.session_state['admin_logged_in']:
        st.subheader("Yönetici Girişi")
        kadi = st.text_input("Kullanıcı Adı", key="admin_user")
        sifre = st.text_input("Şifre", type="password", key="admin_pass")
        
        if st.button("Giriş Yap"):
            if kadi == ADMIN_USER and sifre == ADMIN_PASS:
                st.session_state['admin_logged_in'] = True
                st.rerun()
            else:
                st.error("Hatalı Giriş!")
    else:
        # Yönetici İçeriği
        c1, c2 = st.columns([8, 1])
        with c1:
            st.success(f"Yönetici Paneli | Aktif Kullanıcı: {ADMIN_USER}")
        with c2:
            if st.button("Çıkış"):
                st.session_state['admin_logged_in'] = False
                st.rerun()
            
        st.divider()
        st.subheader("📋 Bekleyen ve Onaylanan Talepler")
        
        df = db.load_data()
        
        if not df.empty:
            # Önce Bekleyenleri Göster
            df = df.sort_values(by="Durum", ascending=True) 

            edited_df = st.data_editor(
                df,
                use_container_width=True,
                # ID ve Gün Sayısı gibi otomatik alanları değiştirmesin
                disabled=["ID", "Talep Tarihi", "Gün Sayısı"], 
                column_config={
                    "Durum": st.column_config.SelectboxColumn(
                        "Onay Durumu",
                        help="Onaylamak için değiştirin",
                        width="medium",
                        options=["Beklemede ⏳", "Onaylandı ✅", "Reddedildi ❌"],
                        required=True,
                    ),
                    "Gün Sayısı": st.column_config.NumberColumn(
                        "Gün",
                        help="Toplam İzin Günü",
                        format="%d Gün"
                    )
                }
            )
            
            if st.button("💾 Değişiklikleri Kaydet", type="primary"):
                db.save_data(edited_df)
                st.success("Veritabanı güncellendi!")
                st.rerun()
        else:
            st.info("Görüntülenecek talep yok.")

# --- 2. PERSONEL EKRANI ---
with personel_tabi:
    st.header("Yeni İzin / Rapor Talebi")
    st.info("Lütfen bilgileri eksiksiz doldurunuz. Talebiniz doğrudan yöneticiye iletilecektir.")
    
    with st.form("talep_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tc = st.text_input("TC Kimlik No", max_chars=11)
            ad = st.text_input("Ad Soyad")
            tur = st.selectbox("Talep Türü", ["Yıllık İzin", "Rapor", "Mazeret İzni", "Ücretsiz İzin"])
        with col2:
            d_bas = st.date_input("Başlangıç Tarihi")
            d_bit = st.date_input("Bitiş Tarihi")
            
        aciklama = st.text_area("Açıklama / Adres")
        
        submitted = st.form_submit_button("Talebi Gönder 🚀")
        
        if submitted:
            # Basit Kontroller
            if not tc or not ad:
                st.error("Lütfen TC Kimlik ve Ad Soyad alanlarını doldurunuz.")
            elif d_bit < d_bas:
                st.error("Hata: Bitiş tarihi, başlangıç tarihinden önce olamaz!")
            else:
                db.add_request(tc, ad, tur, d_bas, d_bit, aciklama)
                st.success("Talebiniz başarıyla kaydedildi! Yönetici onayı bekleniyor.")
                st.balloons()