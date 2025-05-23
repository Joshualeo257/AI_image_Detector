import streamlit as st
from PIL import Image
import numpy as np
import tensorflow as tf

# --- Configuration ---
MODEL_PATH = 'ai_image_detector.h5' # <<< IMPORTANT: REPLACE WITH YOUR MODEL PATH
IMG_WIDTH = 224  # <<< IMPORTANT: Replace with your model's expected input width
IMG_HEIGHT = 224 # <<< IMPORTANT: Replace with your model's expected input height
# For a binary classifier (Real vs AI), usually, a threshold is used.
# If model output > threshold, it's considered AI-generated.
PREDICTION_THRESHOLD = 0.5
CLASS_LABELS = {0: "Authentic (Real) Image", 1: "AI-Generated Image"} # Or adjust based on your model's output interpretation

# --- Model Loading ---
# Use st.cache_resource to load the model only once
@st.cache_resource
def load_trained_model(model_path):
    """Loads the pre-trained image classification model."""
    try:
        model = tf.keras.models.load_model(model_path)
        return model
    except Exception as e:
        st.error(f"Error loading model: {e}")
        st.error(f"Please ensure '{model_path}' is a valid Keras model file and TensorFlow is correctly installed.")
        st.error("If you haven't trained a model yet, this app won't work.")
        return None

model = load_trained_model(MODEL_PATH)

# --- Image Preprocessing ---
def preprocess_image(image_pil):
    """
    Preprocesses the uploaded PIL image to the format expected by the model.
    """
    try:
        # Resize
        image_resized = image_pil.resize((IMG_WIDTH, IMG_HEIGHT))

        # Convert to RGB if it's RGBA (to handle PNGs with alpha channel)
        if image_resized.mode == 'RGBA':
            image_resized = image_resized.convert('RGB')

        # Convert to NumPy array
        image_array = np.array(image_resized)

        # Normalize (common practice: scale to 0-1)
        image_array = image_array / 255.0

        # Expand dimensions to create a batch of 1
        # Model expects (batch_size, height, width, channels)
        image_batch = np.expand_dims(image_array, axis=0)
        return image_batch
    except Exception as e:
        st.error(f"Error preprocessing image: {e}")
        return None

# --- Prediction ---
def predict_image_class(image_batch, trained_model):
    """
    Makes a prediction using the loaded model.
    Returns:
        - predicted_class_label (str): The human-readable class label.
        - confidence (float): The model's confidence score for the prediction.
    """
    if trained_model is None or image_batch is None:
        return "Error", 0.0

    try:
        predictions = trained_model.predict(image_batch)
        # Assuming your model outputs a single probability for the "AI-generated" class (class 1)
        # If it outputs two probabilities [prob_real, prob_ai], adjust accordingly:
        # e.g., confidence_ai = predictions[0][1]

        confidence_ai = predictions[0][0] #  predictions is often [[prob]]

        if confidence_ai >= PREDICTION_THRESHOLD:
            predicted_class_index = 1 # AI-Generated
            final_confidence = confidence_ai
        else:
            predicted_class_index = 0 # Real
            final_confidence = 1 - confidence_ai # Confidence in it being Real

        predicted_class_label = CLASS_LABELS[predicted_class_index]
        return predicted_class_label, float(final_confidence)

    except Exception as e:
        st.error(f"Error during prediction: {e}")
        return "Error during prediction", 0.0

# --- Streamlit App Interface ---
st.set_page_config(layout="wide", page_title="AI-Generated Image Detector")

st.title("🖼️ AI-Generated Image Detector")
st.markdown("""
This application uses a Deep Learning model to predict whether an uploaded image
is an authentic photograph or if it has been generated by an AI model.

**Upload an image to see the prediction.**
""")

st.sidebar.header("⚙️ Controls")
uploaded_file = st.sidebar.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

# Display area
col1, col2 = st.columns(2)

with col1:
    st.subheader("Uploaded Image")
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image.", use_column_width=True)
        except Exception as e:
            st.error(f"Error displaying image: {e}")
            uploaded_file = None # Reset to allow re-upload
    else:
        st.info("Please upload an image using the sidebar.")

with col2:
    st.subheader("Prediction Results")
    if uploaded_file is not None and model is not None:
        if st.sidebar.button("🔎 Classify Image"):
            with st.spinner('Preprocessing image and making prediction...'):
                # Preprocess
                processed_image_batch = preprocess_image(image)

                if processed_image_batch is not None:
                    # Predict
                    predicted_label, confidence = predict_image_class(processed_image_batch, model)

                    if "Error" not in predicted_label:
                        if predicted_label == CLASS_LABELS[1]: # AI-Generated
                            st.error(f"**Prediction: {predicted_label}**")
                        else: # Authentic
                            st.success(f"**Prediction: {predicted_label}**")
                        st.write(f"**Confidence:** {confidence:.2%}")

                        # You can add more details or visualizations here
                        # For example, if your model outputs probabilities for multiple classes,
                        # you could show a bar chart of probabilities.
                    else:
                        st.warning("Could not make a prediction due to an error.")
        elif model is None:
             st.warning("Model not loaded. Please check the `MODEL_PATH` and ensure the model file exists.")
        else:
            st.info("Click the 'Classify Image' button in the sidebar to get the prediction.")


    elif model is None and uploaded_file is not None:
        st.error("Model could not be loaded. Please check the console for errors and ensure the model path is correct.")
    else:
        st.info("Upload an image and click 'Classify Image' to see the results here.")

st.sidebar.markdown("---")
st.sidebar.markdown("Developed for ECOE01: Image Processing with Python")
st.sidebar.markdown("Remember to replace the placeholder model with your actual trained model.")