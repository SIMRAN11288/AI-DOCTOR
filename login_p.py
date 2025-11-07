import streamlit as st
def login_page():
  st.title("LOGIN TO AI DOCTOR ASSISTANT")
  username=st.text_input("username",)
  password=st.text_input("Password",type="password")
  login_button=st.button("login")
  if login_button:
        if username == "admin" and password == "12345":
            st.session_state["logged_in"] = True
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")
          
def check_login_status():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    return st.session_state["logged_in"]
