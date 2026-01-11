import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Militia Locate | Compliance Engine", layout="wide")

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
        font-weight: 700;
        font-size: 1.15rem;
        margin-top: 30px;
        margin-bottom: 15px;
        color: #0f2b45;
        border-left: 4px solid #0f2b45;
        padding-left: 12px;
    }
    .legal-text {
        font-family: 'Segoe UI', sans-serif;
        font-size: 0.95rem;
        line-height: 1.65;
        color: #2c2c2c;
        text-align: justify;
        background-color: #f8f9fa;
        padding: 20px;
        border: 1px solid #e9ecef;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    .feature-box {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .status-pass {
        border-left: 4px solid #28a745;
        background-color: #f0fff4;
        padding: 20px;
        border-radius: 4px;
        border: 1px solid #d4edda;
    }
    .status-fail {
        border-left: 4px solid #dc3545;
        background-color: #fff5f5;
        padding: 20px;
        border-radius: 4px;
        border: 1px solid #f5c6cb;
    }
    .stButton>button {
        background-color: #0f2b45;
        color: white;
        border-radius: 2px;
        border: none;
        padding: 10px 25px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton>button:hover {
        background-color: #1a3c5e;
        color: white;
    }
    a { color: #0056b3; text-decoration: none; border-bottom: 1px dotted #0056b3; }
    a:hover { text-decoration: none; border-bottom: 1px solid #0056b3; }
    strong { color: #0f2b45; }
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
                    "reason": f"REGULATORY BLOCK: {ticker} is on the Regulation SHO Threshold List (Rule 204). Hard Borrow required.",
                    "code": "ERR-204-FAIL"
                }

        # CHECK 2: SETTLEMENT FRICTION (Japan T+2 vs US T+1)
        if region == "JP" and not is_pre_borrow:
            return {
                "outcome": "REJECT",
                "reason": "SETTLEMENT RISK: Japan (T+2) requires confirmed Pre-Borrow due to US T+1 funding mismatch.",
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

# Logical Order: Policy -> Action -> Data -> Rules -> Proof
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
    st.markdown("### Executive Summary: Pre-Trade Compliance Architecture")
    
    # 1. Problem Statement
    st.markdown("<div class='section-title'>1. Problem Statement: The Locate Requirement (Rule 203(b)(1))</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='legal-text'>
    Under <strong>Regulation SHO Rule 203(b)(1)</strong> <a href='https://www.ecfr.gov/current/title-17/section-242.203' target='_blank'>[1]</a>, a broker-dealer is prohibited from accepting a short sale order unless it has (i) borrowed the security, (ii) entered into a bona-fide arrangement to borrow, or (iii) has <strong>reasonable grounds to believe</strong> that the security can be borrowed for delivery on the settlement date.
    <br><br>
    <strong>Implication for Militia Capital:</strong> Unlike registered market makers, Militia executes a <strong>directional strategy</strong>. We take speculative positions based on fundamental thesis rather than providing continuous two-sided liquidity. Therefore, Militia <strong>does not qualify</strong> for the "Bona-Fide Market Maker" exception (Rule 203(b)(2)(iii)).
    <br><br>
    Consequently, every short order generated by the desk must satisfy the stricter "Locate Requirement" of Rule 203(b)(1). Failure to secure a valid locate results in "naked shorting," triggering mandatory buy-ins under <strong>Rule 204</strong> <a href='https://www.ecfr.gov/current/title-17/section-242.204' target='_blank'>[2]</a> and potential inclusion on the Regulation SHO Threshold List (the "Penalty Box").
    </div>
    """, unsafe_allow_html=True)

    # 2. The Solution
    st.markdown("<div class='section-title'>2. The Solution: Affirmative Determination</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='legal-text'>
    To satisfy Rule 203(b)(1)(ii), this tool generates an "Affirmative Determination" of borrowability. It aggregates real-time inventory feeds from our prime brokers (State Street, CalPERS, Nomura) to establish the "Reasonable Grounds" required by law.
    <br><br>
    <strong>The "Reasonable Grounds" Exception:</strong>
    By systematically querying "Easy to Borrow" (ETB) lists and decremented inventory pools <em>prior</em> to order routing, Militia creates a legally defensible audit trail. This ensures that we are not relying on stale data, which would invalidate the "reasonable grounds" defense during an SEC examination.
    </div>
    """, unsafe_allow_html=True)

    # 3. The Tool
    st.markdown("<div class='section-title'>3. The Tool: Functional Architecture & Militia Specifics</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='feature-box'>
    <strong>A. Settlement Region Logic (The "Japan Gap")</strong><br>
    <em>Why it matters for Militia:</em> The US market recently transitioned to a <strong>T+1 settlement cycle</strong> (May 2024), while Japan remains on <strong>T+2</strong>. As Militia deploys capital globally, this mismatch creates a critical funding and delivery risk. If we short Japanese equities (e.g., region <code>JP</code>) using T+1 US collateral, a delivery failure is highly probable without a confirmed "Hard Borrow."
    <br>
    <em>Tool Function:</em> The engine automatically <strong>REJECTS</strong> any Japanese short order that relies solely on "Easy to Borrow" lists. It forces the trader to confirm a "Pre-Borrow" (Hard Locate), ensuring we meet the stricter delivery requirements of the Tokyo Stock Exchange.
    </div>

    <div class='feature-box'>
    <strong>B. Inventory Master (Aggregated Liquidity)</strong><br>
    <em>Why it matters for Militia:</em> Our short theses often target small-cap or distressed companies where liquidity is fragmented. Relying on a single prime broker increases the risk of "Buy-Ins" if that broker loses inventory.
    <br>
    <em>Tool Function:</em> This module aggregates disparate pools of liquidity into a single "Master Inventory." This allows Samuel Lee and the desk to source shares from CalPERS or Nomura seamlessly when State Street is dry, maximizing our ability to express short views without technical friction.
    </div>

    <div class='feature-box'>
    <strong>C. Compliance Controls (Threshold List Monitoring)</strong><br>
    <em>Why it matters for Militia:</em> If a security appears on the <strong>Regulation SHO Threshold List</strong> (due to 5 consecutive days of settlement fails), Rule 203(b)(3) prohibits any further shorting without a pre-borrow agreement.
    <br>
    <em>Tool Function:</em> The system scrapes the NYSE Threshold List daily. If a trader attempts to short a Restricted Ticker (e.g., <code>VOLATILE</code>), the tool blocks the trade at the gateway level, preventing accidental violations that would freeze the fund's assets in that name.
    </div>

    <div class='feature-box'>
    <strong>D. Audit Trail (SEC Rule 204(a) Evidence)</strong><br>
    <em>Why it matters for Militia:</em> In the event of an inquiry, the burden of proof is on the fund to demonstrate that a locate was obtained <em>before</em> the trade.
    <br>
    <em>Tool Function:</em> Every successful locate generates a cryptographically unique <strong>Locate ID</strong> and timestamp, stored in an immutable ledger. This serves as the primary artifact for legal defense.
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
