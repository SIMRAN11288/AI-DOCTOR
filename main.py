import streamlit as st
from login_p import login_page, check_login_status
from doctor_assistant import doctor_assistant

# Check login
logged_in = check_login_status()

if not logged_in:
    login_p()
else:
    doctor_assistant()
