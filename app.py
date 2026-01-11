import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Militia Locate", layout="wide")

# Professional, institutional styling. 
# "San Francisco" font stack for modern feel. No emojis.
st.markdown("""
    <style>
    .reportview-container { background: #ffffff; }
    .main-header {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 5px;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #666666;
        font-size: 1.05rem;
        margin-top: 0px;
        margin-bottom: 25px;
        border-bottom: 1px solid #eeeeee;
        padding-bottom: 15px;
    }
    .section-title {
        font-weight: 600;
        font-size: 1.2rem;
        margin-top: 25px;
        margin-bottom: 10px;
        color: #2c3e50;
        border-left: 3px solid #2c3e50;
        padding-left: 10px;
    }
    .legal-text {
        font-family: 'Segoe UI', sans-serif;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #333333;
        text-align: justify;
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 4px;
    }
    .status-pass {
        border-left: 4px solid #28a745;
        background-color: #f8fff9;
        padding: 20px;
        border-radius: 4px;
        border: 1px solid #e0e0e0;
    }
    .status-fail {
        border-left: 4px solid #dc3545;
        background-color: #fffcfc;
        padding: 20px;
        border-radius: 4px;
        border: 1px solid #e0e0e0;
    }
    .stButton>button {
        background-color: #000000;
        color: white;
        border-radius: 4px;
        border: none;
        padding: 10px 20px;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #333333;
        color: white;
    }
    a {
        color: #0066cc;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BACKEND LOGIC (THE "BRAIN")
# -----------------------------------------------------------------------------

class ComplianceEngine:
    def __init__(self):
        # 1. INVENTORY STATE
        if 'inventory' not in st.session_state:
            st.session_state.inventory = pd.DataFrame([
                {"Ticker": "XYZ", "Lender": "State Street", "Quantity": 100000, "TaxID": "99-123456", "Region": "US"},
                {"Ticker": "ABC", "Lender": "CalPERS", "Quantity": 50000, "TaxID": "88-654321", "Region": "US"},
                {"Ticker": "JP_CORP", "Lender": "Nomura", "Quantity": 20000, "TaxID": "77-111222", "Region": "JP"},
                {"Ticker": "VOLATILE", "Lender": "State Street", "Quantity": 10000, "TaxID": "99-123456", "Region": "US"},
            ])
        
        # 2. RESTRICTED LISTS (REG SHO)
        if 'restricted_list' not in st.session_state:
            st.session_state.restricted_list = ["VOLATILE", "FAIL_CORP"]

        # 3. AUDIT LEDGER
        if 'audit_ledger' not in st.session_state:
            st.session_state.audit_ledger = []

    def get_inventory(self):
        return st.session_state.inventory

    def get_restricted_list(self):
        return st.session_state.restricted_list

    def process_order(self, ticker, quantity, region, is_pre_borrow):
        # CHECK 1: REGULATORY BLOCKS (Rule 204)
        if ticker in st.session_state.restricted_list:
            if not is_pre_borrow:
                return {
                    "outcome": "REJECT",
                    "reason": f"REGULATORY BLOCK: {ticker} is on the Regulation SHO Threshold List (Rule 204).",
                    "code": "ERR-204-FAIL"
                }

        # CHECK 2: SETTLEMENT FRICTION
        if region == "JP" and not is_pre_borrow:
            return {
                "outcome": "REJECT",
                "reason": "SETTLEMENT RISK: Region JP requires confirmed Pre-Borrow agreement.",
                "code": "ERR-SETTLE-JP"
            }

        # CHECK 3: INVENTORY AVAILABILITY (Reasonable Grounds)
        available_rows = st.session_state.inventory[st.session_state.inventory['Ticker'] == ticker]
        total_available = available_rows['Quantity'].sum()
        
        if total_available < quantity:
            return {
                "outcome": "REJECT",
                "reason": f"INSUFFICIENT LIQUIDITY: Requested {quantity}, Found {total_available}.",
                "code": "ERR-LIQ-001"
            }

        # CHECK 4: ALLOCATION
        remaining_needed = quantity
        sources_used = []

        for index, row in available_rows.iterrows():
            if remaining_needed <= 0:
                break
            
            take = min(row['Quantity'], remaining_needed)
            
            # Update the database in real-time
            st.session_state.inventory.at[index, 'Quantity'] -= take
            remaining_needed -= take
            
            sources_used.append(f"{row['Lender']} (TaxID: {row['TaxID']})")

        # GENERATE COMPLIANCE ARTIFACT
        locate_id = str(uuid.uuid4()).upper()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        st.session_state.audit_ledger.append({
            "Time": timestamp,
            "Locate ID": locate_id,
            "Ticker": ticker,
            "Qty": quantity,
            "Lenders": ", ".join(sources_used)
        })

        return {
            "outcome": "PASS",
            "locate_id": locate_id,
            "source_data": sources_used
        }

# Initialize the System
system = ComplianceEngine()

# -----------------------------------------------------------------------------
# FRONT END (THE "DASHBOARD")
# -----------------------------------------------------------------------------

# Sidebar Navigation
st.sidebar.title("Militia Locate")
st.sidebar.markdown("COMPLIANCE GATEWAY")

# Reordered Workflow: Context -> Action -> Data -> Rules -> Proof
view = st.sidebar.radio(
    "Workflow:",
    ("About", "Trade Simulator", "Inventory Master", "Compliance Controls", "Audit Trail")
)

st.sidebar.markdown("---")
st.sidebar.caption("SYSTEM STATUS")
st.sidebar.code("FIX:  ONLINE\nREG:  UPDATED\nUSER: S. LEE")

# Top Header
st.markdown("<h1 class='main-header'>Militia Locate</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Regulation SHO Compliance & Inventory Management System</p>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# VIEW: ABOUT (LANDING PAGE)
# -----------------------------------------------------------------------------
if view == "About":
    st.markdown("### Executive Summary")
    
    st.markdown("""
    <div class='legal-text'>
    This platform serves as the central pre-trade compliance engine for Militia Capital, designed to satisfy the borrowing requirements of the Securities Exchange Act of 1934 before any short sale order is routed to the market.
    </div>
    """, unsafe_allow_html=True)

    # 1. Problem Statement
    st.markdown("<div class='section-title'>1. Problem Statement: The Locate Requirement</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='legal-text'>
    Pursuant to <strong>Regulation SHO Rule 203(b)(1)</strong> <a href='https://www.ecfr.gov/current/title-17/section-242.203' target='_blank'>[1]</a>, a broker-dealer may not accept a short sale order from a customer unless it has (i) borrowed the security, (ii) entered into a bona-fide arrangement to borrow the security, or (iii) has reasonable grounds to believe that the security can be borrowed so that it can be delivered on the date delivery is due.
    <br><br>
    <strong>Implications for Militia:</strong> Failure to secure a valid "locate" prior to execution results in "naked shorting." This violation triggers mandatory close-out requirements under <strong>Rule 204</strong> <a href='https://www.ecfr.gov/current/title-17/section-242.204' target='_blank'>[2]</a> and exposes the fund to inclusion on the <strong>Regulation SHO Threshold List</strong> <a href='https://www.nyse.com/regulation/nyse/public-info' target='_blank'>[3]</a>. Being placed in the "Penalty Box" would restrict Militia from executing short strategies without expensive, pre-confirmed borrowing arrangements.
    </div>
    """, unsafe_allow_html=True)

    # 2. The Solution
    st.markdown("<div class='section-title'>2. The Solution: Reasonable Grounds & Exceptions</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='legal-text'>
    While <strong>Rule 203(b)(2)</strong> provides limited exceptions for "bona-fide market making," Militia Capital's directional strategy does not qualify for this exemption. Therefore, the firm must rely on the "Reasonable Grounds" provision of Rule 203(b)(1)(ii).
    <br><br>
    The "Militia Locate" tool solves this by aggregating real-time inventory feeds from prime brokers (e.g., State Street, CalPERS). It establishes an <strong>affirmative determination</strong> of borrowability <em>before</em> the order is routed to the FIX gateway. 
    <br><br>
    <strong>Key Exception Logic:</strong>
    <ul>
        <li><strong>Restricted Securities:</strong> The tool automatically blocks orders on Threshold Securities unless a "Pre-Borrow" (Hard Borrow) is confirmed, ensuring Rule 204 compliance.</li>
        <li><strong>Long Sales:</strong> Orders marked "Long" are exempt from the locate requirement (Rule 200(g)), provided the seller is "deemed to own" the security.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    # 3. The Tool
    st.markdown("<div class='section-title'>3. The Tool: Functional Architecture</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='legal-text'>
    The system is divided into four critical workflows:
    <br><br>
    <strong>A. Trade Simulator (FIX Gateway)</strong><br>
    The primary interface for traders. It simulates the FIX Protocol (Tag 114) handshake. Inputting a ticker (e.g., <code>XYZ</code>) queries the consolidated inventory. If sufficient shares exist, the system locks the inventory and issues a unique <strong>Locate ID</strong>.
    <br><br>
    <strong>B. Inventory Master</strong><br>
    A real-time ledger of global liquidity provided by connected lenders. This fulfills the "Reasonable Grounds" standard by documenting that shares were available at the precise microsecond of the request.
    <br><br>
    <strong>C. Compliance Controls</strong><br>
    Monitors the Regulation SHO Threshold List. Any security appearing here is automatically blocked from "Easy-to-Borrow" locates, forcing the trader to utilize the "Hard Borrow" protocol.
    <br><br>
    <strong>D. Audit Trail</strong><br>
    An immutable, append-only log of all issued Locate IDs. This artifact is generated to satisfy SEC examination requests regarding Rule 204(a) record-keeping.
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# VIEW: TRADE SIMULATOR
# -----------------------------------------------------------------------------
elif view == "Trade Simulator":
    st.subheader("Direct Borrow Request")
    st.markdown("Simulate an incoming short sale order via FIX Protocol.")

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**Order Parameters**")
        input_ticker = st.text_input("Ticker Symbol", value="XYZ").upper()
        input_qty = st.number_input("Share Quantity", min_value=100, value=5000, step=100)
        input_region = st.selectbox("Settlement Region", ["US", "JP"])
        
        st.markdown("**Override Flags**")
        input_preborrow = st.checkbox("Hard Borrow / Pre-Borrow Confirmed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.button("VALIDATE & LOCATE")

    with col2:
        st.markdown("**System Response**")
        if submit:
            result = system.process_order(input_ticker, input_qty, input_region, input_preborrow)
            
            if result["outcome"] == "PASS":
                st.markdown(f"""
                <div class="status-pass">
                    <h3 style="margin:0; color:#155724">LOCATE CONFIRMED</h3>
                    <p style="margin-top:10px;"><strong>Locate ID:</strong> {result['locate_id']}</p>
                    <p><strong>Inventory Source:</strong> {result['source_data']}</p>
                    <small style="color:#666;">FIX Tag 114 satisfied. Order released to market.</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="status-fail">
                    <h3 style="margin:0; color:#721c24">REJECTED</h3>
                    <p style="margin-top:10px;"><strong>Error:</strong> {result['reason']}</p>
                    <p><strong>Code:</strong> {result['code']}</p>
                    <small style="color:#666;">Order blocked at gateway. Do not execute.</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Awaiting order input...")

# -----------------------------------------------------------------------------
# VIEW: INVENTORY MASTER
# -----------------------------------------------------------------------------
elif view == "Inventory Master":
    st.subheader("Global Inventory Position")
    st.markdown("Aggregated available-to-borrow securities from connected prime brokers.")
    
    st.dataframe(system.get_inventory(), use_container_width=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Refresh Feed (CalPERS)"):
            st.success("CalPERS feed updated.")
    with col_b:
        if st.button("Refresh Feed (State Street)"):
            st.success("State Street feed updated.")

# -----------------------------------------------------------------------------
# VIEW: COMPLIANCE CONTROLS
# -----------------------------------------------------------------------------
elif view == "Compliance Controls":
    st.subheader("Regulation SHO Threshold List")
    st.markdown("Securities restricted from 'Easy to Borrow' locates due to persistent delivery failures (Rule 203(c)(6)).")
    
    restricted_df = pd.DataFrame(system.get_restricted_list(), columns=["Restricted Ticker"])
    st.table(restricted_df)
    
    st.caption("Last updated: 04:00 AM EST via NYSE FTP.")

# -----------------------------------------------------------------------------
# VIEW: AUDIT TRAIL
# -----------------------------------------------------------------------------
elif view == "Audit Trail":
    st.subheader("Transaction Ledger")
    st.markdown("Immutable record of all issued Locate IDs for regulatory examination.")
    
    ledger = st.session_state.audit_ledger
    if len(ledger) > 0:
        st.dataframe(pd.DataFrame(ledger), use_container_width=True)
    else:
        st.text("No transactions recorded in this session.")
