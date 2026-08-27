import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ระบบควบคุมสินค้า & การผลิต", layout="wide", initial_sidebar_state="collapsed")

# =====================================================================
# 1. CONSTANTS & USER DATABASE WITH ROLES
# =====================================================================
USER_DATABASE = {
    "admin": {"password": "888", "name": "ผู้ดูแลระบบ", "role": "Admin"},
    "wh_staff": {"password": "123", "name": "พนักงานคลังสินค้า", "role": "Warehouse"},
    "prod_staff": {"password": "123", "name": "พนักงานฝ่ายผลิต", "role": "Production"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "main_menu"

# ฐานข้อมูลจำลอง (RM, FG, Jobs)
if "inventory_rm" not in st.session_state:
    st.session_state.inventory_rm = pd.DataFrame([
        {"code": "RM-001", "name": "ม้วนฟิล์ม PET 12u", "qty": 5000.0, "unit": "Kg"},
        {"code": "RM-002", "name": "ม้วนฟิล์ม LLDPE 40u", "qty": 4000.0, "unit": "Kg"},
        {"code": "RM-003", "name": "หมึกพิมพ์ Solvent Base", "qty": 300.0, "unit": "Kg"},
        {"code": "RM-004", "name": "กาว PU Dry Lamination", "qty": 500.0, "unit": "Kg"},
        {"code": "RM-005", "name": "จุกฝาเกลียว (Spout 10mm)", "qty": 50000.0, "unit": "ชิ้น"}
    ])

if "inventory_fg" not in st.session_state:
    st.session_state.inventory_fg = pd.DataFrame([
        {"job_id": "JOB-2026-000", "product_name": "ซองกาแฟ 250g", "qty": 15000, "unit": "ซอง", "in_date": "2026-08-20"}
    ])

if "jobs" not in st.session_state:
    st.session_state.jobs = pd.DataFrame([
        {"job_id": "JOB-2026-001", "product_name": "ซองติดจุก 250ml", "job_type": "ซองติดจุก (Spout)", "current_stage": "WIP 1: Print (พิมพ์ลาย)", "target_qty": 20000, "unit": "ซอง"}
    ])

if "issued_materials" not in st.session_state:
    st.session_state.issued_materials = pd.DataFrame(columns=["job_id", "target_wip", "rm_code", "rm_name", "qty", "unit", "issue_date"])

# ซ่อนแถบ Sidebar ของ Streamlit ด้วย CSS
st.markdown("""
    <style>
        [data-testid="collapsedControl"] {display: none;}
        section[data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. LOGIN SCREEN
# =====================================================================
def login_screen():
    st.markdown("<h2 style='text-align: center;'>🔐 เข้าสู่ระบบควบคุมสินค้า & การผลิต</h2>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username (admin / wh_staff / prod_staff)")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("เข้าสู่ระบบ")
            if submit:
                if username in USER_DATABASE and USER_DATABASE[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_info = USER_DATABASE[username]
                    st.session_state.current_page = "main_menu"
                    st.rerun()
                else:
                    st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

# =====================================================================
# 3. MAIN APPLICATION & NAVIGATION CONTROL
# =====================================================================
def main_app():
    user = st.session_state.user_info
    role = user["role"]

    # Header ส่วนบนสุด
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.title("🏭 ระบบคลังสินค้า & ควบคุมกระบวนการผลิต")
        st.caption(f"👤 ผู้ใช้งาน: **{user['name']}** | สิทธิ์การใช้งาน: **{role}**")
    with head_col2:
        st.write("")
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()
            
    st.markdown("---")

    # -------------------------------------------------------------
    # 📍 หน้าหลัก (Main Dashboard) แสดงเมนูกลางแบบไม่มี Sidebar
    # -------------------------------------------------------------
    if st.session_state.current_page == "main_menu":
        col_wh, col_prod = st.columns(2)
        
        # --- 📦 โซนคลังสินค้า (RM / FG) ---
        with col_wh:
            st.markdown("### 📦 คลัง RM / FG")
            if role in ["Admin", "Warehouse"]:
                if st.button("📦 1. สต็อกวัตถุดิบ (RM Stock)", use_container_width=True):
                    st.session_state.current_page = "rm_stock"
                    st.rerun()
                st.write("")
                if st.button("🏆 4. สต็อกสินค้าสำเร็จรูป (FG Stock)", use_container_width=True):
                    st.session_state.current_page = "fg_stock"
                    st.rerun()
                st.write("")
                if st.button("📜 5. ประวัติการทำรายการ", use_container_width=True):
                    st.session_state.current_page = "history"
                    st.rerun()
            else:
                st.error("🔒 คุณไม่มีสิทธิ์เข้าถึงส่วนงานคลังสินค้า (เฉพาะฝ่ายคลัง)")

        # --- 🏭 โซนฝ่ายผลิต (Production) ---
        with col_prod:
            st.markdown("### 🏭 Production")
            if role in ["Admin", "Production"]:
                if st.button("🏗️ 2. เปิด Job & จ่าย RM เข้า WIP", use_container_width=True):
                    st.session_state.current_page = "open_job"
                    st.rerun()
                st.write("")
                if st.button("🔄 3. ติดตาม & เคลื่อนย้าย WIP", use_container_width=True):
                    st.session_state.current_page = "track_wip"
                    st.rerun()
            else:
                st.error("🔒 คุณไม่มีสิทธิ์เข้าถึงส่วนงานการผลิต (เฉพาะฝ่ายผลิต)")

    # -------------------------------------------------------------
    # ปุ่มย้อนกลับ (เมื่อกดเข้าไปในหน้าย่อย)
    # -------------------------------------------------------------
    else:
        if st.button("⬅️ กลับสู่หน้าหลัก (Main Dashboard)"):
            st.session_state.current_page = "main_menu"
            st.rerun()
        st.markdown("---")

    # -------------------------------------------------------------
    # หน้าย่อย 1: คลังวัตถุดิบ (RM Stock)
    # -------------------------------------------------------------
    if st.session_state.current_page == "rm_stock":
        st.subheader("📦 สต็อกวัตถุดิบในคลัง (RM Stock)")
        
        with st.expander("📥 บันทึกรับเข้าวัตถุดิบใหม่"):
            with st.form("rec_rm"):
                c1, c2, c3, c4 = st.columns(4)
                code = c1.text_input("รหัส RM")
                name = c2.text_input("ชื่อวัตถุดิบ")
                qty = c3.number_input("จำนวนรับเข้า", min_value=0.1)
                unit = c4.selectbox("หน่วยนับ", ["Kg", "ม้วน", "ชิ้น", "ชุด"])
                if st.form_submit_button("💾 บันทึกรับเข้า"):
                    idx = st.session_state.inventory_rm[st.session_state.inventory_rm['code'] == code].index
                    if len(idx) > 0:
                        st.session_state.inventory_rm.loc[idx[0], 'qty'] += qty
                    else:
                        new_rm = {"code": code, "name": name, "qty": qty, "unit": unit}
                        st.session_state.inventory_rm = pd.concat([st.session_state.inventory_rm, pd.DataFrame([new_rm])], ignore_index=True)
                    st.success("บันทึกรับเข้าเรียบร้อย")
                    st.rerun()
                    
        st.dataframe(st.session_state.inventory_rm, use_container_width=True)

    # -------------------------------------------------------------
    # หน้าย่อย 2: เปิด Job & จ่าย RM เข้า WIP
    # -------------------------------------------------------------
    elif st.session_state.current_page == "open_job":
        st.subheader("🏗️ เปิด Job Order ใหม่ & จ่าย RM ตรงเข้า WIP")
        tab_new, tab_issue = st.tabs(["🚀 เปิด Job ใหม่", "📤 จ่าย RM เข้า WIP"])
        
        with tab_new:
            with st.form("create_job"):
                j_id = st.text_input("เลขที่ Job Order (เช่น JOB-2026-002)")
                p_name = st.text_input("ชื่อสินค้า/ซองบรรจุภัณฑ์")
                j_type = st.selectbox("ประเภทปลายทางการผลิต:", [
                    "งานม้วน (Dry2 -> Slit -> Packing)",
                    "ซองไม่ติดจุก (Dry2 -> Bag Making -> Packing)",
                    "ซองผ่านการตัดม้วน (Dry2 -> Slit -> Bag Making -> Packing)",
                    "ซองติดจุก (Spout)"
                ])
                t_qty = st.number_input("จำนวนที่ต้องการผลิต", min_value=1, value=10000)
                u_name = st.selectbox("หน่วยผลิต", ["ซอง", "ม้วน", "ชิ้น"])
                
                if st.form_submit_button("💾 บันทึกเปิด Job"):
                    job_data = {
                        "job_id": j_id, "product_name": p_name, "job_type": j_type,
                        "current_stage": "WIP 1: Print (พิมพ์ลาย)", "target_qty": t_qty, "unit": u_name
                    }
                    st.session_state.jobs = pd.concat([st.session_state.jobs, pd.DataFrame([job_data])], ignore_index=True)
                    st.success(f"เปิด Job {j_id} เรียบร้อยแล้ว")
                    st.rerun()

        with tab_issue:
            with st.form("issue_rm"):
                job_list = st.session_state.jobs['job_id'].tolist()
                sel_job = st.selectbox("เลือก Job Order:", job_list if job_list else ["ไม่มี Job"])
                target_wip = st.selectbox("จ่ายตรงไปยัง WIP ขั้นตอน:", [
                    "WIP 1: Print (จ่าย ฟิล์ม/หมึก)", "WIP 2: Dry 1 (จ่าย ฟิล์ม/กาว)",
                    "WIP 3: Dry 2 (จ่าย ฟิล์ม/กาว)", "WIP 6: Spout (จ่าย จุก/ฝา)"
                ])
                rm_opts = [f"{r['code']} - {r['name']} (คงเหลือ {r['qty']} {r['unit']})" for _, r in st.session_state.inventory_rm.iterrows()]
                sel_rm = st.selectbox("เลือกวัตถุดิบ (RM):", rm_opts)
                iss_qty = st.number_input("จำนวนที่เบิกจ่าย", min_value=0.1)
                
                if st.form_submit_button("🚀 ตัดสต็อก & จ่ายวัตถุดิบ"):
                    rm_code = sel_rm.split(" - ")[0]
                    idx = st.session_state.inventory_rm[st.session_state.inventory_rm['code'] == rm_code].index[0]
                    curr_qty = st.session_state.inventory_rm.loc[idx, 'qty']
                    
                    if curr_qty < iss_qty:
                        st.error("สต็อก RM ไม่พอ!")
                    else:
                        st.session_state.inventory_rm.loc[idx, 'qty'] -= iss_qty
                        iss_entry = {
                            "job_id": sel_job, "target_wip": target_wip, "rm_code": rm_code,
                            "rm_name": st.session_state.inventory_rm.loc[idx, 'name'],
                            "qty": iss_qty, "unit": st.session_state.inventory_rm.loc[idx, 'unit'],
                            "issue_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        st.session_state.issued_materials = pd.concat([st.session_state.issued_materials, pd.DataFrame([iss_entry])], ignore_index=True)
                        st.success("จ่ายวัตถุดิบเรียบร้อย!")
                        st.rerun()

    # -------------------------------------------------------------
    # หน้าย่อย 3: ติดตาม & เคลื่อนย้าย WIP
    # -------------------------------------------------------------
    elif st.session_state.current_page == "track_wip":
        st.subheader("🔄 ระบบติดตาม WIP & การไหลของงาน")
        st.dataframe(st.session_state.jobs, use_container_width=True)
        st.markdown("---")
        
        if not st.session_state.jobs.empty:
            with st.form("move_wip"):
                sel_job_id = st.selectbox("เลือก Job ที่ต้องการย้ายขั้นตอน:", st.session_state.jobs['job_id'].tolist())
                job_curr_info = st.session_state.jobs[st.session_state.jobs['job_id'] == sel_job_id].iloc[0]
                
                st.info(f"📍 ขั้นตอนปัจจุบัน: **{job_curr_info['current_stage']}**")
                
                next_stage_options = [
                    "WIP 2: Dry 1 (ประกบชั้นที่ 1)", "WIP 3: Dry 2 (ประกบชั้นที่ 2)",
                    "WIP 4: Slit (ตัดแบ่งม้วน)", "WIP 5: Bag Making (ขึ้นรูปถุง/ซอง)",
                    "WIP 6: Spout (ติดจุก)", "WIP 7: Packing (แพ็กเกจจิ้ง)",
                    "FG: สินค้าสำเร็จรูป (โอนเข้าคลัง FG)"
                ]
                selected_next = st.selectbox("เลือกขั้นตอนถัดไป:", next_stage_options)
                completed_qty = st.number_input("จำนวนที่ผลิตได้", min_value=1, value=int(job_curr_info['target_qty']))
                
                if st.form_submit_button("🚀 บันทึกย้ายขั้นตอน"):
                    j_idx = st.session_state.jobs[st.session_state.jobs['job_id'] == sel_job_id].index[0]
                    if "FG: สินค้าสำเร็จรูป" in selected_next:
                        fg_item = {
                            "job_id": sel_job_id, "product_name": job_curr_info['product_name'],
                            "qty": completed_qty, "unit": job_curr_info['unit'],
                            "in_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        st.session_state.inventory_fg = pd.concat([st.session_state.inventory_fg, pd.DataFrame([fg_item])], ignore_index=True)
                        st.session_state.jobs.loc[j_idx, 'current_stage'] = "FG: สำเร็จรูป (เสร็จสิ้น)"
                        st.success("โอนเข้าคลัง FG เรียบร้อย!")
                    else:
                        st.session_state.jobs.loc[j_idx, 'current_stage'] = selected_next
                        st.success("อัปเดตขั้นตอนเรียบร้อย!")
                    st.rerun()

    # -------------------------------------------------------------
    # หน้าย่อย 4: คลังสินค้าสำเร็จรูป (FG Stock)
    # -------------------------------------------------------------
    elif st.session_state.current_page == "fg_stock":
        st.subheader("🏆 รายการสินค้าสำเร็จรูปในคลัง (FG Stock)")
        st.dataframe(st.session_state.inventory_fg, use_container_width=True)

    # -------------------------------------------------------------
    # หน้าย่อย 5: ประวัติการทำรายการ
    # -------------------------------------------------------------
    elif st.session_state.current_page == "history":
        st.subheader("📜 ประวัติการจ่ายวัตถุดิบเข้า WIP")
        st.dataframe(st.session_state.issued_materials, use_container_width=True)

# =====================================================================
# 4. ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_screen()
    else:
        main_app()
