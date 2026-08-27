import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ระบบบริหารคลังและไลน์ผลิต Flexible Packaging", layout="wide")

# =====================================================================
# 1. CONSTANTS & INITIAL SESSION STATE
# =====================================================================
USER_DATABASE = {
    "admin": {"password": "88888888", "name": "ผู้ดูแลระบบ", "role": "Admin"},
    "prajak": {"password": "123456", "name": "Mr.Prajak", "role": "Manager"},
    "operator": {"password": "1234", "name": "พนักงานคลัง/ไลน์ผลิต", "role": "User"}
}

PROCESS_STAGES = [
    "WIP 1: Print (พิมพ์ลาย)",
    "WIP 2: Dry 1 (ประกบชั้นที่ 1)",
    "WIP 3: Dry 2 (ประกบชั้นที่ 2)",
    "WIP 4: Slit (ตัดแบ่งม้วน)",
    "WIP 5: Bag Making (ขึ้นรูปถุง/ซอง)",
    "WIP 6: Spout (ติดจุก)",
    "WIP 7: Packing (แพ็กเกจจิ้ง)",
    "FG: สินค้าสำเร็จรูป"
]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# คลังวัตถุดิบ (RM)
if "inventory_rm" not in st.session_state:
    st.session_state.inventory_rm = pd.DataFrame([
        {"code": "RM-001", "name": "ม้วนฟิล์ม PET 12u", "qty": 5000.0, "unit": "Kg"},
        {"code": "RM-002", "name": "ม้วนฟิล์ม LLDPE 40u", "qty": 4000.0, "unit": "Kg"},
        {"code": "RM-003", "name": "หมึกพิมพ์ Solvent Base", "qty": 300.0, "unit": "Kg"},
        {"code": "RM-004", "name": "กาว PU Dry Lamination", "qty": 500.0, "unit": "Kg"},
        {"code": "RM-005", "name": "จุกฝาเกลียว (Spout 10mm)", "qty": 50000.0, "unit": "ชิ้น"}
    ])

# คลังสินค้าสำเร็จรูป (FG)
if "inventory_fg" not in st.session_state:
    st.session_state.inventory_fg = pd.DataFrame(columns=["job_id", "product_name", "qty", "unit", "in_date"])

# Job การผลิต & WIP Tracking
if "jobs" not in st.session_state:
    st.session_state.jobs = pd.DataFrame([
        {
            "job_id": "JOB-2026-001",
            "product_name": "ซองติดจุก 250ml",
            "job_type": "ซองติดจุก (Spout)",
            "current_stage": "WIP 1: Print (พิมพ์ลาย)",
            "target_qty": 20000,
            "unit": "ซอง",
            "start_date": "2026-08-27"
        }
    ])

# บันทึกการจ่าย RM เข้า WIP
if "issued_materials" not in st.session_state:
    st.session_state.issued_materials = pd.DataFrame(columns=["job_id", "target_wip", "rm_code", "rm_name", "qty", "unit", "issue_date"])

# ประวัติ Transaction
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["timestamp", "type", "job_id", "detail", "operator"])

# =====================================================================
# 2. LOGIN SCREEN
# =====================================================================
def login_screen():
    st.markdown("<h2 style='text-align: center;'>🔐 เข้าสู่ระบบบริหารคลังสินค้า & ติดตามงานผลิต</h2>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("เข้าสู่ระบบ")
            if submit:
                if username in USER_DATABASE and USER_DATABASE[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_info = USER_DATABASE[username]
                    st.rerun()
                else:
                    st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

# =====================================================================
# 3. MAIN APPLICATION
# =====================================================================
def main_app():
    user = st.session_state.user_info
    st.sidebar.title(f"👤 {user['name']}")
    st.sidebar.caption(f"สิทธิ์การใช้งาน: {user['role']}")
    
    menu = st.sidebar.radio(
        "เลือกเมนูการทำงาน:",
        [
            "📦 1. คลังวัตถุดิบ (RM Stock)",
            "🏗️ 2. เปิด Job & จ่าย RM เข้า WIP (Print/Dry1/Dry2)",
            "🔄 3. ติดตาม & เคลื่อนย้าย WIP (ตาม Process Flow)",
            "🏆 4. คลังสินค้าสำเร็จรูป (FG Stock)",
            "📜 5. ประวัติการทำรายการ"
        ]
    )
    
    if st.sidebar.button("🚪 ออกจากระบบ", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    st.title("🏭 ระบบคลังสินค้า & ควบคุมกระบวนการผลิต (Flexible Packaging)")
    st.markdown("---")

    # -------------------------------------------------------------
    # เมนู 1: คลังวัตถุดิบ (RM Stock)
    # -------------------------------------------------------------
    if menu.startswith("📦 1"):
        st.subheader("📦 สต็อกวัตถุดิบในคลัง (RM)")
        
        with st.expander("📥 บันทึกรับเข้าวัตถุดิบใหม่"):
            with st.form("rec_rm"):
                c1, c2, c3, c4 = st.columns(4)
                code = c1.text_input("รหัส RM")
                name = c2.text_input("ชื่อวัตถุดิบ")
                qty = c3.number_input("จำนวนรับเข้า", min_value=0.1)
                unit = c4.selectbox("หน่วยนับ", ["Kg", "ม้วน", "ชิ้น", "ชุด"])
                if st.form_submit_button("💾 รับเข้าคลัง"):
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
    # เมนู 2: เปิด Job & จ่าย RM เข้า WIP
    # -------------------------------------------------------------
    elif menu.startswith("🏗️ 2"):
        st.subheader("🏗️ เปิด Job Order ใหม่ & จ่าย RM ตรงเข้า WIP (Print / Dry1 / Dry2)")
        
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
                        "current_stage": "WIP 1: Print (พิมพ์ลาย)", "target_qty": t_qty,
                        "unit": u_name, "start_date": datetime.now().strftime("%Y-%m-%d")
                    }
                    st.session_state.jobs = pd.concat([st.session_state.jobs, pd.DataFrame([job_data])], ignore_index=True)
                    st.success(f"เปิด Job {j_id} เรียบร้อยแล้ว")
                    st.rerun()

        with tab_issue:
            st.markdown("##### 🎯 เลือกตัดจ่าย RM ไปยังจุดใช้งาน (ตาม Diagram: Print / Dry 1 / Dry 2)")
            with st.form("issue_rm"):
                job_list = st.session_state.jobs['job_id'].tolist()
                sel_job = st.selectbox("เลือก Job Order:", job_list if job_list else ["ไม่มี Job"])
                target_wip = st.selectbox("จ่ายตรงไปยัง WIP ขั้นตอน:", [
                    "WIP 1: Print (จ่าย ฟิล์ม/หมึก)",
                    "WIP 2: Dry 1 (จ่าย ฟิล์ม/กาว)",
                    "WIP 3: Dry 2 (จ่าย ฟิล์ม/กาว)",
                    "WIP 6: Spout (จ่าย จุก/ฝา)"
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
                        st.success(f"จ่าย {st.session_state.inventory_rm.loc[idx, 'name']} เข้า {target_wip} เรียบร้อย!")
                        st.rerun()

    # -------------------------------------------------------------
    # เมนู 3: ติดตาม & เคลื่อนย้าย WIP (ตาม Process Flow)
    # -------------------------------------------------------------
    elif menu.startswith("🔄 3"):
        st.subheader("🔄 ระบบติดตาม WIP & การไหลของงาน (ตาม Flow Chart)")
        
        # แสดงสถานะ Job ในปัจจุบัน
        st.dataframe(st.session_state.jobs, use_container_width=True)
        st.markdown("---")
        
        st.markdown("#### ⚡ บันทึกส่งมอบงานข้ามขั้นตอน WIP")
        if not st.session_state.jobs.empty:
            with st.form("move_wip"):
                sel_job_id = st.selectbox("เลือก Job ที่ต้องการย้ายขั้นตอน:", st.session_state.jobs['job_id'].tolist())
                job_curr_info = st.session_state.jobs[st.session_state.jobs['job_id'] == sel_job_id].iloc[0]
                
                st.info(f"📍 ขั้นตอนปัจจุบัน: **{job_curr_info['current_stage']}** | ประเภทงาน: **{job_curr_info['job_type']}**")
                
                # Dynamic Routing based on diagram
                next_stage_options = []
                curr = job_curr_info['current_stage']
                
                if "WIP 1: Print" in curr:
                    next_stage_options = ["WIP 2: Dry 1 (ประกบชั้นที่ 1) [ฟิล์มพิมพ์แล้ว]"]
                elif "WIP 2: Dry 1" in curr:
                    next_stage_options = ["WIP 3: Dry 2 (ประกบชั้นที่ 2) [ฟิล์มพิมพ์ประกบ 2 ชั้น]"]
                elif "WIP 3: Dry 2" in curr:
                    next_stage_options = [
                        "WIP 4: Slit (ตัดแบ่งม้วน) [แบ่งม้วน/ม้วนส่งถุง]",
                        "WIP 5: Bag Making (ขึ้นรูปถุง/ซอง) [ไปแบบไม่ผ่านตัดม้วน]"
                    ]
                elif "WIP 4: Slit" in curr:
                    next_stage_options = [
                        "WIP 7: Packing (งานม้วนจบที่แพ็กเกจจิ้ง)",
                        "WIP 5: Bag Making (ส่งต่อขึ้นรูปซอง)"
                    ]
                elif "WIP 5: Bag Making" in curr:
                    next_stage_options = [
                        "WIP 6: Spout (ไปขั้นตอนติดจุก)",
                        "WIP 7: Packing (ซองไม่ติดจุก เข้าแพ็กเกจจิ้ง)"
                    ]
                elif "WIP 6: Spout" in curr:
                    next_stage_options = ["WIP 7: Packing (ซองติดจุก เข้าแพ็กเกจจิ้ง)"]
                elif "WIP 7: Packing" in curr:
                    next_stage_options = ["FG: สินค้าสำเร็จรูป (โอนเข้าคลัง FG)"]

                selected_next = st.selectbox("เลือกขั้นตอนถัดไป (ตาม Flow):", next_stage_options)
                completed_qty = st.number_input("จำนวนที่ผลิตได้ในขั้นตอนนี้", min_value=1, value=int(job_curr_info['target_qty']))
                
                if st.form_submit_button("🚀 บันทึกย้ายไปขั้นตอนถัดไป"):
                    j_idx = st.session_state.jobs[st.session_state.jobs['job_id'] == sel_job_id].index[0]
                    
                    # ถ้าเป็นการย้ายเข้า FG
                    if "FG: สินค้าสำเร็จรูป" in selected_next:
                        fg_item = {
                            "job_id": sel_job_id,
                            "product_name": job_curr_info['product_name'],
                            "qty": completed_qty,
                            "unit": job_curr_info['unit'],
                            "in_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        st.session_state.inventory_fg = pd.concat([st.session_state.inventory_fg, pd.DataFrame([fg_item])], ignore_index=True)
                        st.session_state.jobs.loc[j_idx, 'current_stage'] = "FG: สำเร็จรูป (เสร็จสิ้น)"
                        st.success(f"🎉 งาน Job {sel_job_id} ผลิตเสร็จสิ้น และโอนเข้าคลัง FG เรียบร้อยแล้ว!")
                    else:
                        clean_stage_name = selected_next.split(" [")[0]
                        st.session_state.jobs.loc[j_idx, 'current_stage'] = clean_stage_name
                        st.success(f"ย้าย Job {sel_job_id} ไปยัง {clean_stage_name} เรียบร้อย!")
                    st.rerun()

    # -------------------------------------------------------------
    # เมนู 4: คลังสินค้าสำเร็จรูป (FG Stock)
    # -------------------------------------------------------------
    elif menu.startswith("🏆 4"):
        st.subheader("🏆 รายการสินค้าสำเร็จรูปในคลัง (FG)")
        st.dataframe(st.session_state.inventory_fg, use_container_width=True)

    # -------------------------------------------------------------
    # เมนู 5: ประวัติการทำรายการ
    # -------------------------------------------------------------
    elif menu.startswith("📜 5"):
        st.subheader("📜 รายการเบิกจ่ายวัตถุดิบเข้า WIP")
        st.dataframe(st.session_state.issued_materials, use_container_width=True)

if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_screen()
    else:
        main_app()
