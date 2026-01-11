import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(page_title="LocateLock | Militia Capital", layout="wide")

# Professional, minimal styling. Hides Streamlit branding for a "proprietary tool" feel.
st.markdown("""
    <style>
    .reportview-container { background: #ffffff; }
    .main-header {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0px;
    }
    .sub-header {
        color: #4a4a4a;
        font-size: 1.1rem;
        margin-top: -15px;
        margin-bottom: 20px;
    }
    .status-pass {
        border-left: 5px solid #28a745;
        background-color: #f6fff8;
        padding: 15px;
        border-radius: 2px;
    }
    .status-fail {
        border-left: 5px solid #dc3545;
        background-color: #fff8f8;
        padding: 15px;
        border-radius: 2px;
    }
    .stButton>button {
        background-color: #2c3e50;
        color: white;
        border-radius: 0px;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BACKEND LOGIC (THE "BRAIN")
# -----------------------------------------------------------------------------

class LocateLockEngine:
    def __init__(self):
        # 1. INVENTORY STATE
        # This acts as the central vault. It holds shares from all external lenders.
        if 'inventory' not in st.session_state:
            st.session_state.inventory = pd.DataFrame([
                {"Ticker": "XYZ", "Lender": "State Street", "Quantity": 100000, "TaxID": "99-123456", "Region": "US"},
                {"Ticker": "ABC", "Lender": "CalPERS", "Quantity": 50000, "TaxID": "88-654321", "Region": "US"},
                {"Ticker": "JP_CORP", "Lender": "Nomura", "Quantity": 20000, "TaxID": "77-111222", "Region": "JP"},
                {"Ticker": "VOLATILE", "Lender": "State Street", "Quantity": 10000, "TaxID": "99-123456", "Region": "US"},
            ])
        
        # 2. RESTRICTED LISTS (REG SHO)
        # This list prevents trading on stocks with excessive Fails to Deliver.
        if 'restricted_list' not in st.session_state:
            st.session_state.restricted_list = ["VOLATILE", "FAIL_CORP"]

        # 3. AUDIT LEDGER
        # This records every successful transaction for legal proof.
        if 'audit_ledger' not in st.session_state:
            st.session_state.audit_ledger = []

    def get_inventory(self):
        return st.session_state.inventory

    def get_restricted_list(self):
        return st.session_state.restricted_list

    def process_order(self, ticker, quantity, region, is_pre_borrow):
        """
        The Gatekeeper Logic.
        Input: Order details.
        Output: PASS (with Locate ID) or REJECT (with Reason).
        """
        
        # CHECK 1: COMPLIANCE BLOCKS (The "Penalty Box")
        if ticker in st.session_state.restricted_list:
            if not is_pre_borrow:
                return {
                    "outcome": "REJECT",
                    "reason": f"REGULATORY BLOCK: {ticker} is on the Threshold List (Rule 204).",
                    "code": "ERR-204-FAIL"
                }

        # CHECK 2: SETTLEMENT FRICTION (The "Japan Gap")
        if region == "JP" and not is_pre_borrow:
            return {
                "outcome": "REJECT",
                "reason": "SETTLEMENT RISK: Japanese T+2 requires confirmed Pre-Borrow.",
                "code": "ERR-SETTLE-JP"
            }

        # CHECK 3: INVENTORY AVAILABILITY (The "Vault")
        # Filter the master list for the specific ticker
        available_rows = st.session_state.inventory[st.session_state.inventory['Ticker'] == ticker]
        total_available = available_rows['Quantity'].sum()
        
        if total_available < quantity:
            return {
                "outcome": "REJECT",
                "reason": f"INSUFFICIENT LIQUIDITY: Requested {quantity}, Found {total_available}.",
                "code": "ERR-LIQ-001"
            }

        # CHECK 4: ALLOCATION (The "Decrementing Counter")
        # Logic: Lock the shares now so they cannot be used by another trader.
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
        
        # Save to Audit Trail
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
system = LocateLockEngine()

# -----------------------------------------------------------------------------
# FRONT END (THE "DASHBOARD")
# -----------------------------------------------------------------------------

# Top Header
st.markdown("<h1 class='main-header'>LocateLock</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Inventory Aggregation & Reg SHO Compliance Engine</p>", unsafe_allow_html=True)
st.markdown("---")

# Navigation Sidebar
st.sidebar.title("Command Center")
view = st.sidebar.radio(
    "Select Workflow:",
    ("Trade Simulator (FIX Gateway)", "Inventory Master", "Compliance Controls", "Audit Trail")
)

st.sidebar.markdown("---")
st.sidebar.text("CONNECTION STATUS:")
st.sidebar.code("FIX: CONNECTED\nDB:  ONLINE\nREG: UPDATED")

# -----------------------------------------------------------------------------
# VIEW: TRADE SIMULATOR
# -----------------------------------------------------------------------------
if view == "Trade Simulator (FIX Gateway)":
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
                    <h3 style="margin:0; color:#155724">✓ LOCATE CONFIRMED</h3>
                    <p><strong>Locate ID:</strong> {result['locate_id']}</p>
                    <p><strong>Inventory Source:</strong> {result['source_data']}</p>
                    <small>FIX Tag 114 satisfied. Order released to market.</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="status-fail">
                    <h3 style="margin:0; color:#721c24">✕ REJECTED</h3>
                    <p><strong>Error:</strong> {result['reason']}</p>
                    <p><strong>Code:</strong> {result['code']}</p>
                    <small>Order blocked at gateway. Do not execute.</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Waiting for order input...")

# -----------------------------------------------------------------------------
# VIEW: INVENTORY MASTER
# -----------------------------------------------------------------------------
elif view == "Inventory Master":
    st.subheader("Global Inventory Position")
    st.markdown("Aggregated available-to-borrow securities from all connected lenders.")
    
    # Display the live dataframe from the engine
    st.dataframe(system.get_inventory(), use_container_width=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Force Refresh (CalPERS)"):
            st.success("CalPERS feed updated.")
    with col_b:
        if st.button("Force Refresh (State Street)"):
            st.success("State Street feed updated.")

# -----------------------------------------------------------------------------
# VIEW: COMPLIANCE CONTROLS
# -----------------------------------------------------------------------------
elif view == "Compliance Controls":
    st.subheader("Regulation SHO Threshold List")
    st.markdown("Securities on this list are restricted from 'Easy to Borrow' locates due to persistent delivery failures.")
    
    restricted_df = pd.DataFrame(system.get_restricted_list(), columns=["Restricted Ticker"])
    st.table(restricted_df)
    
    st.caption("Last updated: Today at 04:00 AM EST via NYSE FTP.")

# -----------------------------------------------------------------------------
# VIEW: AUDIT TRAIL
# -----------------------------------------------------------------------------
elif view == "Audit Trail":
    st.subheader("Transaction Ledger")
    st.markdown("Immutable record of all issued Locate IDs.")
    
    ledger = st.session_state.audit_ledger
    if len(ledger) > 0:
        st.dataframe(pd.DataFrame(ledger), use_container_width=True)
    else:
        st.text("No transactions recorded in this session.")
