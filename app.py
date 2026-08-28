import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ระบบควบคุมสินค้า & การผลิต (Multi-WIP)", layout="wide", initial_sidebar_state="collapsed")

# ซ่อนแถบ Sidebar
st.markdown("""
    <style>
        [data-testid="collapsedControl"] {display: none;}
        section[data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 1. USER DATABASE & STAGES
# =====================================================================
USER_DATABASE = {
    "admin": {"password": "888", "name": "ผู้ดูแลระบบ", "role": "Admin"},
    "wh_staff": {"password": "123", "name": "พนักงานคลังสินค้า", "role": "Warehouse"},
    "prod_staff": {"password": "123", "name": "พนักงานฝ่ายผลิต", "role": "Production"}
}

STAGES = [
    "WIP 1: Print (พิมพ์ลาย)",
    "WIP 2: Dry 1 (ประกบชั้นที่ 1)",
    "WIP 3: Dry 2 (ประกบชั้นที่ 2)",
    "WIP 4: Slit (ตัดแบ่งม้วน)",
    "WIP 5: Bag Making (ขึ้นรูปถุง/ซอง)",
    "WIP 6: Spout (ติดจุก)",
    "WIP 7: Packing (บรรจุกล่อง)"
]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "main_menu"

# --- ฐานข้อมูลจำลอง ---
if "inventory_rm" not in st.session_state:
    st.session_state.inventory_rm = pd.DataFrame([
        {"code": "RM-001", "name": "ม้วนฟิล์ม PET 12u", "qty": 5000.0, "unit": "Kg"},
        {"code": "RM-002", "name": "ม้วนฟิล์ม LLDPE 40u", "qty": 4000.0, "unit": "Kg"},
        {"code": "RM-003", "name": "หมึกพิมพ์ Solvent Base", "qty": 300.0, "unit": "Kg"},
        {"code": "RM-004", "name": "กาว PU Dry Lamination", "qty": 500.0, "unit": "Kg"},
        {"code": "RM-005", "name": "จุกฝาเกลียว (Spout 10mm)", "qty": 50000.0, "unit": "ชิ้น"}
    ])

# ตารางเก็บ WIP คงเหลือของแต่ละขั้นตอนแยกตาม Job
if "inventory_wip" not in st.session_state:
    st.session_state.inventory_wip = pd.DataFrame(columns=["job_id", "stage", "qty", "unit"])

if "inventory_fg" not in st.session_state:
    st.session_state.inventory_fg = pd.DataFrame([
        {"job_id": "JOB-2026-000", "product_name": "ซองกาแฟ 250g", "qty": 15000, "unit": "ซอง", "in_date": "2026-08-20"}
    ])

if "jobs" not in st.session_state:
    st.session_state.jobs = pd.DataFrame([
        {"job_id": "JOB-2026-001", "product_name": "ซองติดจุก 250ml", "target_qty": 20000, "unit": "ซอง"}
    ])

if "issued_materials" not in st.session_state:
    st.session_state.issued_materials = pd.DataFrame(columns=["job_id", "target_wip", "mat_type", "code_name", "qty", "unit", "issue_date"])

# Helper function สำหรับอัปเดตสต็อก WIP
def add_wip_qty(job_id, stage, qty, unit):
    df = st.session_state.inventory_wip
    match = df[(df['job_id'] == job_id) & (df['stage'] == stage)]
    if not match.empty:
        idx = match.index[0]
        st.session_state.inventory_wip.loc[idx, 'qty'] += qty
    else:
        new_row = {"job_id": job_id, "stage": stage, "qty": qty, "unit": unit}
        st.session_state.inventory_wip = pd.concat([st.session_state.inventory_wip, pd.DataFrame([new_row])], ignore_index=True)

# Helper function สำหรับลดสต็อก WIP เมื่อถูกดึงไปใช้
def deduce_wip_qty(job_id, stage, qty):
    df = st.session_state.inventory_wip
    match = df[(df['job_id'] == job_id) & (df['stage'] == stage)]
    if not match.empty:
        idx = match.index[0]
        st.session_state.inventory_wip.loc[idx, 'qty'] -= qty

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
# 3. MAIN APPLICATION
# =====================================================================
def main_app():
    user = st.session_state.user_info
    role = user["role"]

    # Header
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.title("🏭 ระบบคลังสินค้า & ควบคุมกระบวนการผลิต (Multi-WIP)")
        st.caption(f"👤 ผู้ใช้งาน: **{user['name']}** | สิทธิ์การใช้งาน: **{role}**")
    with head_col2:
        st.write("")
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()
            
    st.markdown("---")

    # -------------------------------------------------------------
    # เมนูกลาง (Main Dashboard)
    # -------------------------------------------------------------
    if st.session_state.current_page == "main_menu":
        col_wh, col_prod = st.columns(2)
        
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
                if st.button("📜 5. ประวัติการเบิก/จ่ายสินค้า", use_container_width=True):
                    st.session_state.current_page = "history"
                    st.rerun()
            else:
                st.error("🔒 คุณไม่มีสิทธิ์เข้าถึงส่วนงานคลังสินค้า")

        with col_prod:
            st.markdown("### 🏭 Production & WIP Control")
            if role in ["Admin", "Production"]:
                if st.button("🏗️ 2. เปิด Job Order ใหม่", use_container_width=True):
                    st.session_state.current_page = "open_job"
                    st.rerun()
                st.write("")
                if st.button("🔄 3. บันทึกผลิต & ดึง WIP/RM มาทำต่อ", use_container_width=True):
                    st.session_state.current_page = "process_wip"
                    st.rerun()
                st.write("")
                if st.button("📊 6. ดูสต็อก WIP รายแผนก", use_container_width=True):
                    st.session_state.current_page = "wip_stock"
                    st.rerun()
            else:
                st.error("🔒 คุณไม่มีสิทธิ์เข้าถึงส่วนงานการผลิต")

    else:
        if st.button("⬅️ กลับสู่หน้าหลัก (Main Dashboard)"):
            st.session_state.current_page = "main_menu"
            st.rerun()
        st.markdown("---")

    # -------------------------------------------------------------
    # หน้า 1: คลังวัตถุดิบ (RM Stock)
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
    # หน้า 2: เปิด Job Order ใหม่
    # -------------------------------------------------------------
    elif st.session_state.current_page == "open_job":
        st.subheader("🏗️ เปิด Job Order ใหม่")
        with st.form("create_job"):
            j_id = st.text_input("เลขที่ Job Order (เช่น JOB-2026-002)")
            p_name = st.text_input("ชื่อสินค้า/ซองบรรจุภัณฑ์")
            t_qty = st.number_input("จำนวนที่ต้องการผลิตรวม", min_value=1, value=10000)
            u_name = st.selectbox("หน่วยผลิตหลัก", ["ซอง", "ม้วน", "ชิ้น", "Kg"])
            
            if st.form_submit_button("💾 บันทึกเปิด Job"):
                job_data = {"job_id": j_id, "product_name": p_name, "target_qty": t_qty, "unit": u_name}
                st.session_state.jobs = pd.concat([st.session_state.jobs, pd.DataFrame([job_data])], ignore_index=True)
                st.success(f"เปิด Job {j_id} เรียบร้อยแล้ว")
                st.rerun()
        
        st.markdown("### รายการ Job ทั้งหมด")
        st.dataframe(st.session_state.jobs, use_container_width=True)

    # -------------------------------------------------------------
    # หน้า 3: บันทึกการผลิต & ดึง WIP/RM มาทำต่อ (จุดสำคัญ)
    # -------------------------------------------------------------
    elif st.session_state.current_page == "process_wip":
        st.subheader("🔄 บันทึกการผลิตประจำแผนก (ดึง RM / WIP ก่อนหน้า มาผลิตต่อ)")
        
        if st.session_state.jobs.empty:
            st.warning("ยังไม่มี Job Order ในระบบ กรุณาเปิด Job ก่อน")
        else:
            job_list = st.session_state.jobs['job_id'].tolist()
            sel_job = st.selectbox("1️⃣ เลือก Job Order ที่ต้องการทำงาน:", job_list)
            
            # ดึงข้อมูล RM และ WIP ของ Job นี้ที่มีอยู่
            current_wip_df = st.session_state.inventory_wip[
                (st.session_state.inventory_wip['job_id'] == sel_job) & 
                (st.session_state.inventory_wip['qty'] > 0)
            ]
            
            st.markdown("---")
            col_in, col_out = st.columns(2)
            
            with col_in:
                st.markdown("#### 📥 2. เบิกวัตถุดิบ / WIP เข้ามาผลิต")
                input_type = st.radio("ประเภทสิ่งที่นำมาใช้ผลิต:", ["เบิก RM จากคลังหลัก", "ดึง WIP จากแผนกก่อนหน้า"])
                
                used_rm_code = None
                used_wip_stage = None
                available_max = 0.0
                unit_label = ""

                if input_type == "เบิก RM จากคลังหลัก":
                    rm_opts = [f"{r['code']} - {r['name']} (เหลือ {r['qty']} {r['unit']})" for _, r in st.session_state.inventory_rm.iterrows()]
                    if rm_opts:
                        sel_rm_str = st.selectbox("เลือกวัตถุดิบ RM:", rm_opts)
                        used_rm_code = sel_rm_str.split(" - ")[0]
                        rm_data = st.session_state.inventory_rm[st.session_state.inventory_rm['code'] == used_rm_code].iloc[0]
                        available_max = float(rm_data['qty'])
                        unit_label = rm_data['unit']
                else:
                    if current_wip_df.empty:
                        st.info("⚠️ ยังไม่มี WIP ของแผนกก่อนหน้าสำหรับ Job นี้")
                    else:
                        wip_opts = [f"{w['stage']} (คงเหลือ {w['qty']} {w['unit']})" for _, w in current_wip_df.iterrows()]
                        sel_wip_str = st.selectbox("เลือก WIP จากแผนกก่อนหน้า:", wip_opts)
                        used_wip_stage = sel_wip_str.split(" (")[0]
                        wip_data = current_wip_df[current_wip_df['stage'] == used_wip_stage].iloc[0]
                        available_max = float(wip_data['qty'])
                        unit_label = wip_data['unit']

                input_qty = st.number_input(f"จำนวนที่นำมาใช้ (สูงสุด {available_max} {unit_label}):", min_value=0.0, max_value=available_max if available_max > 0 else 0.0, value=0.0)

            with col_out:
                st.markdown("#### 📤 3. ผลลัพธ์การผลิตที่ได้ (ไปยัง WIP ถัดไป)")
                target_stage = st.selectbox("แผนกที่กำลังทำการผลิต (Output):", STAGES + ["FG: สินค้าสำเร็จรูป (เข้าคลัง FG)"])
                output_qty = st.number_input("จำนวนผลผลิตที่ทำเสร็จ:", min_value=0.1, value=1.0)
                output_unit = st.selectbox("หน่วยนับผลผลิต:", ["Kg", "ม้วน", "ซอง", "ชิ้น"])

            st.markdown("---")
            if st.button("🚀 บันทึกการผลิต & ตัดสต็อกสะสม", use_container_width=True):
                if input_qty <= 0:
                    st.error("กรุณาระบุจำนวนวัตถุดิบ/WIP ที่นำมาใช้ผลิต")
                else:
                    # 1. ตัดสต็อกขาเข้า
                    if input_type == "เบิก RM จากคลังหลัก" and used_rm_code:
                        rm_idx = st.session_state.inventory_rm[st.session_state.inventory_rm['code'] == used_rm_code].index[0]
                        st.session_state.inventory_rm.loc[rm_idx, 'qty'] -= input_qty
                        mat_name = st.session_state.inventory_rm.loc[rm_idx, 'name']
                        # บันทึกประวัติ
                        iss_entry = {"job_id": sel_job, "target_wip": target_stage, "mat_type": "RM", "code_name": f"{used_rm_code} ({mat_name})", "qty": input_qty, "unit": unit_label, "issue_date": datetime.now().strftime("%Y-%m-%d %H:%M")}
                        st.session_state.issued_materials = pd.concat([st.session_state.issued_materials, pd.DataFrame([iss_entry])], ignore_index=True)

                    elif input_type == "ดึง WIP จากแผนกก่อนหน้า" and used_wip_stage:
                        deduce_wip_qty(sel_job, used_wip_stage, input_qty)
                        iss_entry = {"job_id": sel_job, "target_wip": target_stage, "mat_type": "WIP", "code_name": used_wip_stage, "qty": input_qty, "unit": unit_label, "issue_date": datetime.now().strftime("%Y-%m-%d %H:%M")}
                        st.session_state.issued_materials = pd.concat([st.session_state.issued_materials, pd.DataFrame([iss_entry])], ignore_index=True)

                    # 2. เพิ่มสต็อกขาออก
                    if target_stage.startswith("FG:"):
                        job_info = st.session_state.jobs[st.session_state.jobs['job_id'] == sel_job].iloc[0]
                        fg_entry = {"job_id": sel_job, "product_name": job_info['product_name'], "qty": output_qty, "unit": output_unit, "in_date": datetime.now().strftime("%Y-%m-%d %H:%M")}
                        st.session_state.inventory_fg = pd.concat([st.session_state.inventory_fg, pd.DataFrame([fg_entry])], ignore_index=True)
                        st.success(f"บันทึกการผลิตสำเร็จ! สินค้าโอนเข้าคลัง FG เรียบร้อยแล้ว")
                    else:
                        add_wip_qty(sel_job, target_stage, output_qty, output_unit)
                        st.success(f"บันทึกการผลิตสำเร็จ! งานถูกส่งไปเป็นสต็อกคงเหลืออยู่ที่ **{target_stage}** เรียบร้อยแล้ว")

                    st.rerun()

    # -------------------------------------------------------------
    # หน้า 4: สต็อกสินค้าสำเร็จรูป (FG Stock)
    # -------------------------------------------------------------
    elif st.session_state.current_page == "fg_stock":
        st.subheader("🏆 รายการสินค้าสำเร็จรูปในคลัง (FG Stock)")
        st.dataframe(st.session_state.inventory_fg, use_container_width=True)

    # -------------------------------------------------------------
    # หน้า 5: ประวัติการทำรายการ
    # -------------------------------------------------------------
    elif st.session_state.current_page == "history":
        st.subheader("📜 ประวัติการเบิก RM และการดึง WIP ไปใช้งาน")
        st.dataframe(st.session_state.issued_materials, use_container_width=True)

    # -------------------------------------------------------------
    # หน้า 6: สต็อก WIP รายแผนก (ดูยอดคงเหลือที่รอผลิตต่อ)
    # -------------------------------------------------------------
    elif st.session_state.current_page == "wip_stock":
        st.subheader("📊 สต็อก WIP คงเหลือในแต่ละแผนก (รอแผนกถัดไปมาดึง)")
        st.dataframe(st.session_state.inventory_wip[st.session_state.inventory_wip['qty'] > 0], use_container_width=True)

# =====================================================================
# 4. ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_screen()
    else:
        main_app()
