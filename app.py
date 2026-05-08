import streamlit as st
from supabase import create_client, Client
import datetime

# --- 1. ตั้งค่าการเชื่อมต่อ (ใส่ค่าของคุณตรงนี้) ---
URL = "https://bzjcnaknbazxohtqznvq.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ6amNuYWtuYmF6eG9odHF6bnZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc1NjA1MTgsImV4cCI6MjA5MzEzNjUxOH0.MNAhbiPORjrajMs2E4_qGy_7FWE3hFIgJT3sGZfnZPE"
supabase: Client = create_client(URL, KEY)

# ตั้งค่าหน้าเว็บให้ดูง่ายขึ้น
st.set_page_config(page_title="Bot Rental Admin", layout="wide")

def add_bg_from_url():
    st.markdown(
        """
        <style>
        /* 1. บังคับแบล็คกราวด์ทุกชั้น (ใส่ทั้งรูปและสีสำรอง) */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), 
                              url("https://images.pexels.com/photos/6770610/pexels-photo-6770610.jpeg") !important;
            background-color: #0e1117 !important; /* สีดำเข้มสำรองเผื่อรูปไม่ขึ้น */
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
        }

        /* 2. บังคับซ่อนไอคอนเจ้าปัญหาที่ทำให้ตัวหนังสือซ้อน */
        [data-testid="stExpander"] svg {
            display: none !important;
        }
        
        /* 3. กล่องเนื้อหา (ทำเป็นกระจกฝ้า Glassmorphism) */
        .main .block-container {
            background: rgba(255, 255, 255, 0.9) !important;
            border-radius: 20px !important;
            padding: 3rem !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8) !important;
            margin-top: 50px;
        }

        /* 4. ปรับสี Font ให้เข้ากับแบล็คกราวด์เข้ม */
        h1, h2, h3 {
            color: #ffffff !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5) !important;
            padding-bottom: 20px;
        }
        
        /* แก้สีตัวหนังสือในกล่อง Expander ให้เป็นสีดำเพื่อให้อ่านง่าย */
        [data-testid="stExpander"] p, [data-testid="stExpander"] label {
            color: #000000 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
st.title("🤖 Bot Rental Management System")

# --- 2. ส่วนแสดงสถานะปัจจุบัน ---
st.header("📋 สถานะการเช่าบอทปัจจุบัน")
rentals = supabase.table("v_rental_dashboard").select("*").execute()
rental_options = {}

if rentals.data:
    # สร้างคอลัมน์แสดงผลแบบ Grid
    for i in range(0, len(rentals.data), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(rentals.data):
                item = rentals.data[i + j]
                # เก็บข้อมูลไว้ทำ Dropdown เติมเงิน
                label = f"{item['customer_name']} (บอท: {item['bot_name']})"
                rental_options[label] = item['rental_id']
                
                with cols[j].expander(f"👤 {item['customer_name']} - {item['bot_name']}", expanded=True):
                    c1, c2 = st.columns(2)
                    status = item['status']
                    if status == "Active":
                        c1.success(f"สถานะ: {status}")
                    elif "Warning" in status:
                        c1.warning(f"สถานะ: {status}")
                    else:
                        c1.error(f"สถานะ: {status}")
                    
                    c2.info(f"⏳ เหลือ: {int(item['minutes_remaining'])} นาที")
                    st.caption(f"หมดอายุ: {datetime.datetime.fromisoformat(item['expiry_time']).strftime('%d/%m/%Y %H:%M')}")
else:
    st.info("ยังไม่มีข้อมูลลูกค้าในระบบ")

# --- 3. ระบบจัดการ (เติมเงิน & เพิ่มลูกค้า) ---
st.divider()
col_left, col_right = st.columns(2)

with col_left:
    st.header("💰 เติมชั่วโมงการใช้งาน")
    if rental_options:
        with st.form("topup_form", clear_on_submit=True):
            selected_label = st.selectbox("เลือกลูกค้าที่ต้องการเติม", list(rental_options.keys()))
            target_id = rental_options[selected_label]
            hours_to_add = st.number_input("จำนวนชั่วโมง (1 วัน = 24)", min_value=1, value=1)
            submit_topup = st.form_submit_button("✅ ยืนยันการเติมชั่วโมง")
            
            if submit_topup:
                # ดึงเวลาเดิมมาคำนวณ
                current_data = supabase.table("bot_rentals").select("expiry_time").eq("id", target_id).single().execute()
                old_expiry_str = current_data.data['expiry_time']
                old_expiry = datetime.datetime.fromisoformat(old_expiry_str)
                
                now = datetime.datetime.now(datetime.timezone.utc)
                start_time = max(old_expiry, now)
                new_expiry = start_time + datetime.timedelta(hours=hours_to_add)
                
                # อัปเดตตารางหลัก
                supabase.table("bot_rentals").update({"expiry_time": new_expiry.isoformat()}).eq("id", target_id).execute()
                
                # บันทึกประวัติ (Top-up History)
                supabase.table("topup_history").insert({
                    "rental_id": target_id,
                    "hours_added": hours_to_add,
                    "old_expiry": old_expiry_str,
                    "new_expiry": new_expiry.isoformat()
                }).execute()
                
                st.success(f"เติมสำเร็จ! บอทจะหมดอายุวันที่ {new_expiry.strftime('%d/%m/%Y %H:%M')}")
                st.rerun()

with col_right:
    st.header("➕ เพิ่มลูกค้าใหม่")
    with st.form("add_customer_form", clear_on_submit=True):
        new_name = st.text_input("ชื่อลูกค้า")
        new_tel_id = st.text_input("Telegram ID (สำหรับแจ้งเตือน)")
        new_bot = st.text_input("ชื่อบอท", value="Bot_Weltrade_V3")
        init_hours = st.number_input("ชั่วโมงเริ่มต้น", min_value=1, value=24)
        submit_new = st.form_submit_button("💾 บันทึกข้อมูล")
        
        if submit_new and new_name:
            # เพิ่มลูกค้า
            res = supabase.table("customers").insert({"name": new_name, "telegram_id": new_tel_id}).execute()
            new_id = res.data[0]['id']
            # เพิ่มข้อมูลเช่า
            exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=init_hours)
            supabase.table("bot_rentals").insert({"customer_id": new_id, "bot_name": new_bot, "expiry_time": exp.isoformat()}).execute()
            st.success(f"เพิ่มลูกค้า {new_name} เรียบร้อย!")
            st.rerun()

# --- 4. แสดงประวัติการเติมเงิน ---
st.divider()
st.header("📜 ประวัติการเติมเงินล่าสุด (10 รายการ)")
history = supabase.table("v_topup_logs").select("*").order("created_at", desc=True).limit(10).execute()

if history.data:
    df_history = []
    for h in history.data:
        df_history.append({
            "วันที่ทำรายการ": datetime.datetime.fromisoformat(h['created_at']).strftime('%d/%m/%Y %H:%M'),
            "ลูกค้า": h['customer_name'],
            "บอท": h['bot_name'],
            "เติม (ชม.)": h['hours_added'],
            "หมดอายุใหม่": datetime.datetime.fromisoformat(h['new_expiry']).strftime('%d/%m/%Y %H:%M')
        })
    st.table(df_history)
