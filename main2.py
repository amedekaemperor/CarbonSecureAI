import streamlit as st
import pandas as pd
import pickle
import pydeck

# loding model
@st.cache_resource
def load_model():
    with open("best_pipeline.pkl", "rb") as f:
        return pickle.load(f)

pipeline = load_model()

st.header("CarbonSecureAI")

# Sidebar
with st.sidebar:
    st.markdown("## About CarbonSecureAI")

    st.markdown("""
    For carbon capture and storage (CCS) to effectively support climate change 
    mitigation, stored CO₂ must remain securely isolated from the atmosphere 
    and oceans for **at least 10,000 years**.  

    Since direct experiments over such timescales are impossible, 
    **CarbonSecureAI** leverages deep learning to predict long-term 
    storage security.  

    The model was trained on the **largest global dataset of natural CO₂ 
    reservoirs** (Miocic et al., 2016), which represent storage systems where 
    CO₂ has been naturally trapped for **10⁴–10⁶ years** across diverse 
    geological settings.  

    ---
    **Project Lead**  
    Amedeka Emperor  
    Research Assistant, Net-Zero Carbon Emission, KNUST  
    amedekaemperor@gmail.com
    """)


# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["General", "Storage Capacity", "Injectivity", "Seal Integrity", "Summary", "Security Assessment", "Visualization"])

# --- Tab 1 ---
with tab1:
    st.subheader("General Information")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Reservoir Name", placeholder="Name", key="reservoir_name")
        st.text_input("Location", placeholder="Location", key="location")

    with col2:
        st.number_input("Longitude", step=0.01, format="%.4f", key="longitude")
        st.number_input("Latitude", step=0.01, format="%.4f", key="latitude")

# --- Tab 2 ---
with tab2:
    st.subheader("Storage Capacity")

    # Ensure storage_capacity exists in session_state
    if "storage_capacity" not in st.session_state:
        st.session_state.storage_capacity = 0.0

    # Direct input option (will update if user clicks "Calculate")
    user_capacity = st.number_input(
        "Storage Capacity (Mt)", 
        min_value=0.0, 
        step=0.1, 
        format="%.2f", 
        key="storage_capacity"
    )

    st.markdown("#### Or provide reservoir parameters:")

    col3, col4 = st.columns(2)
    with col3:
        area = st.number_input("Area (m²)", min_value=0.0, step=100.0, format="%.2f", key="area")
        thickness = st.number_input("Thickness (m)", min_value=0.0, step=1.0, format="%.2f", key="thickness")
        porosity = st.number_input("Porosity (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.2f", key="porosity")

    with col4:
        co2_density = st.number_input("CO₂ Density (kg/m³)", min_value=0.0, step=1.0, format="%.2f", key="co2_density")
        eff_factor = st.number_input(
            "Storage Efficiency Factor (%)", 
            min_value=0.0, 
            max_value=100.0, 
            step=0.1, 
            format="%.2f", 
            key="eff_factor",
            help="Fraction of the pore volume that can be filled by CO₂."
        )

        # Function to update storage capacity in session_state
        def calculate_capacity():
            porosity_val = st.session_state.porosity / 100
            eff_factor_val = st.session_state.eff_factor / 100
            storage_capacity_calc = (
                st.session_state.area 
                * st.session_state.thickness 
                * porosity_val 
                * st.session_state.co2_density 
                * eff_factor_val
            )
            # Save result directly in Mt
            st.session_state.storage_capacity = storage_capacity_calc / 1e6  

    # Button with callback
    st.button("Calculate Storage Capacity", on_click=calculate_capacity, type="primary")


# --- Tab 3 ---
with tab3:
    st.subheader("Injectivity Parameters")

    col5, col6 = st.columns(2)
    with col5:
        pressure = st.number_input("Pressure (MPa)", min_value=0.0, step=0.1, format="%.2f", key="pressure")
        temperature = st.number_input("Temperature (°C)", min_value=0.0, step=0.1, format="%.2f", key="temperature")
        depth = st.number_input("Depth (m)", min_value=0.0, step=1.0, format="%.2f", key="depth")

    with col6:
        # Reuse values from Tab 2 if available
        co2_density_tab2 = st.session_state.get("co2_density", 0.0)
        thickness_tab2 = st.session_state.get("thickness", 0.0)

        co2_density_t3 = st.number_input(
            "CO₂ Density (kg/m³)",
            min_value=0.0,
            step=1.0,
            format="%.2f",
            key="co2_density_t3",
            value=co2_density_tab2 if "co2_density_t3" not in st.session_state else st.session_state.co2_density_t3
        )

        thickness_t3 = st.number_input(
            "Thickness (m)",
            min_value=0.0,
            step=1.0,
            format="%.2f",
            key="thickness_t3",
            value=thickness_tab2 if "thickness_t3" not in st.session_state else st.session_state.thickness_t3
        )


# --- Tab 4 ---
with tab4:
    st.subheader("Seal Integrity Parameters")

    col7, col8 = st.columns(2)
    with col7:
        seal_thickness = st.number_input(
            "Seal Thickness (m)",
            min_value=0.0,
            step=1.0,
            format="%.2f",
            key="seal_thickness"
        )

    # with col8:
        faulted = st.segmented_control(
            "Faulted",
            options=["Yes", "No"],
            key="faulted"
        )
        stacked = st.segmented_control(
            "Stacked",
            options=["Yes", "No"],
            key="stacked"
        )

# --- Tab 5 ---
with tab5:
    st.subheader("Data Summary")

    # Initialize dataframe in session_state if not exists
    if "formations" not in st.session_state:
        st.session_state.formations = pd.DataFrame(
            columns=[
                'Name', 'Depth (m)', 'P (MPa)', 'T (°C)',
                'CO2 Density (kg/m3)', 'Storage Capacity (Mt)',
                'Fault', 'Seal Thickness (m)', 'Reservoir Thickness (m)',
                'Stacked', 'Longitude', 'Latitude'
            ]
        )

    # Button to add current formation
    def add_current_formation():
        fault_code = 1 if st.session_state.faulted == "Yes" else 0
        stacked_code = 1 if st.session_state.stacked == "Yes" else 0

        new_entry = {
            "Name": st.session_state.get("reservoir_name", ""),
            "Depth (m)": st.session_state.get("depth", 0.0),
            "P (MPa)": st.session_state.get("pressure", 0.0),
            "T (°C)": st.session_state.get("temperature", 0.0),
            "CO2 Density (kg/m3)": st.session_state.get("co2_density_t3", st.session_state.get("co2_density", 0.0)),
            "Storage Capacity (Mt)": st.session_state.get("storage_capacity", 0.0),
            "Fault": fault_code,
            "Seal Thickness (m)": st.session_state.get("seal_thickness", 0.0),
            "Reservoir Thickness (m)": st.session_state.get("thickness_t3", st.session_state.get("thickness", 0.0)),
            "Stacked": stacked_code,
            "Longitude": st.session_state.get("longitude", 0.0),
            "Latitude": st.session_state.get("latitude", 0.0),
        }

        st.session_state.formations = pd.concat(
            [st.session_state.formations, pd.DataFrame([new_entry])],
            ignore_index=True
        )

    st.button("Add Formation", on_click=add_current_formation, type="primary")

    # Show current table
    st.dataframe(st.session_state.formations, use_container_width=True)

    # Upload option to override
    uploaded_file = st.file_uploader("Upload CSV to override current data", type=["csv"])
    if uploaded_file is not None:
        st.session_state.formations = pd.read_csv(uploaded_file)
        st.success("Data overridden with uploaded CSV!")

# --- Tab 6 ---
with tab6:
    st.subheader("Security Assessment")

    if not st.session_state.formations.empty:
        # --- Make predictions ---
        try:
            # Only use required columns for the model
            feature_cols = [
                'Depth (m)', 'P (MPa)', 'T (°C)',
                'CO2 Density (kg/m3)', 'Storage Capacity (Mt)',
                'Fault', 'Seal Thickness (m)',
                'Reservoir Thickness (m)', 'Stacked'
            ]
            X_test = st.session_state.formations[feature_cols]

            preds = pipeline.predict_proba(X_test)[:, 1].round(2)
            st.session_state.formations["Security"] = preds
        except Exception as e:
            st.error(f"Prediction failed: {e}")

        # --- Select formation first ---
        selected_name = st.selectbox(
            "Select Formation",
            options=st.session_state.formations["Name"].tolist(),
            key="selected_formation"
        )

        # --- Show metrics ---
        if selected_name:
            row = st.session_state.formations[
                st.session_state.formations["Name"] == selected_name
            ].iloc[0]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Security", f"{row['Security']:.2f}")
            with col2:
                st.metric("Storage Capacity (Mt)", f"{row['Storage Capacity (Mt)']:.2f}")
            with col3:
                st.metric("Seal Thickness (m)", f"{row['Seal Thickness (m)']:.2f}")

        # --- Show full updated dataframe at the bottom ---
        st.markdown("### Formation Data")
        st.dataframe(st.session_state.formations, use_container_width=True)

    else:
        st.info("No formations added yet. Please add formations in the Summary tab.")


# --- Tab 7 ---
with tab7:
    st.subheader("Visualization of Formation Security")

    if not st.session_state.formations.empty and "Security" in st.session_state.formations:
        df_viz = st.session_state.formations.copy()

        # Scale point size by storage capacity
        df_viz["size"] = df_viz["Security"] * 100000  # adjust scaling factor if too small/big

        # Color mapping based on security score
        def security_to_color(sec):
            if sec >= 0.9:
                return [0, 200, 0]   # green
            elif sec >= 0.5:
                return [255, 165, 0] # orange
            else:
                return [200, 0, 0]   # red

        df_viz["color"] = df_viz["Security"].apply(security_to_color)

        # Format security as percentage string for tooltip
        df_viz["Security (%)"] = (df_viz["Security"] * 100).round(0).astype(int).astype(str) + "%"

        point_layer = pydeck.Layer(
            "ScatterplotLayer",
            data=df_viz,
            id="formations-security",
            get_position=["Longitude", "Latitude"],
            get_color="color",
            get_radius="size",
            pickable=True,
            auto_highlight=True,
        )

        view_state = pydeck.ViewState(
            latitude=float(df_viz["Latitude"].mean()),
            longitude=float(df_viz["Longitude"].mean()),
            zoom=3,
            pitch=30,
        )

        chart = pydeck.Deck(
            layers=[point_layer],
            initial_view_state=view_state,
            tooltip={"text": "{Name}\nSecurity: {Security (%)}\nStorage Capacity: {Storage Capacity (Mt)} Mt"},
        )

        st.pydeck_chart(chart, use_container_width=True)

    else:
        st.info("No formations with security scores to visualize. Please complete Security Assessment in Tab 6.")




