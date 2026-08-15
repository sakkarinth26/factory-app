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
    "sak191": {"password": "88888888", "name": "ผู้ดูแลระบบ", "role": "Admin"},
    "store": {"password": "store123", "name": "พนักงานคลังวัตถุดิบ", "role": "Store"},
    "planner": {"password": "plan123", "name": "ฝ่ายวางแผนการผลิต", "role": "Planner"},
    "prajak": {"password": "123456", "name": "mr.Prajak", "role": "Sales"}
}

# 1. สต็อกวัตถุดิบและอุปกรณ์ (RM & Tooling)
if "rm_inventory" not in st.session_state:
    st.session_state.rm_inventory = pd.DataFrame([
        {"code": "RM-FILM-001", "name": "ม้วนฟิล์ม PET 12 micron", "category": "ม้วนฟิล์ม", "qty": 2500.0, "unit": "Kg"},
        {"code": "RM-FILM-002", "name": "ม้วนฟิล์ม LLDPE 40 micron", "category": "ม้วนฟิล์ม", "qty": 3800.0, "unit": "Kg"},
        {"code": "RM-CHEM-001", "name": "กาวประกบ PU (Solventless)", "category": "กาว/เคมีภัณฑ์", "qty": 450.0, "unit": "Kg"},
        {"code": "RM-CYL-101", "name": "บล็อกแม่พิมพ์ - ซองกาแฟ 250g (ชุด 5 สี)", "category": "บล็อกแม่พิมพ์", "qty": 1.0, "unit": "ชุด"},
    ])

# 2. 8 WIP Production Steps
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
        },
        {
            "job_id": "JOB-2026-002",
            "product_name": "ซองฟอยล์ใส่อาหารเสริม",
            "customer": "เฮลท์ตี้ บิวตี้",
            "target_qty": 20000,
            "unit": "ซอง",
            "current_stage": "WIP 5: บ่มกาว (Curing / Aging Room)",
            "start_date": "2026-08-12",
            "remark": "บ่มกาว 48 ชั่วโมงก่อนส่ง Slitting"
        }
    ])

# 3. คลังสินค้าสำเร็จรูป (Finished Goods - FG)
if "fg_inventory" not in st.session_state:
    st.session_state.fg_inventory = pd.DataFrame([
        {"fg_code": "FG-POUCH-001", "name": "ถุงซิปล็อคใส 15x23 cm", "customer": "บจก. เอสเอ็มอี ไทย", "in_stock": 15000, "unit": "ซอง", "last_update": "2026-08-14"},
        {"fg_code": "FG-POUCH-002", "name": "ซองฟอยล์ทึบซีล 3 ด้าน", "customer": "หจก. อาหารไทยสด", "in_stock": 8500, "unit": "ซอง", "last_update": "2026-08-15"}
    ])

# 4. ประวัติการขาย/ตัดออก (FG Sales/Delivery Log)
if "fg_sales_log" not in st.session_state:
    st.session_state.fg_sales_log = pd.DataFrame(columns=["date", "fg_code", "name", "customer", "sold_qty", "unit", "do_number", "operator"])

# =====================================================================
# 2. LOGIN SCREEN
# =====================================================================
def login_screen():
    st.markdown("<h2 style='text-align: center;'>🏭 ระบบคลังและการผลิตบรรจุภัณฑ์ชนิดอ่อนตัว</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>Flexible Packaging Production & WIP Tracking System</h4>", unsafe_allow_html=True)
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
            "🏭 2. ติดตามไลน์ผลิต 8 ขั้นตอน (WIP Tracking)",
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
        
        tab1, tab2 = st.tabs(["📋 รายการสต็อกปัจจุบัน", "➕ รับเข้า / ตัดจ่ายวัตถุดิบ"])
        
        with tab1:
            st.subheader("รายการวัตถุดิบและแม่พิมพ์คงคลัง")
            st.dataframe(st.session_state.rm_inventory, use_container_width=True)
            
        with tab2:
            st.subheader("บันทึกปรับปรุงสต็อกวัตถุดิบ")
            with st.form("rm_update_form"):
                rm_codes = [f"{r['code']} - {r['name']}" for _, r in st.session_state.rm_inventory.iterrows()]
                selected_rm = st.selectbox("เลือกวัตถุดิบ/แม่พิมพ์:", rm_codes)
                action_type = st.radio("การดำเนินการ:", ["📥 รับเข้าคลัง (+)", "📤 เบิกไปไลน์ผลิต (-)"], horizontal=True)
                change_qty = st.number_input("จำนวน:", min_value=0.1, step=1.0)
                submit_rm = st.form_submit_button("💾 บันทึกรายการ")
                
                if submit_rm:
                    code_target = selected_rm.split(" - ")[0]
                    idx = st.session_state.rm_inventory[st.session_state.rm_inventory['code'] == code_target].index[0]
                    
                    if "รับเข้า" in action_type:
                        st.session_state.rm_inventory.loc[idx, 'qty'] += change_qty
                        st.success(f"รับเข้า {code_target} จำนวน {change_qty} เรียบร้อย!")
                    else:
                        if st.session_state.rm_inventory.loc[idx, 'qty'] >= change_qty:
                            st.session_state.rm_inventory.loc[idx, 'qty'] -= change_qty
                            st.success(f"เบิกจ่าย {code_target} ออกไปไลน์ผลิตเรียบร้อย!")
                        else:
                            st.error("จำนวนวัตถุดิบในสต็อกไม่เพียงพอสำหรับการเบิก!")

    # =================================================================
    # ส่วนที่ 2: ติดตามไลน์ผลิต 8 ขั้นตอน (WIP TRACKING)
    # =================================================================
    elif main_menu.startswith("🏭 2"):
        st.title("🏭 ติดตามไลน์การผลิต 8 ขั้นตอน (WIP Tracking)")
        st.caption("อัปเดตสถานะงานสั่งผลิต (Job Order) ตั้งแต่เตรียมแม่พิมพ์จนถึงตรวจ QC")
        
        tab_wip_1, tab_wip_2, tab_wip_3 = st.tabs(["📊 สถานะงานผลิตทั้งหมด (WIP Overview)", "🔄 อัปเดตสถานะ WIP", "➕ เปิด Job ผลิตใหม่"])
        
        with tab_wip_1:
            st.subheader("ภาพรวมสถานะ Job Production ล่าสุด")
            st.dataframe(st.session_state.wip_jobs, use_container_width=True)
            
            st.markdown("---")
            st.subheader("📌 สรุปจำนวน Job ในแต่ละ WIP")
            wip_counts = st.session_state.wip_jobs['current_stage'].value_counts()
            for stage in WIP_STAGES:
                count = wip_counts.get(stage, 0)
                st.write(f"• **{stage}**: `{count}` Job")

        with tab_wip_2:
            st.subheader("ย้ายสถานะขั้นตอนการผลิต (Move Stage)")
            with st.form("move_wip_form"):
                job_list = [f"{r['job_id']} | {r['product_name']} ({r['customer']})" for _, r in st.session_state.wip_jobs.iterrows()]
                selected_job = st.selectbox("เลือก Job Order:", job_list)
                new_stage = st.selectbox("ย้ายไปที่ขั้นตอน (New WIP Stage):", WIP_STAGES)
                submit_wip = st.form_submit_button("🔄 อัปเดตสถานะ WIP")
                
                if submit_wip:
                    job_id_target = selected_job.split(" | ")[0]
                    idx = st.session_state.wip_jobs[st.session_state.wip_jobs['job_id'] == job_id_target].index[0]
                    st.session_state.wip_jobs.loc[idx, 'current_stage'] = new_stage
                    st.success(f"อัปเดต Job `{job_id_target}` ไปยัง `{new_stage}` เรียบร้อยแล้ว!")
                    st.rerun()

        with tab_wip_3:
            st.subheader("สร้างใบสั่งผลิตใหม่ (New Production Job)")
            with st.form("new_job_form"):
                new_job_id = st.text_input("เลขที่ Job Order (เช่น JOB-2026-003)")
                p_name = st.text_input("ชื่อสินค้าบรรจุภัณฑ์")
                cust_name = st.text_input("ชื่อลูกค้า")
                t_qty = st.number_input("จำนวนที่ต้องผลิต:", min_value=100, step=1000)
                p_unit = st.selectbox("หน่วยนับ:", ["ซอง", "ม้วน", "ชิ้น"])
                remark_txt = st.text_area("หมายเหตุการผลิต (เช่น ชนิดฟิล์ม, สีพิมพ์)")
                submit_new_job = st.form_submit_button("🚀 เปิด Job ผลิต")
                
                if submit_new_job:
                    if new_job_id and p_name:
                        new_row = {
                            "job_id": new_job_id, "product_name": p_name, "customer": cust_name,
                            "target_qty": t_qty, "unit": p_unit,
                            "current_stage": WIP_STAGES[0],
                            "start_date": datetime.now().strftime("%Y-%m-%d"),
                            "remark": remark_txt
                        }
                        st.session_state.wip_jobs = pd.concat([st.session_state.wip_jobs, pd.DataFrame([new_row])], ignore_index=True)
                        st.success(f"เปิด Job ผลิต `{new_job_id}` เรียบร้อยแล้ว!")
                    else:
                        st.error("กรุณากรอกข้อมูล Job ID และชื่อสินค้าให้ครบถ้วน")

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
                        
                        # บันทึก Log การขาย
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
    login_screen()
else:
    main_app()
