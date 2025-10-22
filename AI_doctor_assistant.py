import streamlit as st
from  langchain_core.prompts import ChatPromptTemplate,PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph_backend import chatbot
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
import requests
from dotenv import load_dotenv
import os
# Load .env file
load_dotenv()

st.title("AI Doctor Assistant")
st.write('enter patient details')
st.text_input("what is your name")
st.text_input("what is your age")
st.radio("sex",['female','male'])
main_symptom=st.text_input("what is your main symptom")
llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash")

#Session State Setup
if "questions" not in st.session_state:   #follow-up questions
    st.session_state.questions=[]
if "current_q" not in st.session_state:    #index of current question
    st.session_state.current_q=0
if "answers" not in st.session_state:      #dictionary {q:ans}
    st.session_state.answers={}
if "follow_up" not in st.session_state:
    st.session_state.follow_up=False
    

if main_symptom and not st.session_state.questions:
    prompt=PromptTemplate(
    template="according to the {symptom} asked 2-3 more related questions from the patient to understand the disease more precisely"
    "Do not include explanations, introductions, or numbering. "
    "Return each question on a new line.",
    input_variables=['symptom']
    )
    formatted_prompt=prompt.format(symptom=main_symptom)
    response=llm.invoke(formatted_prompt)

    st.session_state.questions = [q.strip() for q in response.content.split("\n") if q.strip()]
   
if st.session_state.questions:
    current_question= st.session_state.questions[st.session_state.current_q]
    st.write(f"Question{st.session_state.current_q + 1}:{current_question}")
    
    answer=st.text_input("answer",key=f"answer{st.session_state.current_q}")
    
    if st.button("Next"):
        if answer.strip():
            st.session_state.answers[current_question]=answer
            if st.session_state.current_q +1 < len(st.session_state.questions):
                st.session_state.current_q+=1
            else:
                st.success("All questions are answered")
                st.write("collected answers",st.session_state.answers)
                st.session_state.follow_up=True
patient_data="\n".join([f"{q}:{a}" for q,a in st.session_state.answers.items()])

            
disease=PromptTemplate.from_template("after analysing patient's data detect the probable disease:/n/n{patient_data}")

parser=StrOutputParser()
precautions=PromptTemplate.from_template("Patient data:/n{patient_data}/n/nProbable disease: {disease}/n/n"
    "Suggest a few precautions to take while suffering from {disease} in easy terms so that all can understand.")
format_disease=RunnableLambda(lambda disease: {'patient_data':patient_data,
                    'disease':disease})
chain=disease|llm|parser|format_disease|precautions|llm|parser
result=chain.invoke ({"patient_data":patient_data})
st.write("Probable disease and precaution")
st.write(result)

#doctor calling
doctors_call = PromptTemplate.from_template(
    "Based on the patient's data below, output only the medical specialization "
    "(like cardiologist, dermatologist, neurologist) that would be suitable./n/n"
    "{DATA}/n/nOutput one specialization word only."
)
current_location=st.text_input("enter your current location ( the more precise the location would the more nearest doctor we could suggest)")
# format_new=RunnableLambda(lambda doctor_type: {'doctor_type':doctor_type})
chain2=doctors_call|llm| parser
if current_location:
    doctor_type=chain2.invoke({'DATA':patient_data}).strip()
   

    
import requests
import re
if current_location:
    # Clean the doctor type text (remove punctuation etc.)
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
        response = requests.get("https://overpass-api.de/api/interpreter", params={"data": query}, timeout=20)
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
        st.warning(f"No {doctor_type} found near {current_location}")


    
            
            


