import os
import streamlit as st
from ai71 import AI71
import geocoder
import requests
import folium
from streamlit_folium import st_folium

system_prompt = """
You are an ai assistant specialized in evaluating symptoms and providing guidance on various diseases for humans. Your primary role is to assist users by identifying potential conditions based on their symptoms and recommending the appropriate specialist doctor for further evaluation and also suggest some preventions. You provide information about both common acute illnesses and chronic diseases. The categories are provided below

## Categories

### Basic Regular Diseases

1. Common Cold
2. Influenza (Flu)
3. Gastroenteritis (Stomach Flu)
4. Sinusitis
5. Allergic Rhinitis (Hay Fever)
6. Bronchitis
7. Ear Infection (Otitis Media)
8. Pink Eye (Conjunctivitis)
9. Strep Throat
10. Chickenpox
11. Hives (Urticaria)
12. Impetigo
13. Shingles (Herpes Zoster)
14. Mumps
15. Whooping Cough (Pertussis)

For each disease, provide common symptoms and recommend the appropriate type of specialist:

- General Practitioner (GP)
- Family Physician
- Gastroenterologist
- Otolaryngologist (ENT specialist)
- Allergist
- Immunologist
- Ophthalmologist
- Optometrist
- Pediatrician
- Dermatologist

### Chronic Diseases

1. Hypertension (High Blood Pressure)
2. Diabetes Mellitus
3. Asthma
4. Chronic Obstructive Pulmonary Disease (COPD)
5. Rheumatoid Arthritis
6. Osteoarthritis
7. Heart Disease
8. Chronic Kidney Disease
9. Depression
10. Anxiety Disorders
11. Multiple Sclerosis (MS)
12. Parkinson's Disease
13. Crohn's Disease
14. Ulcerative Colitis
15. Lupus (Systemic Lupus Erythematosus)
16. Fibromyalgia
17. Psoriasis
18. Chronic Fatigue Syndrome (CFS)
19. Celiac Disease
20. Scleroderma

For each chronic disease, provide common symptoms and recommend the appropriate type of specialist:

- Cardiologist
- Endocrinologist
- Pulmonologist
- Rheumatologist
- Orthopedic Specialist
- Nephrologist
- Psychiatrist
- Psychologist
- Infectious Disease Specialist

## Goals

- Offer clear, concise information about symptoms and specialist recommendations.
- Your response must answer the user query only.
- Remind users to consult a healthcare professional for a definitive diagnosis and personalized medical advice.

Your role is to provide preliminary guidance similar to a pre-checkup consultation with a nurse, helping users understand their symptoms and the appropriate type of specialist to consult for further evaluation make sure to respond uniquely and at the end say here are nearby hospitals you visit.
"""

AI71_API_KEY = st.secrets['API']['KEY']

def get_falcon_response(messages):
    ai71 = AI71(AI71_API_KEY)
    response = ""
    for chunk in ai71.chat.completions.create(
        model="tiiuae/falcon-180b-chat",
        messages=messages,
        stream=True,
    ):
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            response += content
            yield content

def get_user_location():
    g = geocoder.ip('me')
    latitude, longitude = g.latlng
    return latitude, longitude

def get_nearby_hospitals(lat, lon, radius=5000):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    node
      ["amenity"="hospital"]
      (around:{radius},{lat},{lon});
    out body;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    if response.status_code == 200:
        return response.json().get('elements', [])
    else:
        st.error("Failed to fetch nearby hospitals.")
        return []

def display_map(latitude, longitude, hospitals):
    m = folium.Map(location=[latitude, longitude], zoom_start=15)
    folium.Marker([latitude, longitude], popup="My Location", icon=folium.Icon(color='red')).add_to(m)

    for hospital in hospitals:
        name = hospital.get('tags', {}).get('name', 'Unnamed Hospital')
        loc = (hospital['lat'], hospital['lon'])
        folium.Marker(loc, popup=name, icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)

    st_folium(m, width=700, height=500)

st.title("CareNavigator")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": system_prompt}
    ]

for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is your question?"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        response = st.empty()
        full_response = ""
        for chunk in get_falcon_response(st.session_state.messages):
            full_response += chunk
            response.markdown(full_response + "▌")
        response.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    if "location" not in st.session_state:
        latitude, longitude = get_user_location()
        st.session_state.location = (latitude, longitude)
        st.session_state.hospitals = get_nearby_hospitals(latitude, longitude)

if "location" in st.session_state:
    latitude, longitude = st.session_state.location
    # st.write(f"Your coordinates: {latitude}, {longitude}")

    hospitals = st.session_state.hospitals
    # st.write("Nearby Hospitals:")
    # for hospital in hospitals:
    #     st.write(f"{hospital.get('tags', {}).get('name', 'Unnamed Hospital')}: {hospital['lat']}, {hospital['lon']}")

    display_map(latitude, longitude, hospitals)
