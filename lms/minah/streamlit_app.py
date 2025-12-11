"""
Streamlit interface for Brainnet Trading System

This app provides a web interface for the three main models:
1. Standard Analysis - Basic technical analysis with LLM insights
2. ConvNeXt Model - Advanced pattern recognition with neural networks
3. Trading Loop - Continuous trading with configurable intervals
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from brainnet.services.engine import run_single_analysis, run_trading_loop
from brainnet.core import load_config

# Set page config
st.set_page_config(
    page_title="Brainnet Trading System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #1f77b4; text-align: center; margin-bottom: 1rem; }
    .model-card { padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 1.5rem; }
    .success { color: #28a745; }
    .warning { color: #ffc107; }
    .error { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown("<h1 class='main-header'>🧠 Brainnet Trading System</h1>", unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Model",
    ["Standard Analysis", "ConvNeXt Model", "Trading Loop"]
)

# Load configuration
config = load_config()

# Common parameters
st.sidebar.header("Common Parameters")
symbol = st.sidebar.text_input("Ticker Symbol", value="AAPL")
interval = st.sidebar.selectbox(
    "Time Interval",
    ["1d", "1h", "4h", "1w"],
    index=0
)

# Standard Analysis Page
if page == "Standard Analysis":
    st.header("📊 Standard Analysis")
    st.markdown("Run technical analysis with LLM insights")
    
    if st.button("Run Analysis", key="run_std_analysis"):
        with st.spinner("Running analysis..."):
            try:
                result = run_single_analysis(symbol)
                
                # Display results
                st.subheader("Analysis Results")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Symbol", symbol)
                    st.metric("Decision", result.get("decision", "N/A"))
                    st.metric("Confidence", f"{result.get('confidence', 0):.2%}")
                
                with col2:
                    st.metric("Current Price", f"${result.get('current_price', 0):.2f}")
                    st.metric("Signal Strength", result.get("signal_strength", "N/A"))
                    st.metric("Timeframe", interval)
                
                # Show analysis details
                with st.expander("Detailed Analysis"):
                    st.json(result)
                
                st.success("Analysis completed successfully!")
                
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")

# ConvNeXt Model Page
elif page == "ConvNeXt Model":
    st.header("🤖 ConvNeXt Model")
    st.markdown("Advanced pattern recognition with neural networks")
    
    device = st.selectbox(
        "Device",
        ["cuda", "cpu"],
        index=1,
        help="Select 'cuda' for GPU acceleration if available"
    )
    
    use_llm = st.checkbox("Enable LLM Analysis", value=True, 
                         help="Combine neural network predictions with LLM insights")
    
    if st.button("Run ConvNeXt Analysis", key="run_convnext"):
        with st.spinner("Running ConvNeXt analysis..."):
            try:
                # This is a placeholder - you'll need to implement or import the actual ConvNeXT function
                # result = run_convnext_analysis(symbol, interval, device, not use_llm)
                st.warning("ConvNeXt integration is not yet implemented in this interface.")
                st.info("Please use the command line interface for now.")
                
                # Example of how the display would look once implemented
                st.subheader("ConvNeXt Analysis Results")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Pattern Detected", "Bullish Continuation")
                    st.metric("Confidence", "78.5%")
                
                with col2:
                    st.metric("Volatility Forecast", "High")
                    st.metric("Pattern Strength", "Strong")
                
                st.warning("This is a preview. Actual ConvNeXt integration is pending implementation.")
                
            except Exception as e:
                st.error(f"Error during ConvNeXt analysis: {str(e)}")

# Trading Loop Page
elif page == "Trading Loop":
    st.header("🔄 Trading Loop")
    st.markdown("Run continuous trading with configurable intervals")
    
    delay_minutes = st.number_input(
        "Check Interval (minutes)",
        min_value=1,
        max_value=1440,
        value=15,
        step=1,
        help="How often to check for new trading signals"
    )
    
    max_iterations = st.number_input(
        "Maximum Iterations",
        min_value=1,
        max_value=1000,
        value=10,
        step=1,
        help="Maximum number of iterations to run (0 for unlimited)"
    )
    
    if st.button("Start Trading Loop", key="start_loop"):
        st.warning("Trading loop execution is not yet implemented in this interface.")
        st.info("Please use the command line interface with 'python -m brainnet.services.main loop' for now.")
        
        # Example of how the display would look once implemented
        st.subheader("Trading Loop Status")
        
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        for i in range(1, 6):  # Simulate progress
            status_text.text(f"Iteration {i} of {5} - Checking for signals...")
            progress_bar.progress(i / 5)
            
            # Simulate some work
            import time
            time.sleep(1)
        
        status_text.success("Trading loop completed!")
        
        # Show example trade log
        st.subheader("Trade Log")
        log_data = {
            "Time": [datetime.now() - timedelta(minutes=i*5) for i in range(5, 0, -1)],
            "Action": ["BUY", "HOLD", "SELL", "HOLD", "BUY"],
            "Symbol": [symbol] * 5,
            "Price": [150.25, 151.10, 152.75, 151.90, 152.10],
            "Quantity": [10, 0, 10, 0, 5],
            "Status": ["FILLED", "N/A", "FILLED", "N/A", "FILLED"]
        }
        
        st.dataframe(pd.DataFrame(log_data), use_container_width=True)

# Add some spacing at the bottom
st.markdown("---")
st.markdown("### About")
st.markdown("""
This is a Streamlit interface for the Brainnet Trading System. 

**Note**: Some features may require additional setup or may not be fully implemented in the web interface yet. 
For full functionality, please use the command line interface.
""")
