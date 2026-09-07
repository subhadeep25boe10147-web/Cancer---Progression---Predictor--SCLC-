import tkinter as tk
import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from tkinter import messagebox
import joblib
from fpdf import FPDF
import os
model = joblib.load('dist/model.pkl')
import sys
import os

# Determine if the application is running as a compiled executable or normal script
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# Build the absolute path to model.pkl
model_path = os.path.join(application_path, "model.pkl")

# Load the model safely
model = joblib.load(model_path)

import random  # Used for mocking the prediction


# ==========================================
# 1. LIVE GRAPH UPDATE FUNCTION
# ==========================================
def update_plot(*args):
    """Updates the sine wave graph in real-time when Stretch or Frequency changes."""
    try:
        A = float(stretch_var.get()) if stretch_var.get() else 0.0
        f = float(freq_var.get()) if freq_var.get() else 0.0
    except ValueError:
        A, f = 0.0, 0.0  # Default to flatline if user types text instead of numbers

    t = np.linspace(0, 2, 500)  # 2 seconds of time
    y = A * np.sin(2 * np.pi * f * t)  # S(t) = A * sin(2πft)

    ax.clear()
    ax.plot(t, y, color="#2980B9", linewidth=2)
    ax.set_title("Live Mechanotransduction: S(t) = A*sin(2πft)", fontsize=10)
    ax.set_xlabel("Time (s)", fontsize=8)
    ax.set_ylabel("Stretch (%)", fontsize=8)
    ax.grid(True, linestyle="--", alpha=0.6)


    # Keep the Y-axis fixed so the wave visually grows
    ax.set_ylim(-30, 30)
    canvas.draw()


# ==========================================
# 2. PREDICTION & COLOR LOGIC
# ==========================================
def predict_action():
    try:
        # Create the DataFrame from the current inputs
        patient = pd.DataFrame({
            "Age": [int(all_vars["Age"].get())],
            "Sex": [int(all_vars["Sex (0=F, 1=M)"].get())],
            "Smoking": [int(all_vars["Smoking (0=N, 1=Y)"].get())],
            "Smoking_PackYears": [float(all_vars["Smoking Pack Years"].get())],
            "Stretch": [float(all_vars["Stretch (%)"].get())],
            "Frequency": [float(all_vars["Frequency (Hz)"].get())],
            "Stretch_Duration": [int(all_vars["Stretch Duration (Hours)"].get())],
            "Fibrosis": [int(all_vars["Fibrosis Grade"].get())],
            "Tissue_Stiffness": [float(all_vars["Tissue Stiffness (kPa)"].get())],
            "IL6": [float(all_vars["IL6"].get())],
            "VEGF": [float(all_vars["VEGF"].get())],
            "Ki67": [float(all_vars["Ki67"].get())],
            "Tumor_Size": [float(all_vars["Tumor Size (cm)"].get())]
        })

        # Make prediction
        real_score = model.predict(patient)[0]

        # Update UI
        score_label.config(text=f"{real_score:.3f}")

        if real_score <= 0.333:
            risk_label.config(text="LOW RISK", bootstyle="success")
        elif real_score <= 0.666:
            risk_label.config(text="MODERATE RISK", bootstyle="warning")
        else:
            risk_label.config(text="HIGH RISK", bootstyle="danger")

    except Exception as e:
        messagebox.showerror("Error", f"Please check inputs:\n{e}")


def clear_action():
    """Clears all fields, resets graph and results."""
    for var in all_vars.values():
        var.set("")
    score_label.config(text="0.000", bootstyle="dark")
    risk_label.config(text="------", bootstyle="secondary")
    update_plot()


def generate_report():
    try:
        # 1. Make sure a prediction has been run first
        current_score = score_label.cget("text")
        if current_score == "0.000":
            messagebox.showwarning("Warning", "Please run a prediction before generating a report.")
            return

        # 2. Save a temporary screenshot of the matplotlib graph
        fig.savefig("temp_graph.png")

        # 3. Create the PDF document
        pdf = FPDF()
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", 'B', 18)
        pdf.cell(200, 10, txt="Cancer Progression Risk Report", ln=True, align='C')
        pdf.ln(10)  # Add some blank space

        # Inputs Section
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(200, 10, txt="1. Patient & Biomechanical Inputs:", ln=True, align='L')

        pdf.set_font("Helvetica", '', 11)
        for key, var in all_vars.items():
            # Grabs every input label and the number you typed
            pdf.cell(200, 8, txt=f"    - {key}: {var.get()}", ln=True, align='L')

        pdf.ln(5)

        # AI Result Section
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(200, 10, txt="2. AI Prediction Result:", ln=True, align='L')

        pdf.set_font("Helvetica", 'B', 14)
        current_risk = risk_label.cget("text")
        pdf.cell(200, 10, txt=f"    Score: {current_score} ({current_risk})", ln=True, align='L')
        pdf.ln(5)

        # Embed the Graph
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(200, 10, txt="3. Mechanotransduction Analysis:", ln=True, align='L')
        # Insert the image we saved earlier (x=15 positions it slightly indented)
        pdf.image("temp_graph.png", x=15, w=150)

        # 4. Save the PDF to your project folder
        pdf.output("Clinical_Report.pdf")

        # 5. Clean up by deleting the temporary image file
        if os.path.exists("temp_graph.png"):
            os.remove("temp_graph.png")

        messagebox.showinfo("Success", "Report successfully saved as 'Clinical_Report.pdf' in your project folder!")

    except Exception as e:
        messagebox.showerror("Error", f"Could not generate report: {e}")


# ==========================================
# 3. MAIN WINDOW & THEME SETUP
# ==========================================
# "cosmo" is a clean, medical-looking theme
app = ttk.Window(themename="cosmo")
app.title("Cancer Progression Predictor")
app.geometry("1100x800")

# Header
header_frame = ttk.Frame(app)
header_frame.pack(pady=15)
ttk.Label(header_frame, text="Cancer Progression Predictor", font=("Segoe UI", 24, "bold")).pack()
ttk.Label(header_frame, text="AI-Based Mathematical Modeling of Cyclic Mechanical Stretching",
          font=("Segoe UI", 12, "italic"), bootstyle="secondary").pack()

# Main Container (splits left for inputs, right for graph)
main_container = ttk.Frame(app)
main_container.pack(fill=BOTH, expand=True, padx=20)

left_panel = ttk.Frame(main_container)
left_panel.pack(side=LEFT, fill=Y, expand=True)

right_panel = ttk.Frame(main_container)
right_panel.pack(side=RIGHT, fill=BOTH, expand=True, padx=(20, 0))

all_vars = {}  # Dictionary to store our input variables

# ==========================================
# 4. SCIENTIFIC TOOLTIPS DICTIONARY
# ==========================================
tooltips_text = {
    "Ki67": "Proliferation marker reflecting ERK/Cyclin D1 activity.",
    "Tissue Stiffness (kPa)": "Measures Extracellular Matrix (ECM) rigidity.",
    "VEGF": "Triggered by HIF-1α to promote angiogenesis.",
    "IL6": "Pro-inflammatory cytokine linked to tumor progression.",
    "Fibrosis Grade": "Higher grades indicate stiffer extracellular matrix.",
    "Stretch (%)": "Amplitude of cyclic respiratory strain.",
    "Frequency (Hz)": "Breathing rate / mechanical cyclic frequency."
}


# Helper function to create grouped inputs
def create_input_group(parent, title, fields):
    frame = ttk.LabelFrame(parent, text=title, padding=15, bootstyle="info")
    frame.pack(fill=X, pady=10)

    for i, field in enumerate(fields):
        ttk.Label(frame, text=field, font=("Segoe UI", 11)).grid(row=i, column=0, sticky=E, pady=5, padx=5)

        var = ttk.StringVar()
        all_vars[field] = var
        entry = ttk.Entry(frame, textvariable=var, width=15, font=("Segoe UI", 11))
        entry.grid(row=i, column=1, sticky=W, pady=5)

        # Add Hover Tooltip if it exists in our dictionary


# Create the Groups
create_input_group(left_panel, "1. Patient Profile",
                   ["Age", "Sex (0=F, 1=M)", "Smoking (0=N, 1=Y)", "Smoking Pack Years", "Tumor Size (cm)"])
create_input_group(left_panel, "2. Biomechanical Dynamics",
                   ["Stretch (%)", "Frequency (Hz)", "Stretch Duration (Hours)", "Tissue Stiffness (kPa)"])
create_input_group(left_panel, "3. Molecular Biomarkers", ["Fibrosis Grade", "IL6", "VEGF", "Ki67"])

# ==========================================
# 5. MATPLOTLIB LIVE GRAPH SETUP
# ==========================================
graph_frame = ttk.LabelFrame(right_panel, text="Real-Time Stretch Visualization", padding=10, bootstyle="primary")
graph_frame.pack(fill=BOTH, expand=True, pady=10)

fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
fig.patch.set_facecolor('#fdfdfd')  # Matches the theme background
canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(fill=BOTH, expand=True)

# Bind the Stretch and Frequency variables to the update_plot function
stretch_var = all_vars["Stretch (%)"]
freq_var = all_vars["Frequency (Hz)"]
stretch_var.trace_add("write", update_plot)
freq_var.trace_add("write", update_plot)

# Initial plot draw
update_plot()

# ==========================================
# 6. BUTTONS & RESULT SECTION
# ==========================================
btn_frame = ttk.Frame(right_panel)
btn_frame.pack(pady=20)

ttk.Button(btn_frame, text="Predict Risk", bootstyle="primary", width=15, command=predict_action).grid(row=0, column=0,
                                                                                                       padx=10)
ttk.Button(btn_frame, text="Clear Data", bootstyle="secondary", width=15, command=clear_action).grid(row=0, column=1,
                                                                                                     padx=10)
ttk.Button(btn_frame, text="Generate Report", bootstyle="info", width=15, command=generate_report).grid(row=0, column=2, padx=10)
result_frame = ttk.LabelFrame(right_panel, text="AI Prediction Result", padding=20, bootstyle="dark")
result_frame.pack(fill=X, pady=10)

score_label = ttk.Label(result_frame, text="0.000", font=("Segoe UI", 36, "bold"), bootstyle="dark")
score_label.pack(pady=5)

risk_label = ttk.Label(result_frame, text="------", font=("Segoe UI", 18, "bold"), bootstyle="secondary")
risk_label.pack()

app.mainloop()