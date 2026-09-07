import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt

st.title("Cancer Progression Predictor")
st.write("AI-Based Mathematical Modeling of Cyclic Mechanical Stretching")

# Load model safely
model = joblib.load("model.pkl")

# Create input widgets for your 13 variables
age = st.number_input("Age", value=68)
sex = st.selectbox("Sex (0=F, 1=M)", [0, 1])
smoking = st.selectbox("Smoking (0=N, 1=Y)", [0, 1])
smoking_pack_years = st.number_input("Smoking_PackYears", value=35.0)
tumor_size = st.number_input("Tumor Size (cm)", value=5.5)

stretch = st.number_input("Stretch (%)", value=18.0)
frequency = st.number_input("Frequency (Hz)", value=1.5)
duration = st.number_input("Stretch Duration (Hours)", value=24.0)
stiffness = st.number_input("Tissue Stiffness (kPa)", value=28.5)

fibrosis = st.number_input("Fibrosis Grade", value=4.0)
il6 = st.number_input("IL6", value=18.2)
vegf = st.number_input("VEGF", value=350.0)
ki67 = st.number_input("Ki67", value=75.0)

if st.button("Predict Risk"):
    input_data = pd.DataFrame({
        "Age": [age], "Sex": [sex], "Smoking": [smoking],
        "Smoking_PackYears": [smoking_pack_years], "Tumor_Size": [tumor_size],
        "Stretch": [stretch], "Frequency": [frequency],
        "Stretch_Duration": [duration], "Tissue_Stiffness": [stiffness],
        "Fibrosis_Grade": [fibrosis], "IL6": [il6], "VEGF": [vegf], "Ki67": [ki67]
    })

    prediction = model.predict(input_data)[0]
    st.write(f"### Prediction Score: {prediction:.3f}")