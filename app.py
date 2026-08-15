import streamlit as st
import pandas as pd
from datetime import datetime

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Flexible Packaging ERP & WIP System", layout="wide", page_icon="🏭")

# =====================================================================
# 1. INITIAL SESSION STATES & MOCK DATA
# =====================================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# สิทธิ์ผู้ใช้งาน
USER_DATABASE = {
    "admin": {"password": "88888888", "name": "ผู้ดูแลระบบ", "role": "Admin"},
    "prajak": {"password": "123456", "name": "ผู้จัดการโรงงาน", "role": "Manager"},
    "pram": {"password": "55555", "name": "ผู้จัดการฝ่ายผลิต", "role": "Manager"},
    "store": {"password": "store123", "name": "พนักงานคลังวัตถุดิบ", "role": "Store"},
    "planner": {"password": "plan123", "name": "ฝ่ายวางแผนการผลิต", "role": "Planner"},
    "sales": {"password": "sales123", "name": "ฝ่ายขายและจัดส่ง", "role": "Sales"}
}

# 8 WIP Production Steps
WIP_STAGES = [
    "WIP 1: เตรียมวัตถุดิบ & แม่พิมพ์ (Pre-Production)",
    "WIP 2: พิมพ์ลาย (Printing)",
    "WIP 3: ประกบแห้ง (Dry Lamination)",
    "WIP 4: ประกบไร้ตัวทำละลาย (Solventless Lamination)",
    "WIP 5: บ่มกาว (Curing / Aging Room)",
    "WIP 6: ตัดม้วน (Slitting)",
    "WIP 7: ขึ้นรูปถุง / พับซอง (Bag / Pouch Making)",
    "WIP 8: ตรวจสอบคุณภาพและแพ็กเกจ (QC & Packaging)"
]

# 1. สต็อกวัตถุดิบและอุปกรณ์ (RM & Tooling)
if "rm_inventory" not in st.session_state:
    st.session_state.rm_inventory = pd.DataFrame([
        {"code": "RM-FILM-001", "name": "ม้วนฟิล์ม PET 12 micron", "category": "ม้วนฟิล์ม", "qty": 2500.0, "unit": "Kg"},
        {"code": "RM-FILM-002", "name": "ม้วนฟิล์ม LLDPE 40 micron", "category": "ม้วนฟิล์ม", "qty": 3800.0, "unit": "Kg"},
        {"code": "RM-CHEM-001", "name": "กาวประกบ PU (Solventless)", "category": "กาว/เคมีภัณฑ์", "qty": 450.0, "unit": "Kg"},
        {"code": "RM-CYL-101", "name": "บล็อกแม่พิมพ์ - ซองกาแฟ 250g (ชุด 5 สี)", "category": "บล็อกแม่พิมพ์", "qty": 1.0, "unit": "ชุด"},
    ])

# 2. รายการ Job การผลิต
if "wip_jobs" not in st.session_state:
    st.session_state.wip_jobs = pd.DataFrame([
        {
            "job_id": "JOB-2026-001",
            "product_name": "ถุงกาแฟสกรีน 250g",
            "customer": "บริษัท กาแฟไทย จำกัด",
            "target_qty": 50000,
            "unit": "ซอง",
            "current_stage": "WIP 2: พิมพ์ลาย (Printing)",
            "start_date": "2026-08-10",
            "remark": "พิมพ์ 5 สี ด้านล่างมีซิปล็อค"
        }
    ])

# 3. รายการผูกวัตถุดิบสำหรับแต่ละ Job (Job Materials Requirement / BOM & Issue Status)
if "job_materials" not in st.session_state:
    st.session_state.job_materials = pd.DataFrame([
        {
            "job_id": "JOB-2026-001",
            "rm_code": "RM-CYL-101",
            "rm_name": "บล็อกแม่พิมพ์ - ซองกาแฟ 250g (ชุด 5 สี)",
            "req_qty": 1.0,
            "unit": "ชุด",
            "target_wip": "WIP 1: เตรียมวัตถุดิบ & แม่พิมพ์ (Pre-Production)",
            "status": "ISSUED (เบิกแล้ว)"
        },
        {
            "job_id": "JOB-2026-001",
            "rm_code": "RM-FILM-001",
            "rm_name": "ม้วนฟิล์ม PET 12 micron",
            "req_qty": 350.0,
            "unit": "Kg",
            "target_wip": "WIP 2: พิมพ์ลาย (Printing)",
            "status": "ISSUED (เบิกแล้ว)"
        },
        {
            "job_id": "JOB-2026-001",
            "rm_code": "RM-CHEM-001",
            "rm_name": "กาวประกบ PU (Solventless)",
            "req_qty": 50.0,
            "unit": "Kg",
            "target_wip": "WIP 4: ประกบไร้ตัวทำละลาย (Solventless Lamination)",
            "status": "PENDING (รอเบิก)"
        },
        {
            "job_id": "JOB-2026-001",
            "rm_code": "RM-FILM-002",
            "rm_name": "ม้วนฟิล์ม LLDPE 40 micron",
            "req_qty": 400.0,
            "unit": "Kg",
            "target_wip": "WIP 4: ประกบไร้ตัวทำละลาย (Solventless Lamination)",
            "status": "PENDING (รอเบิก)"
        }
    ])

# 4. คลังสินค้าสำเร็จรูป (Finished Goods - FG)
if "fg_inventory" not in st.session_state:
    st.session_state.fg_inventory = pd.DataFrame([
        {"fg_code": "FG-POUCH-001", "name": "ถุงซิปล็อคใส 15x23 cm", "customer": "บจก. เอสเอ็มอี ไทย", "in_stock": 15000, "unit": "ซอง", "last_update": "2026-08-14"},
        {"fg_code": "FG-POUCH-002", "name": "ซองฟอยล์ทึบซีล 3 ด้าน", "customer": "หจก. อาหารไทยสด", "in_stock": 8500, "unit": "ซอง", "last_update": "2026-08-15"}
    ])

# 5. ประวัติการขาย/ตัดออก (FG Sales/Delivery Log)
if "fg_sales_log" not in st.session_state:
    st.session_state.fg_sales_log = pd.DataFrame(columns=["date", "fg_code", "name", "customer", "sold_qty", "unit", "do_number", "operator"])

# =====================================================================
# 2. LOGIN SCREEN
# =====================================================================
def login_screen():
    st.markdown("<h2 style='text-align: center;'>🏭 ระบบคลังและการผลิตบรรจุภัณฑ์ชนิดอ่อนตัว</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>Flexible Packaging Production & Multi-WIP Material Management</h4>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username (ชื่อผู้ใช้)")
            password = st.text_input("Password (รหัสผ่าน)", type="password")
            submit = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)
            
            if submit:
                if username in USER_DATABASE and USER_DATABASE[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_info = USER_DATABASE[username]
                    st.success("เข้าสู่ระบบสำเร็จ!")
                    st.rerun()
                else:
                    st.error("Username หรือ Password ไม่ถูกต้อง")

# =====================================================================
# 3. MAIN APPLICATION
# =====================================================================
def main_app():
    user = st.session_state.user_info
    
    # Sidebar
    st.sidebar.title(f"👤 สวัสดี: {user['name']}")
    st.sidebar.caption(f"สิทธิ์: {user['role']}")
    
    main_menu = st.sidebar.radio(
        "เลือกส่วนงาน:",
        [
            "📦 1. คลังวัตถุดิบและอุปกรณ์ (Raw Materials & Tools)",
            "🏭 2. ติดตามไลน์ผลิต 8 ขั้นตอน (WIP & Material Issue)",
            "🚚 3. คลังสินค้าสำเร็จรูปและการขาย (FG & Sales)"
        ]
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 ออกจากระบบ (Logout)", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()

    # =================================================================
    # ส่วนที่ 1: คลังวัตถุดิบและอุปกรณ์ (RM & TOOLING)
    # =================================================================
    if main_menu.startswith("📦 1"):
        st.title("📦 คลังวัตถุดิบและอุปกรณ์การผลิต")
        st.caption("จัดเก็บและติดตามสต็อกม้วนฟิล์ม, กาว/เคมีภัณฑ์ และบล็อกแม่พิมพ์")
        
        tab1, tab2 = st.tabs(["📋 รายการสต็อกปัจจุบัน", "➕ รับเข้าวัตถุดิบใหม่"])
        
        with tab1:
            st.subheader("รายการวัตถุดิบและแม่พิมพ์คงคลัง")
            st.dataframe(st.session_state.rm_inventory, use_container_width=True)
            
        with tab2:
            st.subheader("บันทึกรับวัตถุดิบเข้าคลัง")
            with st.form("rm_update_form"):
                rm_codes = [f"{r['code']} - {r['name']}" for _, r in st.session_state.rm_inventory.iterrows()]
                selected_rm = st.selectbox("เลือกวัตถุดิบ/แม่พิมพ์:", rm_codes)
                change_qty = st.number_input("จำนวนที่รับเข้า:", min_value=0.1, step=10.0)
                submit_rm = st.form_submit_button("📥 บันทึกรับเข้าสต็อก")
                
                if submit_rm:
                    code_target = selected_rm.split(" - ")[0]
                    idx = st.session_state.rm_inventory[st.session_state.rm_inventory['code'] == code_target].index[0]
                    st.session_state.rm_inventory.loc[idx, 'qty'] += change_qty
                    st.success(f"เพิ่มสต็อก {code_target} จำนวน {change_qty} เรียบร้อย!")
                    st.rerun()

    # =================================================================
    # ส่วนที่ 2: ติดตามไลน์ผลิต 8 ขั้นตอน & การเบิกวัตถุดิบเข้า WIP
    # =================================================================
    elif main_menu.startswith("🏭 2"):
        st.title("🏭 ติดตามไลน์ผลิต 8 ขั้นตอน & เบิกวัตถุดิบเข้า WIP")
        
        tab_wip_1, tab_wip_2, tab_wip_3, tab_wip_4 = st.tabs([
            "📊 สถานะ Job & การเบิกวัตถุดิบ", 
            "📤 เบิกวัตถุดิบเข้า WIP", 
            "🔄 อัปเดตขั้นตอน Job", 
            "➕ เปิด Job ผลิตใหม่ + กำหนด BOM"
        ])
        
        # TAB 1: OVERVIEW & MATERIAL TRACKING
        with tab_wip_1:
            st.subheader("1. รายการ Job Order ทั้งหมด")
            st.dataframe(st.session_state.wip_jobs, use_container_width=True)
            
            st.markdown("---")
            st.subheader("2. ตรวจสอบการใช้วัตถุดิบแยกตาม WIP ของ Job")
            
            if not st.session_state.wip_jobs.empty:
                job_list_view = st.selectbox("เลือก Job Order เพื่อดูรายละเอียดการใช้วัตถุดิบ:", st.session_state.wip_jobs['job_id'].tolist())
                
                job_mat_filtered = st.session_state.job_materials[st.session_state.job_materials['job_id'] == job_list_view]
                st.write(f"📋 **วัตถุดิบและ WIP ที่ต้องส่งไปใช้ สำหรับ `{job_list_view}`:**")
                st.dataframe(job_mat_filtered, use_container_width=True)
            else:
                st.info("ยังไม่มีข้อมูล Job ผลิต")

        # TAB 2: MATERIAL ISSUE TO SPECIFIC WIP
        with tab_wip_2:
            st.subheader("📤 เบิกวัตถุดิบจ่ายตรงไปยัง WIP")
            st.caption("ระบบจะตัดสต็อกวัตถุดิบจากคลัง และเปลี่ยนสถานะวัตถุดิบเป็น ISSUED")
            
            # กรองเฉพาะวัตถุดิบที่ยังไม่ได้เบิก (PENDING)
            pending_mats = st.session_state.job_materials[st.session_state.job_materials['status'] == "PENDING (รอเบิก)"]
            
            if pending_mats.empty:
                st.success("🎉 วัตถุดิบสำหรับทุก Job ถูกเบิกจ่ายเข้า WIP ครบถ้วนแล้ว!")
            else:
                with st.form("issue_material_form"):
                    mat_options = [
                        f"ID:{idx} | Job: {r['job_id']} | วัตถุดิบ: {r['rm_name']} | ส่งไป: {r['target_wip']} | จำนวน: {r['req_qty']} {r['unit']}"
                        for idx, r in pending_mats.iterrows()
                    ]
                    selected_mat_item = st.selectbox("เลือกรายการวัตถุดิบที่ต้องการเบิก:", mat_options)
                    submit_issue = st.form_submit_button("🚀 ยืนยันการเบิกจ่ายวัตถุดิบเข้า WIP")
                    
                    if submit_issue:
                        mat_idx = int(selected_mat_item.split(" | ")[0].replace("ID:", ""))
                        target_job = st.session_state.job_materials.loc[mat_idx, 'job_id']
                        rm_code = st.session_state.job_materials.loc[mat_idx, 'rm_code']
                        req_qty = st.session_state.job_materials.loc[mat_idx, 'req_qty']
                        target_wip = st.session_state.job_materials.loc[mat_idx, 'target_wip']
                        
                        # ตรวจสอบสต็อกคลัง
                        rm_idx = st.session_state.rm_inventory[st.session_state.rm_inventory['code'] == rm_code].index[0]
                        current_stock = st.session_state.rm_inventory.loc[rm_idx, 'qty']
                        
                        if current_stock >= req_qty:
                            # ตัดสต็อก RM
                            st.session_state.rm_inventory.loc[rm_idx, 'qty'] -= req_qty
                            # อัปเดตสถานะใน Job Materials
                            st.session_state.job_materials.loc[mat_idx, 'status'] = "ISSUED (เบิกแล้ว)"
                            st.success(f"เบิก `{rm_code}` จำนวน {req_qty} จ่ายเข้า `{target_wip}` สำหรับ Job `{target_job}` เรียบร้อย!")
                            st.rerun()
                        else:
                            st.error(f"วัตถุดิบในคลังไม่พอ! มีอยู่ {current_stock} แต่ต้องใช้ {req_qty}")

        # TAB 3: UPDATE JOB STAGE
        with tab_wip_3:
            st.subheader("🔄 ย้ายขั้นตอนการผลิตของ Job")
            with st.form("move_wip_form"):
                job_list = [f"{r['job_id']} | {r['product_name']}" for _, r in st.session_state.wip_jobs.iterrows()]
                selected_job = st.selectbox("เลือก Job Order:", job_list)
                new_stage = st.selectbox("ย้ายไปยังขั้นตอน:", WIP_STAGES)
                submit_wip = st.form_submit_button("🔄 อัปเดตสถานะ WIP")
                
                if submit_wip:
                    job_id_target = selected_job.split(" | ")[0]
                    idx = st.session_state.wip_jobs[st.session_state.wip_jobs['job_id'] == job_id_target].index[0]
                    st.session_state.wip_jobs.loc[idx, 'current_stage'] = new_stage
                    st.success(f"อัปเดต Job `{job_id_target}` ไปยัง `{new_stage}` เรียบร้อย!")
                    st.rerun()

        # TAB 4: NEW JOB & MULTI-MATERIAL BOM
        with tab_wip_4:
            st.subheader("➕ เปิด Job ผลิตใหม่ พร้อมกำหนดวัตถุดิบประจำ WIP")
            
            with st.form("new_job_multi_form"):
                col_j1, col_j2 = st.columns(2)
                with col_j1:
                    new_job_id = st.text_input("เลขที่ Job Order (เช่น JOB-2026-002)")
                    p_name = st.text_input("ชื่อสินค้าบรรจุภัณฑ์")
                with col_j2:
                    cust_name = st.text_input("ชื่อลูกค้า")
                    t_qty = st.number_input("จำนวนที่ผลิต:", min_value=100, step=1000)
                
                st.markdown("---")
                st.markdown("##### 🛠️ เลือกวัตถุดิบที่ต้องใช้ใน Job นี้ (เลือกได้สูงสุด 4 ตัว และระบุ WIP ปลายทาง):")
                
                rm_list = [f"{r['code']} | {r['name']} ({r['qty']} {r['unit']})" for _, r in st.session_state.rm_inventory.iterrows()]
                
                # วัตถุดิบตัวที่ 1
                col_m1_a, col_m1_b, col_m1_c = st.columns([2, 1, 2])
                with col_m1_a:
                    m1_rm = st.selectbox("วัตถุดิบ 1:", ["- ไม่ระบุ -"] + rm_list, key="m1")
                with col_m1_b:
                    m1_qty = st.number_input("จำนวนที่ใช้:", min_value=0.0, step=10.0, key="m1_q")
                with col_m1_c:
                    m1_wip = st.selectbox("ส่งไปใช้ที่ WIP:", WIP_STAGES, key="m1_w")
                    
                # วัตถุดิบตัวที่ 2
                col_m2_a, col_m2_b, col_m2_c = st.columns([2, 1, 2])
                with col_m2_a:
                    m2_rm = st.selectbox("วัตถุดิบ 2:", ["- ไม่ระบุ -"] + rm_list, key="m2")
                with col_m2_b:
                    m2_qty = st.number_input("จำนวนที่ใช้:", min_value=0.0, step=10.0, key="m2_q")
                with col_m2_c:
                    m2_wip = st.selectbox("ส่งไปใช้ที่ WIP:", WIP_STAGES, index=1, key="m2_w")

                # วัตถุดิบตัวที่ 3
                col_m3_a, col_m3_b, col_m3_c = st.columns([2, 1, 2])
                with col_m3_a:
                    m3_rm = st.selectbox("วัตถุดิบ 3:", ["- ไม่ระบุ -"] + rm_list, key="m3")
                with col_m3_b:
                    m3_qty = st.number_input("จำนวนที่ใช้:", min_value=0.0, step=10.0, key="m3_q")
                with col_m3_c:
                    m3_wip = st.selectbox("ส่งไปใช้ที่ WIP:", WIP_STAGES, index=3, key="m3_w")

                submit_create_job = st.form_submit_button("🚀 บันทึกเปิด Job ผลิต")
                
                if submit_create_job:
                    if new_job_id and p_name:
                        # 1. เพิ่ม Job ใหม่
                        new_job_row = {
                            "job_id": new_job_id, "product_name": p_name, "customer": cust_name,
                            "target_qty": t_qty, "unit": "ซอง",
                            "current_stage": WIP_STAGES[0],
                            "start_date": datetime.now().strftime("%Y-%m-%d"),
                            "remark": ""
                        }
                        st.session_state.wip_jobs = pd.concat([st.session_state.wip_jobs, pd.DataFrame([new_job_row])], ignore_index=True)
                        
                        # 2. เพิ่มรายการวัตถุดิบผูก Job
                        mats_to_add = []
                        for m_select, q_val, w_target in [(m1_rm, m1_qty, m1_wip), (m2_rm, m2_qty, m2_wip), (m3_rm, m3_qty, m3_wip)]:
                            if m_select != "- ไม่ระบุ -" and q_val > 0:
                                code_part = m_select.split(" | ")[0]
                                name_part = m_select.split(" | ")[1].split(" (")[0]
                                unit_part = m_select.split("(")[1].split(" ")[1].replace(")", "")
                                mats_to_add.append({
                                    "job_id": new_job_id,
                                    "rm_code": code_part,
                                    "rm_name": name_part,
                                    "req_qty": q_val,
                                    "unit": unit_part,
                                    "target_wip": w_target,
                                    "status": "PENDING (รอเบิก)"
                                })
                        
                        if mats_to_add:
                            st.session_state.job_materials = pd.concat([st.session_state.job_materials, pd.DataFrame(mats_to_add)], ignore_index=True)
                        
                        st.success(f"เปิด Job `{new_job_id}` และบันทึกสูตรวัตถุดิบเรียบร้อยแล้ว!")
                        st.rerun()
                    else:
                        st.error("กรุณากรอก Job ID และชื่อสินค้าให้ครบถ้วน")

    # =================================================================
    # ส่วนที่ 3: คลังสินค้าสำเร็จรูป (FINISHED GOODS - FG & SALES)
    # =================================================================
    elif main_menu.startswith("🚚 3"):
        st.title("🚚 คลังสินค้าสำเร็จรูปและการจัดส่ง (FG & Delivery)")
        st.caption("ตรวจเช็คสินค้าพร้อมขาย รับเข้าจากผลิต และตัดจ่ายส่งมอบลูกค้า")
        
        fg_tab1, fg_tab2, fg_tab3 = st.tabs(["📦 สินค้าคงคลัง FG", "📥 รับเข้า FG จากการผลิต", "🚛 บันทึกการส่งมอบ/ขายออก"])
        
        with fg_tab1:
            st.subheader("รายการบรรจุภัณฑ์สำเร็จรูปพร้อมขาย (FG Stock)")
            st.dataframe(st.session_state.fg_inventory, use_container_width=True)
            
        with fg_tab2:
            st.subheader("รับสินค้าสำเร็จรูปเข้าคลัง FG (จาก WIP 8)")
            with st.form("fg_in_form"):
                fg_list = [f"{r['fg_code']} - {r['name']} ({r['customer']})" for _, r in st.session_state.fg_inventory.iterrows()]
                selected_fg = st.selectbox("เลือกรายการ FG:", fg_list)
                in_qty = st.number_input("จำนวนที่ผลิตเสร็จรับเข้าคลัง:", min_value=1, step=100)
                submit_fg_in = st.form_submit_button("📥 บันทึกรับเข้า FG")
                
                if submit_fg_in:
                    fg_code_target = selected_fg.split(" - ")[0]
                    idx = st.session_state.fg_inventory[st.session_state.fg_inventory['fg_code'] == fg_code_target].index[0]
                    st.session_state.fg_inventory.loc[idx, 'in_stock'] += in_qty
                    st.session_state.fg_inventory.loc[idx, 'last_update'] = datetime.now().strftime("%Y-%m-%d")
                    st.success(f"เพิ่มสต็อก FG `{fg_code_target}` จำนวน {in_qty:,} หน่วย เรียบร้อย!")
                    st.rerun()

        with fg_tab3:
            st.subheader("ตัดสต็อกขาย / ส่งมอบสินค้าให้ลูกค้า")
            with st.form("fg_out_form"):
                fg_list_out = [f"{r['fg_code']} - {r['name']} (คงเหลือ: {r['in_stock']:,} {r['unit']})" for _, r in st.session_state.fg_inventory.iterrows()]
                selected_fg_out = st.selectbox("เลือกสินค้าที่ส่งมอบ:", fg_list_out)
                do_num = st.text_input("เลขที่ใบส่งสินค้า / DO Number (เช่น DO-2026-0801)")
                out_qty = st.number_input("จำนวนที่ตัดส่งมอบ:", min_value=1, step=100)
                sale_date = st.date_input("วันที่ส่งมอบสินค้า:", datetime.now())
                submit_fg_out = st.form_submit_button("🚛 บันทึกการตัดส่งมอบ")
                
                if submit_fg_out:
                    fg_code_target = selected_fg_out.split(" - ")[0]
                    idx = st.session_state.fg_inventory[st.session_state.fg_inventory['fg_code'] == fg_code_target].index[0]
                    current_stock = st.session_state.fg_inventory.loc[idx, 'in_stock']
                    
                    if out_qty > current_stock:
                        st.error("จำนวนที่ต้องการตัดส่งมอบ เกินกว่าจำนวนสินค้าที่มีอยู่ในคลัง!")
                    else:
                        st.session_state.fg_inventory.loc[idx, 'in_stock'] -= out_qty
                        
                        log_entry = {
                            "date": sale_date.strftime("%Y-%m-%d"),
                            "fg_code": fg_code_target,
                            "name": st.session_state.fg_inventory.loc[idx, 'name'],
                            "customer": st.session_state.fg_inventory.loc[idx, 'customer'],
                            "sold_qty": out_qty,
                            "unit": st.session_state.fg_inventory.loc[idx, 'unit'],
                            "do_number": do_num,
                            "operator": user['name']
                        }
                        st.session_state.fg_sales_log = pd.concat([pd.DataFrame([log_entry]), st.session_state.fg_sales_log], ignore_index=True)
                        st.success(f"ตัดสต็อกส่งมอบ `{fg_code_target}` จำนวน {out_qty:,} หน่วย เรียบร้อยแล้ว!")
                        st.rerun()

            st.markdown("---")
            st.subheader("📜 ประวัติการขายและการจัดส่งสินค้า (Sales Log)")
            st.dataframe(st.session_state.fg_sales_log, use_container_width=True)

# =====================================================================
# 4. APP CONTROLLER
# =====================================================================
if not st.session_state.logged_in:
    login_screen()
else:
    main_app()
