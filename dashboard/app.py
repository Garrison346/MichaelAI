
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image


# Project directories
ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "runs" / "classify" / "fire_baseline"
MODEL_PATH = RUN_DIR / "weights" / "best.pt"
RESULTS_PATH = RUN_DIR / "results.csv"

# Make src/ importable when run via `streamlit run dashboard/app.py`
sys.path.insert(0, str(ROOT))
from src.perception.classifier import FireClassifier


# Load model once and reuse it across interactions
@st.cache_resource
def load_classifier(model_path: str):
    return FireClassifier(model_path, device="cpu")


# Configure dashboard
st.set_page_config(
    page_title="MichaelAI Dashboard",
    page_icon="🔥",
    layout="wide",
)

st.title("🔥 MichaelAI")
st.caption("Fire / No-Fire Classification Dashboard")

prediction_tab, training_tab = st.tabs([
    "Image Classification",
    "Training Metrics",
])


# Image classification tab
with prediction_tab:
    st.header("Classify an Image")

    uploaded_file = st.file_uploader(
        "Upload a JPG or PNG image",
        type=["jpg", "jpeg", "png"],
    )

    if not MODEL_PATH.exists():
        st.error(f"Model checkpoint not found: {MODEL_PATH}")

    elif uploaded_file is not None:
        image = Image.open(uploaded_file).convert("RGB")

        left, right = st.columns(2)

        with left:
            st.image(image, caption="Uploaded image", width="stretch")

        with right:
            # Run image classification
            prediction = load_classifier(str(MODEL_PATH)).predict(image)

            scores = {
                "fire": prediction["fire_probability"],
                "nofire": prediction["nofire_probability"],
            }

            predicted_label = prediction["label"]

            st.subheader("Prediction")
            st.metric(
                "Predicted Class",
                predicted_label.upper(),
            )

            # Display probability for each class
            for label, probability in scores.items():
                st.write(f"{label}: {probability:.2%}")
                st.progress(probability)

            st.caption(
                "Probabilities are model estimates, "
                "not guarantees of correctness."
            )


# Training metrics tab
with training_tab:
    st.header("Training Performance")

    if RESULTS_PATH.exists():
        # Ultralytics logs epoch metrics to CSV
        df = pd.read_csv(RESULTS_PATH)
        df.columns = df.columns.str.strip()

        st.subheader("Training History")

        # Plot whatever numeric metrics are available
        numeric_columns = [
            col for col in df.select_dtypes(include="number").columns
            if col != "epoch"
        ]

        selected_metrics = st.multiselect(
            "Select metrics to plot",
            options=numeric_columns,
            default=numeric_columns[:2],
        )

        if selected_metrics:
            chart_data = df.set_index("epoch")[selected_metrics]
            st.line_chart(chart_data)

        with st.expander("Raw Training Data"):
            st.dataframe(df, width="stretch")

    else:
        st.info(
            "No training results found. "
            "Complete a training run first."
        )
