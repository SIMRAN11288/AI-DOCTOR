import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
import requests
from login_p import login_page,check_login_status
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
    display_symptoms
    # Disease prediction
    disease_prompt = PromptTemplate.from_template(
        "After analyzing the patient's data, detect the most probable disease:\n\n{patient_data}"
    )
     # 🧠 Split symptoms using regex to handle commas, semicolons, or multiple spaces
    symptoms_list = re.split(r'[,\n; ]+', symptoms_input)
    
    # Clean empty and capitalize
    symptoms_list = [sym.strip().capitalize() for sym in symptoms_list if sym.strip()]

    st.markdown("### 🩺 Symptoms You Entered:")
    for s in symptoms_list:
        st.markdown(f"- {s}")  # display in bullet points

    # Prepare patient data neatly
    combined_symptoms = ", ".join(symptoms_list)
    st.write(combined_symptoms)
    parser = StrOutputParser()

    precautions_prompt = PromptTemplate.from_template(
        "Patient data:\n{patient_data}\n\nProbable disease: {disease}\n\n"
        "Suggest a very few precautions to take while suffering from {disease} in simple language so that everyone can understand."
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
    doctor_type = re.sub(r"[^a-zA-Z ]", "", doctor_type).lower().strip()

    # Location input
    current_location = st.text_input(
        "Enter your current location (the more precise, the better the nearby doctor suggestions):"
    )

    if current_location:
        current_location = current_location.strip().capitalize()

        # --- Load doctors from text file ---
        doctor_list = []
        if os.path.exists("doctors.txt"):
            with open("doctors.txt", "r") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) == 3:
                        name_d, specialization, phone = [p.strip() for p in parts]
                        meet_link = None
                    elif len(parts) == 4:
                        name_d, specialization, phone, meet_link = [p.strip() for p in parts]
                    else:
                        continue
                    doctor_list.append({
                        "name": name_d,
                        "specialization": specialization.lower(),
                        "phone": phone,
                        "meet_link": meet_link
                    })

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

        # API call
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

        # Show nearby or fallback
        if results:
            st.subheader(f"🏥 Nearby {doctor_type.title()}s in {current_location}:")
            for element in results[:5]:
                name_d = element["tags"].get("name", "Unknown")
                phone = element["tags"].get("phone") or element["tags"].get("contact:phone", "Not available")
                lat = element.get("lat")
                lon = element.get("lon")
                st.write(f"**{name_d}**")
                st.write(f"📞 Phone: xxxxxxx789")
                st.write(f"📍 [Location on Map](https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon})")
                st.write("---")

        
            # Fallback local doctors
            fallback_doctors = [d for d in doctor_list if doctor_type in d["specialization"].lower()]
            if fallback_doctors:
                st.subheader(f"🏥 Suggested {doctor_type.title()}s from local list:")
                for doc in fallback_doctors:
                    st.write(f"**{doc['name']}**")
                    st.write(f"📞 Phone: {doc['phone']}")
                    if doc.get("meet_link"):
                        st.markdown(f"[💬 Join Google Meet]({doc['meet_link']})", unsafe_allow_html=True)
                    st.write("---")
            else:
                st.warning(f"No {doctor_type} found near {current_location}. Try a nearby city.")





