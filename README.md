# 🫁 SCLC Cancer Progression Predictor

An **AI-based machine learning application** designed to predict the **Cancer Progression Score (CPS)** in **Small Cell Lung Cancer (SCLC)** using selected clinical and experimental parameters.

The project combines a trained machine learning model, a structured dataset, and a user-friendly desktop GUI to provide quick and accessible cancer progression predictions.

> **Note:** This project is intended for **academic and research purposes only** and should not be used for clinical diagnosis or treatment decisions.

---

## 🚀 Features

### 🤖 Machine Learning Model

* Pre-trained machine learning model stored as `model.pkl`.
* Predicts the **Cancer Progression Score (CPS)** from the provided input parameters.
* Model can be retrained using the included training script and dataset.

### 🖥️ Graphical User Interface

* Simple and user-friendly desktop application.
* Allows users to enter the required parameters.
* Provides an instant predicted progression score.

### 📊 Dataset

* Includes the dataset used for model development and training.
* Stored in CSV format for easy inspection and modification.

### 📦 Standalone Windows Application

* A compiled `.exe` version is provided.
* Users can run the application without installing Python or configuring the development environment.

---

## 📂 Project Structure

```text
SCLC-Cancer-Progression-Predictor/
│
├── dataset.csv
│       └── Dataset used for training the machine learning model
│
├── train_model.py
│       └── Script for training and saving the ML model
│
├── predictor.py
│       └── Core prediction logic
│
├── predictor_gui.py
│       └── Graphical User Interface for the predictor
│
├── model.pkl
│       └── Pre-trained machine learning model
│
├── requirements.txt
│       └── Required Python libraries and dependencies
│
├── predictor_gui.spec
│       └── PyInstaller configuration file
│
└── dist/
        └── predictor_gui.exe
                └── Standalone Windows executable
```

---

## 🧠 How the Project Works

The prediction workflow can be summarized as:

```text
Input Parameters
       ↓
Data Processing
       ↓
Machine Learning Model
       ↓
Cancer Progression Prediction
       ↓
Predicted CPS
```

The user provides the required input parameters through the graphical interface. These values are passed to the trained machine learning model, which generates the predicted **Cancer Progression Score (CPS)**.

---

## 💻 Installation & Setup

### Prerequisites

Make sure you have the following installed:

* Python 3.x
* pip
* Git

### 1. Clone the Repository

```bash
https://github.com/subhadeep25boe10147-web/Cancer---Progression---Predictor--SCLC-.git
```

Navigate to the project directory:

```bash
cd SCLC--Cancer--Progression--Predictor
```

### 2. Install Dependencies

Install the required Python packages using:

```bash
pip install -r requirements.txt
```

### 3. Run the Application

Launch the graphical interface with:

```bash
python predictor_gui.py
```

---

## 🛠️ Training the Model

If you want to retrain the machine learning model using the provided dataset, run:

```bash
python train_model.py
```

This process trains the model using `dataset.csv` and generates the trained model file.

After training, the prediction system can use the generated model to make new predictions.

---

## 🔮 Making Predictions

The prediction functionality is implemented in:

```text
predictor.py
```

The GUI application uses this prediction logic to process user inputs and display the resulting **Cancer Progression Score (CPS)**.

---

## 🖥️ Running the Standalone Application

A Windows executable is available in the `dist` directory:

```text
dist/predictor_gui.exe
```

Simply launch the executable to use the application without manually running the Python source code.

> **Windows Note:** Depending on your system's security settings, Windows Defender or SmartScreen may display a warning for an independently compiled executable.

---

## 📋 Technologies Used

| Technology        | Purpose                       |
| ----------------- | ----------------------------- |
| **Python**        | Core programming language     |
| **Scikit-learn**  | Machine learning model        |
| **Pandas**        | Dataset processing            |
| **NumPy**         | Numerical computation         |
| **Tkinter**       | Graphical user interface      |
| **Joblib/Pickle** | Model serialization           |
| **PyInstaller**   | Windows executable generation |

---

## 📈 Project Workflow

```text
Dataset Collection
        ↓
Data Preprocessing
        ↓
Feature Selection
        ↓
Model Training
        ↓
Model Evaluation
        ↓
Model Serialization
        ↓
GUI Integration
        ↓
CPS Prediction
```

---

## 🎯 Project Objective

The primary objective of this project is to demonstrate how **artificial intelligence and machine learning** can be integrated into a biomedical research workflow for predicting cancer progression.

The project provides a practical example of combining:

* Biomedical parameters
* Dataset-based analysis
* Machine learning
* Predictive modeling
* Python programming
* Graphical user interface development

---

## 🔬 Research Context

**Small Cell Lung Cancer (SCLC)** is an aggressive form of lung cancer characterized by rapid growth and progression.

This project explores the application of machine learning to estimate a **Cancer Progression Score (CPS)** from selected input parameters. The approach is intended to demonstrate how computational methods can support biomedical research and experimental data analysis.

---

## ⚠️ Disclaimer

This application is developed **strictly for educational, academic, and research purposes**.

The predicted Cancer Progression Score should **not** be considered a medical diagnosis, prognosis, or treatment recommendation. The model has not been validated for clinical use and should not replace professional medical judgment.

---

## 👨‍💻 Author

Subhadeep Paul
B.Tech Bioengineering / Biomedical Engineering
VIT Bhopal University

---

## ⭐ Acknowledgement

This project was developed as part of an academic exploration of **Artificial Intelligence and Machine Learning in Biomedical Engineering**, with a focus on computational approaches to cancer progression analysis.

---

## 📜 License

This project is intended for academic and research use. If you plan to distribute or modify the project, please add an appropriate open-source license such as **MIT License**.
