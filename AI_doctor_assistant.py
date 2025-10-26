import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
import requests
from dotenv import load_dotenv
import os
import re

# Load .env file
load_dotenv()

st.title("AI Doctor Assistant")
st.write('Enter patient details:')

# Basic patient info
name = st.text_input("What is your name?")
age = st.text_input("What is your age?")
sex = st.radio("Sex", ['female', 'male'])
main_symptom = st.text_input("What is your main symptom?")

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Once the main symptom is entered, proceed to diagnosis directly
if main_symptom:
    patient_data = f"Name: {name}\nAge: {age}\nSex: {sex}\nMain Symptom: {main_symptom}"

    # Disease prediction
    disease_prompt = PromptTemplate.from_template(
        "After analyzing the patient's data, detect the most probable disease:\n\n{patient_data}"
    )

    parser = StrOutputParser()

    precautions_prompt = PromptTemplate.from_template(
        "Patient data:\n{patient_data}\n\nProbable disease: {disease}\n\n"
        "Suggest a few precautions to take while suffering from {disease} in simple language so that everyone can understand. "
    )

    format_disease = RunnableLambda(
        lambda disease: {'patient_data': patient_data, 'disease': disease}
    )

    chain = disease_prompt | llm | parser | format_disease | precautions_prompt | llm | parser
    result = chain.invoke({"patient_data": patient_data})

    st.write("### 🩺 Probable Disease and Precautions")
    st.write(result)

    # Doctor specialization
    doctors_call = PromptTemplate.from_template(
        "Based on the patient's data below, output only the medical specialization "
        "(like cardiologist, dermatologist, neurologist) that would be suitable.\n\n"
        "{DATA}\n\nOutput one specialization word only."
    )

    chain2 = doctors_call | llm | parser
    doctor_type = chain2.invoke({'DATA': patient_data}).strip()

    # Location input
    current_location = st.text_input(
        "Enter your current location (the more precise, the better the nearby doctor suggestions):"
    )

    if current_location:
        #Normalize the location 
        current_location = current_location.strip().capitalize()

        # Clean the doctor type text
        doctor_type = re.sub(r"[^a-zA-Z ]", "", doctor_type).lower().split()[-1]

        # Build the Overpass query
        query = f"""
        [out:json];
        area[name="{current_location}"]->.a;
        (
          node["amenity"="{doctor_type}"](area.a);
          node["amenity"="doctors"](area.a);
          node["amenity"="clinic"](area.a);
          node["amenity"="hospital"](area.a);
        );
        out;
        """

        try:
            response = requests.get(
                "https://overpass-api.de/api/interpreter",
                params={"data": query},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            st.error(f"API request failed: {e}")
            data = {"elements": []}

        results = data.get("elements", [])

        if results:
            st.subheader(f"🏥 Nearby {doctor_type.title()}s in {current_location}:")
            for element in results[:5]:  # Show top 5 results
                name = element["tags"].get("name", "Unknown")
                lat = element.get("lat")
                lon = element.get("lon")
                st.write(f"**{name}**")
                st.write(f"📍 [Location on Map](https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon})")
                st.write("---")
        else:
            st.warning(f"No {doctor_type} found near {current_location}. Try a nearby city.")

