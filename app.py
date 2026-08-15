import streamlit as st
import pandas as pd
from datetime import datetime

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="ระบบบริหารคลังสินค้า (Cloud Access)", layout="wide")

# =====================================================================
# 1. ฐานข้อมูลผู้ใช้งาน (USER DATABASE)
# =====================================================================
USER_DATABASE = {
    "admin": {"password": "88888888", "name": "ผู้ดูแลระบบ", "role": "Admin"},
    "prajak": {"password": "123456", "name": "Mr.Prajak", "role": "Manager"},
    "user2": {"password": "user5678", "name": "พนักงานฝ่ายผลิต B", "role": "User"}
}

# Initial Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# ฐานข้อมูลจำลอง (จะอัปเดตแบบ Real-time ใน memory ของเซิร์ฟเวอร์)
if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame([
        {"code": "RM-001", "name": "แผ่นไม้พาเลท", "qty": 150.0, "unit": "ชิ้น", "min_alert": 20},
        {"code": "RM-002", "name": "สกรูยึด 2 นิ้ว", "qty": 5000.0, "unit": "ตัว", "min_alert": 500},
        {"code": "RM-003", "name": "สีทาไม้ (แกลลอน)", "qty": 45.0, "unit": "แกลลอน", "min_alert": 10}
    ])

if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["timestamp", "type", "code", "name", "qty", "unit", "operator"])

# =====================================================================
# 2. หน้าจอเข้าสู่ระบบ (LOGIN SCREEN)
# =====================================================================
def login_screen():
    st.markdown("<h2 style='text-align: center;'>🔐 เข้าสู่ระบบบริหารคลังและการผลิต</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username (ชื่อผู้ใช้งาน)")
            password = st.text_input("Password (รหัสผ่าน)", type="password")
            submit = st.form_submit_button("เข้าสู่ระบบ")
            
            if submit:
                if username in USER_DATABASE and USER_DATABASE[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_info = USER_DATABASE[username]
                    st.success("เข้าสู่ระบบสำเร็จ!")
                    st.rerun()
                else:
                    st.error("Username หรือ Password ไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง")

# =====================================================================
# 3. หน้าจอหลักของระบบ (MAIN APPLICATION)
# =====================================================================
def main_app():
    user = st.session_state.user_info
    
    # -------------------------------------------------------------
    # เมนูด้านซ้าย (Sidebar)
    # -------------------------------------------------------------
    st.sidebar.title(f"👤 สวัสดี, {user['name']}")
    st.sidebar.caption(f"สิทธิ์การใช้งาน: {user['role']}")
    
    menu = st.sidebar.radio(
        "เลือกเมนูการทำงาน:",
        ["📦 คลังวัตถุดิบปัจจุบัน", "📥 รับเข้าวัตถุดิบ (IN)", "📤 เบิกออกวัตถุดิบ (OUT)", "📜 ประวัติการรับ-เบิก"]
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 ออกจากระบบ (Logout)", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()

    st.title("🏭 ระบบบริหารคลังและการผลิต (Real-time Cloud)")
    st.caption("💡 ข้อมูลเชื่อมโยง Real-time ทุกอุปกรณ์ผ่านระบบผู้ใช้งาน")

    # -------------------------------------------------------------
    # เมนู 1: คลังวัตถุดิบปัจจุบัน
    # -------------------------------------------------------------
    if menu == "📦 คลังวัตถุดิบปัจจุบัน":
        st.subheader("📦 รายการวัตถุดิบล่าสุดในคลัง")
        
        # การ์ดสรุปจำนวนรายการ
        total_items = len(st.session_state.inventory)
        low_stock_items = len(st.session_state.inventory[st.session_state.inventory['qty'] <= st.session_state.inventory['min_alert']])
        
        col1, col2 = st.columns(2)
        col1.metric("จำนวนรายการวัตถุดิบทั้งหมด", f"{total_items} รายการ")
        col2.metric("รายการที่สต็อกต่ำกว่าเกณฑ์", f"{low_stock_items} รายการ", delta_color="inverse")
        
        st.markdown("---")
        st.dataframe(
            st.session_state.inventory.style.format({'qty': '{:,.2f}'}),
            use_container_width=True
        )

    # -------------------------------------------------------------
    # เมนู 2: รับเข้าวัตถุดิบ (IN)
    # -------------------------------------------------------------
    elif menu == "📥 รับเข้าวัตถุดิบ (IN)":
        st.subheader("📥 บันทึกการรับเข้าวัตถุดิบ (Stock In)")
        
        # ดึงรายการวัตถุดิบที่มีอยู่มาใส่ Dropdown
        df_inv = st.session_state.inventory
        item_list = [f"{row['code']} - {row['name']}" for _, row in df_inv.iterrows()]
        item_list.append("➕ เพิ่มวัตถุดิบใหม่เข้าสู่ระบบ")
        
        with st.form("stock_in_form"):
            selected_item = st.selectbox("เลือกวัตถุดิบที่ต้องการรับเข้า:", item_list)
            
            # ถ้าเป็นสินค้าใหม่ ให้กรอกชื่อและหน่วยนับเพิ่ม
            if selected_item == "➕ เพิ่มวัตถุดิบใหม่เข้าสู่ระบบ":
                new_code = st.text_input("รหัสวัตถุดิบใหม่ (เช่น RM-004)")
                new_name = st.text_input("ชื่อวัตถุดิบใหม่")
                new_unit = st.text_input("หน่วยนับ (เช่น ชิ้น, กิโลกรัม, ลิตร)")
                new_min = st.number_input("เกณฑ์แจ้งเตือนสต็อกต่ำ (Min Alert)", value=10, step=1)
            
            in_qty = st.number_input("จำนวนที่รับเข้า:", min_value=0.01, step=1.0)
            submit_in = st.form_submit_button("💾 บันทึกการรับเข้า")
            
            if submit_in:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if selected_item == "➕ เพิ่มวัตถุดิบใหม่เข้าสู่ระบบ":
                    if new_code and new_name and new_unit:
                        # เพิ่มรายการใหม่
                        new_row = {"code": new_code, "name": new_name, "qty": in_qty, "unit": new_unit, "min_alert": new_min}
                        st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([new_row])], ignore_index=True)
                        item_code, item_name, item_unit = new_code, new_name, new_unit
                    else:
                        st.error("กรุณากรอกข้อมูลวัตถุดิบใหม่ให้ครบถ้วน")
                        st.stop()
                else:
                    # อัปเดตรายการเดิม
                    item_code = selected_item.split(" - ")[0]
                    idx = st.session_state.inventory[st.session_state.inventory['code'] == item_code].index[0]
                    st.session_state.inventory.loc[idx, 'qty'] += in_qty
                    item_name = st.session_state.inventory.loc[idx, 'name']
                    item_unit = st.session_state.inventory.loc[idx, 'unit']
                
                # บันทึกประวัติ Transaction
                log_entry = {
                    "timestamp": now_str, "type": "รับเข้า (+)", "code": item_code,
                    "name": item_name, "qty": in_qty, "unit": item_unit, "operator": user['name']
                }
                st.session_state.history = pd.concat([pd.DataFrame([log_entry]), st.session_state.history], ignore_index=True)
                
                st.success(f"บันทึกรับเข้า `{item_name}` จำนวน {in_qty:,.2f} {item_unit} เรียบร้อยแล้ว!")

    # -------------------------------------------------------------
    # เมนู 3: เบิกออกวัตถุดิบ (OUT)
    # -------------------------------------------------------------
    elif menu == "📤 เบิกออกวัตถุดิบ (OUT)":
        st.subheader("📤 บันทึกการเบิกออกวัตถุดิบ (Stock Out)")
        
        df_inv = st.session_state.inventory
        item_options = {f"{row['code']} - {row['name']} (คงเหลือ: {row['qty']:,.2f} {row['unit']})": row['code'] for _, row in df_inv.iterrows()}
        
        if not item_options:
            st.warning("ไม่มีวัตถุดิบในคลังสินค้า")
        else:
            with st.form("stock_out_form"):
                selected_display = st.selectbox("เลือกวัตถุดิบที่ต้องการเบิก:", list(item_options.keys()))
                item_code = item_options[selected_display]
                
                # ดึงข้อมูลคงเหลือปัจจุบัน
                idx = df_inv[df_inv['code'] == item_code].index[0]
                current_qty = df_inv.loc[idx, 'qty']
                unit = df_inv.loc[idx, 'unit']
                item_name = df_inv.loc[idx, 'name']
                
                out_qty = st.number_input("จำนวนที่ต้องการเบิกออก:", min_value=0.01, max_value=float(current_qty), step=1.0)
                submit_out = st.form_submit_button("💾 บันทึกการเบิกออก")
                
                if submit_out:
                    if out_qty > current_qty:
                        st.error("จำนวนที่เบิกเกินกว่าจำนวนสินค้าคงเหลือในคลัง!")
                    else:
                        # ตัดสต็อก
                        st.session_state.inventory.loc[idx, 'qty'] -= out_qty
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # บันทึกประวัติ
                        log_entry = {
                            "timestamp": now_str, "type": "เบิกออก (-)", "code": item_code,
                            "name": item_name, "qty": out_qty, "unit": unit, "operator": user['name']
                        }
                        st.session_state.history = pd.concat([pd.DataFrame([log_entry]), st.session_state.history], ignore_index=True)
                        
                        st.success(f"ตัดสต็อก `{item_name}` จำนวน {out_qty:,.2f} {unit} โดย {user['name']} เรียบร้อย!")

    # -------------------------------------------------------------
    # เมนู 4: ประวัติการรับ-เบิก (Transaction History)
    # -------------------------------------------------------------
    elif menu == "📜 ประวัติการรับ-เบิก":
        st.subheader("📜 ประวัติการรับเข้าและเบิกออกวัตถุดิบท้งหมด")
        if st.session_state.history.empty:
            st.info("ยังไม่มีประวัติการทำรายการ")
        else:
            st.dataframe(st.session_state.history, use_container_width=True)

# =====================================================================
# 4. ตัวควบคุมหน้าจอ (APP CONTROLLER)
# =====================================================================
if not st.session_state.logged_in:
    login_screen()
else:
    main_app()