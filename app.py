import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="ระบบควบคุมสินค้า & การผลิต (SQLite + Admin Delete)", layout="wide", initial_sidebar_state="collapsed")

# ซ่อนแถบ Sidebar ของ Streamlit
st.markdown("""
    <style>
        [data-testid="collapsedControl"] {display: none;}
        section[data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 1. DATABASE SETUP (SQLITE)
# =====================================================================
DB_FILE = "factory_data.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # ตาราง 1: คลังวัตถุดิบ (RM)
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory_rm (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            qty REAL NOT NULL,
            unit TEXT NOT NULL
        )
    ''')

    # ตาราง 2: Job Orders
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            target_qty REAL NOT NULL,
            unit TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    # ตาราง 3: สต็อก WIP รายแผนก
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory_wip (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            qty REAL NOT NULL,
            unit TEXT NOT NULL,
            UNIQUE(job_id, stage)
        )
    ''')

    # ตาราง 4: คลังสินค้าสำเร็จรูป (FG)
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory_fg (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            qty REAL NOT NULL,
            unit TEXT NOT NULL,
            in_date TEXT NOT NULL
        )
    ''')

    # ตาราง 5: ประวัติการเบิกจ่าย / ย้าย WIP
    c.execute('''
        CREATE TABLE IF NOT EXISTS history_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            target_wip TEXT NOT NULL,
            mat_type TEXT NOT NULL,
            code_name TEXT NOT NULL,
            qty REAL NOT NULL,
            unit TEXT NOT NULL,
            issue_date TEXT NOT NULL
        )
    ''')

    # สุ่มเพิ่มข้อมูลเริ่มต้นหากฐานข้อมูลยังว่างเปล่า
    c.execute("SELECT COUNT(*) FROM inventory_rm")
    if c.fetchone()[0] == 0:
        default_rm = [
            ("RM-001", "ม้วนฟิล์ม PET 12u", 5000.0, "Kg"),
            ("RM-002", "ม้วนฟิล์ม LLDPE 40u", 4000.0, "Kg"),
            ("RM-003", "หมึกพิมพ์ Solvent Base", 300.0, "Kg"),
            ("RM-004", "กาว PU Dry Lamination", 500.0, "Kg"),
            ("RM-005", "จุกฝาเกลียว (Spout 10mm)", 50000.0, "ชิ้น")
        ]
        c.executemany("INSERT INTO inventory_rm VALUES (?, ?, ?, ?)", default_rm)
        
    conn.commit()
    conn.close()

# เรียกใช้งานครั้งแรกเพื่อสร้าง DB
init_db()

# =====================================================================
# 2. USER DATABASE & CONSTANTS
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

# =====================================================================
# 3. HELPER FUNCTIONS FOR DB READ/WRITE
# =====================================================================
def load_data(query):
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def update_wip_qty(job_id, stage, qty, unit):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT qty FROM inventory_wip WHERE job_id = ? AND stage = ?", (job_id, stage))
    row = c.fetchone()
    if row:
        new_qty = row[0] + qty
        c.execute("UPDATE inventory_wip SET qty = ? WHERE job_id = ? AND stage = ?", (new_qty, job_id, stage))
    else:
        c.execute("INSERT INTO inventory_wip (job_id, stage, qty, unit) VALUES (?, ?, ?, ?)", (job_id, stage, qty, unit))
    conn.commit()
    conn.close()

def deduce_wip_qty(job_id, stage, qty):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT qty FROM inventory_wip WHERE job_id = ? AND stage = ?", (job_id, stage))
    row = c.fetchone()
    if row:
        new_qty = max(0.0, row[0] - qty)
        c.execute("UPDATE inventory_wip SET qty = ? WHERE job_id = ? AND stage = ?", (new_qty, job_id, stage))
    conn.commit()
    conn.close()

def delete_record(table_name, condition_column, condition_value):
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"DELETE FROM {table_name} WHERE {condition_column} = ?", (condition_value,))
    conn.commit()
    conn.close()

# =====================================================================
# 4. LOGIN SCREEN
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
# 5. MAIN APPLICATION
# =====================================================================
def main_app():
    user = st.session_state.user_info
    role = user["role"]

    # Header
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.title("🏭 ระบบคลังสินค้า & ควบคุมกระบวนการผลิต (SQLite DB)")
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

        # เพิ่มปุ่มเมนูจัดการลบข้อมูลเฉพาะ Admin
        if role == "Admin":
            st.markdown("---")
            st.markdown("### ⚙️ ผู้ดูแลระบบ (Admin Only)")
            if st.button("🗑️ 7. จัดการ & ลบข้อมูลที่บันทึกผิดพลาด", use_container_width=True):
                st.session_state.current_page = "delete_manager"
                st.rerun()

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
                unit = c4.selectbox("หน่วยนับ", ["Kg", "ม้วน", "เมตร", "กล่อง"])
                if st.form_submit_button("💾 บันทึกรับเข้า"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("SELECT qty FROM inventory_rm WHERE code = ?", (code,))
                    row = c.fetchone()
                    if row:
                        c.execute("UPDATE inventory_rm SET qty = ? WHERE code = ?", (row[0] + qty, code))
                    else:
                        c.execute("INSERT INTO inventory_rm VALUES (?, ?, ?, ?)", (code, name, qty, unit))
                    conn.commit()
                    conn.close()
                    st.success("บันทึกรับเข้าเรียบร้อย")
                    st.rerun()
                    
        df_rm = load_data("SELECT * FROM inventory_rm")
        st.dataframe(df_rm, use_container_width=True)

    # -------------------------------------------------------------
    # หน้า 2: เปิด Job Order ใหม่
    # -------------------------------------------------------------
    elif st.session_state.current_page == "open_job":
        st.subheader("🏗️ เปิด Job Order ใหม่")
        with st.form("create_job"):
            j_id = st.text_input("เลขที่ Job Order (เช่น JOB-2026-002)")
            p_name = st.text_input("ชื่อสินค้า/ซองบรรจุภัณฑ์")
            t_qty = st.number_input("จำนวนที่ต้องการผลิตรวม", min_value=1, value=10000)
            u_name = st.selectbox("หน่วยผลิตหลัก", ["ซอง", "ม้วน",  "Kg"])
            
            if st.form_submit_button("💾 บันทึกเปิด Job"):
                conn = get_connection()
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO jobs VALUES (?, ?, ?, ?, ?)", 
                              (j_id, p_name, t_qty, u_name, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    st.success(f"เปิด Job {j_id} เรียบร้อยแล้ว")
                except sqlite3.IntegrityError:
                    st.error("เลขที่ Job นี้มีอยู่ในระบบแล้ว!")
                finally:
                    conn.close()
                st.rerun()
        
        st.markdown("### รายการ Job ทั้งหมด")
        df_jobs = load_data("SELECT * FROM jobs ORDER BY created_at DESC")
        st.dataframe(df_jobs, use_container_width=True)

    # -------------------------------------------------------------
    # หน้า 3: บันทึกการผลิต & ดึง WIP/RM มาทำต่อ
    # -------------------------------------------------------------
    elif st.session_state.current_page == "process_wip":
        st.subheader("🔄 บันทึกการผลิตประจำแผนก (ดึง RM / WIP ก่อนหน้า มาผลิตต่อ)")
        
        df_jobs = load_data("SELECT job_id FROM jobs")
        if df_jobs.empty:
            st.warning("ยังไม่มี Job Order ในระบบ กรุณาเปิด Job ก่อน")
        else:
            job_list = df_jobs['job_id'].tolist()
            sel_job = st.selectbox("1️⃣ เลือก Job Order ที่ต้องการทำงาน:", job_list)
            
            # โหลด RM และ WIP
            df_rm = load_data("SELECT * FROM inventory_rm WHERE qty > 0")
            df_wip = load_data(f"SELECT * FROM inventory_wip WHERE job_id = '{sel_job}' AND qty > 0")
            
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
                    if df_rm.empty:
                        st.info("⚠️ วัตถุดิบในคลังหลักหมด")
                    else:
                        rm_opts = [f"{r['code']} - {r['name']} (เหลือ {r['qty']} {r['unit']})" for _, r in df_rm.iterrows()]
                        sel_rm_str = st.selectbox("เลือกวัตถุดิบ RM:", rm_opts)
                        used_rm_code = sel_rm_str.split(" - ")[0]
                        rm_data = df_rm[df_rm['code'] == used_rm_code].iloc[0]
                        available_max = float(rm_data['qty'])
                        unit_label = rm_data['unit']
                else:
                    if df_wip.empty:
                        st.info("⚠️ ยังไม่มี WIP ของแผนกก่อนหน้าสำหรับ Job นี้")
                    else:
                        wip_opts = [f"{w['stage']} (คงเหลือ {w['qty']} {w['unit']})" for _, w in df_wip.iterrows()]
                        sel_wip_str = st.selectbox("เลือก WIP จากแผนกก่อนหน้า:", wip_opts)
                        used_wip_stage = sel_wip_str.split(" (")[0]
                        wip_data = df_wip[df_wip['stage'] == used_wip_stage].iloc[0]
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
                    conn = get_connection()
                    c = conn.cursor()
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

                    # 1. ตัดสต็อกขาเข้า
                    if input_type == "เบิก RM จากคลังหลัก" and used_rm_code:
                        c.execute("UPDATE inventory_rm SET qty = qty - ? WHERE code = ?", (input_qty, used_rm_code))
                        c.execute("SELECT name FROM inventory_rm WHERE code = ?", (used_rm_code,))
                        mat_name = c.fetchone()[0]
                        c.execute("INSERT INTO history_logs (job_id, target_wip, mat_type, code_name, qty, unit, issue_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (sel_job, target_stage, "RM", f"{used_rm_code} ({mat_name})", input_qty, unit_label, now_str))

                    elif input_type == "ดึง WIP จากแผนกก่อนหน้า" and used_wip_stage:
                        deduce_wip_qty(sel_job, used_wip_stage, input_qty)
                        c.execute("INSERT INTO history_logs (job_id, target_wip, mat_type, code_name, qty, unit, issue_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (sel_job, target_stage, "WIP", used_wip_stage, input_qty, unit_label, now_str))

                    conn.commit()
                    conn.close()

                    # 2. เพิ่มสต็อกขาออก
                    if target_stage.startswith("FG:"):
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("SELECT product_name FROM jobs WHERE job_id = ?", (sel_job,))
                        p_name = c.fetchone()[0]
                        c.execute("INSERT INTO inventory_fg (job_id, product_name, qty, unit, in_date) VALUES (?, ?, ?, ?, ?)",
                                  (sel_job, p_name, output_qty, output_unit, now_str))
                        conn.commit()
                        conn.close()
                        st.success("บันทึกการผลิตสำเร็จ! โอนเข้าคลัง FG เรียบร้อยแล้ว")
                    else:
                        update_wip_qty(sel_job, target_stage, output_qty, output_unit)
                        st.success(f"บันทึกการผลิตสำเร็จ! ผลลัพธ์ส่งเข้า **{target_stage}** เรียบร้อยแล้ว")

                    st.rerun()

    # -------------------------------------------------------------
    # หน้า 4: คลังสินค้าสำเร็จรูป (FG Stock)
    # -------------------------------------------------------------
    elif st.session_state.current_page == "fg_stock":
        st.subheader("🏆 รายการสินค้าสำเร็จรูปในคลัง (FG Stock)")
        df_fg = load_data("SELECT * FROM inventory_fg")
        st.dataframe(df_fg, use_container_width=True)

    # -------------------------------------------------------------
    # หน้า 5: ประวัติการทำรายการ
    # -------------------------------------------------------------
    elif st.session_state.current_page == "history":
        st.subheader("📜 ประวัติการเบิก RM และการดึง WIP ไปใช้งาน")
        df_hist = load_data("SELECT * FROM history_logs ORDER BY id DESC")
        st.dataframe(df_hist, use_container_width=True)

    # -------------------------------------------------------------
    # หน้า 6: สต็อก WIP รายแผนก
    # -------------------------------------------------------------
    elif st.session_state.current_page == "wip_stock":
        st.subheader("📊 สต็อก WIP คงเหลือในแต่ละแผนก (รอแผนกถัดไปมาดึง)")
        df_wip_all = load_data("SELECT * FROM inventory_wip WHERE qty > 0")
        st.dataframe(df_wip_all, use_container_width=True)

    # -------------------------------------------------------------
    # หน้า 7: ลบข้อมูล (เฉพาะ Admin เท่านั้น)
    # -------------------------------------------------------------
    elif st.session_state.current_page == "delete_manager":
        if role != "Admin":
            st.error("🔒 เฉพาะผู้ดูแลระบบ (Admin) เท่านั้นที่สามารถใช้หน้านี้ได้")
        else:
            st.subheader("🗑️ ระบบจัดการ & ลบข้อมูลที่คีย์ผิดพลาด")
            st.warning("⚠️ การลบข้อมูลจะลบออกจากฐานข้อมูล SQLite ถาวร กรุณาตรวจสอบให้แน่ใจก่อนกดลบ")
            
            tab_rm, tab_job, tab_wip, tab_fg, tab_log = st.tabs([
                "📦 ลบวัตถุดิบ (RM)", 
                "🏗️ ลบ Job Order", 
                "📊 ลบสต็อก WIP", 
                "🏆 ลบสินค้า FG", 
                "📜 ลบประวัติเบิกจ่าย"
            ])
            
            # Tab 1: ลบ RM
            with tab_rm:
                df = load_data("SELECT * FROM inventory_rm")
                st.dataframe(df, use_container_width=True)
                if not df.empty:
                    del_code = st.selectbox("เลือกรหัส RM ที่ต้องการลบ:", df['code'].tolist(), key="del_rm_key")
                    if st.button("🗑️ ยืนยันลบวัตถุดิบนี้", key="btn_del_rm"):
                        delete_record("inventory_rm", "code", del_code)
                        st.success(f"ลบรหัส {del_code} เรียบร้อยแล้ว")
                        st.rerun()

            # Tab 2: ลบ Job
            with tab_job:
                df = load_data("SELECT * FROM jobs")
                st.dataframe(df, use_container_width=True)
                if not df.empty:
                    del_job = st.selectbox("เลือก Job Order ที่ต้องการลบ:", df['job_id'].tolist(), key="del_job_key")
                    if st.button("🗑️ ยืนยันลบ Job นี้", key="btn_del_job"):
                        delete_record("jobs", "job_id", del_job)
                        st.success(f"ลบ {del_job} เรียบร้อยแล้ว")
                        st.rerun()

            # Tab 3: ลบ WIP
            with tab_wip:
                df = load_data("SELECT * FROM inventory_wip")
                st.dataframe(df, use_container_width=True)
                if not df.empty:
                    wip_opts = [f"{r['id']} - {r['job_id']} [{r['stage']}] ({r['qty']} {r['unit']})" for _, r in df.iterrows()]
                    del_wip_str = st.selectbox("เลือกรายการ WIP ที่ต้องการลบ:", wip_opts, key="del_wip_key")
                    del_wip_id = int(del_wip_str.split(" - ")[0])
                    if st.button("🗑️ ยืนยันลบ WIP นี้", key="btn_del_wip"):
                        delete_record("inventory_wip", "id", del_wip_id)
                        st.success("ลบรายการ WIP เรียบร้อยแล้ว")
                        st.rerun()

            # Tab 4: ลบ FG
            with tab_fg:
                df = load_data("SELECT * FROM inventory_fg")
                st.dataframe(df, use_container_width=True)
                if not df.empty:
                    fg_opts = [f"{r['id']} - {r['job_id']} : {r['product_name']} ({r['qty']} {r['unit']})" for _, r in df.iterrows()]
                    del_fg_str = st.selectbox("เลือกรายการ FG ที่ต้องการลบ:", fg_opts, key="del_fg_key")
                    del_fg_id = int(del_fg_str.split(" - ")[0])
                    if st.button("🗑️ ยืนยันลบ FG นี้", key="btn_del_fg"):
                        delete_record("inventory_fg", "id", del_fg_id)
                        st.success("ลบรายการ FG เรียบร้อยแล้ว")
                        st.rerun()

            # Tab 5: ลบ History Log
            with tab_log:
                df = load_data("SELECT * FROM history_logs ORDER BY id DESC")
                st.dataframe(df, use_container_width=True)
                if not df.empty:
                    log_opts = [f"{r['id']} - [{r['issue_date']}] Job: {r['job_id']} -> {r['target_wip']}" for _, r in df.iterrows()]
                    del_log_str = st.selectbox("เลือกประวัติที่ต้องการลบ:", log_opts, key="del_log_key")
                    del_log_id = int(del_log_str.split(" - ")[0])
                    if st.button("🗑️ ยืนยันลบประวัตินี้", key="btn_del_log"):
                        delete_record("history_logs", "id", del_log_id)
                        st.success("ลบประวัติรายการเรียบร้อยแล้ว")
                        st.rerun()

# =====================================================================
# 6. ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_screen()
    else:
        main_app()
