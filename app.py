from dotenv import load_dotenv
import base64
import streamlit as st
import os
import io
from PIL import Image
import pdf2image
import google.generativeai as genai
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from googletrans import Translator  # For translating the text
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph

# Load API key from .env
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to translate text to English
def translate_to_english(text):
    translator = Translator()
    detected_lang = translator.detect(text).lang  # Detect the language of the input
    
    if detected_lang != 'en':
        st.write(f"Detected language is: {detected_lang}")
        translated_text = translator.translate(text, src=detected_lang, dest='en').text  # Translate to English
        return translated_text
    return text

# Function to get the response from Gemini model
def get_gemini_response(input, pdf_content, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash-8b-latest')
    response = model.generate_content([input, pdf_content[0], prompt])
    return response.text

# Function to process the PDF and extract its first page as an image
def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        # Convert the PDF to an image
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]

        # Convert to bytes
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()  # encode to base64
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Function to generate PDF report
def generate_pdf(job_description, resume_analysis, title):
    # Create a buffer for the PDF output
    pdf_buffer = io.BytesIO()
    
    # Setup the PDF document
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    
    # Get a stylesheet for formatting text
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    
    # Add custom paragraph style for better text formatting
    paragraph_style = ParagraphStyle(
        "BodyText",
        parent=normal_style,
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.black,
        spaceAfter=6,
        alignment=0  # Left-aligned text
    )
    
    # Create the content for the PDF
    content = []
    
    # Add dynamic title
    content.append(Paragraph(title, styles["Title"]))
    
    # Add job description as a paragraph (if available)
    if job_description:
        content.append(Paragraph(f"<b>Job Description:</b><br/> {job_description}", paragraph_style))
    
    # Add resume analysis response as paragraphs
    if resume_analysis:
        content.append(Paragraph(f"<b>Resume Analysis:</b><br/> {resume_analysis}", paragraph_style))
    
    # Build the document
    doc.build(content)
    
    # Return the PDF buffer
    pdf_buffer.seek(0)  # Reset buffer pointer to start
    return pdf_buffer

# Load your portal icons (replace these paths with the actual paths to your icon images)
linkedin_icon = Image.open("./images/linkedin_icon.png")  # Add the actual path to the LinkedIn icon
indeed_icon = Image.open("./images/indeed_icon.png")  # Add the actual path to the Indeed icon

# Streamlit App
st.set_page_config(page_title="ATS Resume Expert")
st.header("ATS Tracking System")

# Function to convert image to base64 for embedding in markdown
def image_to_base64(image):
    import base64
    import io
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    return base64.b64encode(img_byte_arr.getvalue()).decode()

input_text = st.text_area("Job Description: ", key="input")
uploaded_file = st.file_uploader("Upload your resume(PDF)...", type=["pdf"])

st.subheader("Take the Job Descriptions from portals")

# LinkedIn icon and link (with resized image)
st.markdown(f"""
    <div style="display: flex; justify-content: start; gap: 10px; align-items: center;">
        <a href="https://www.linkedin.com/jobs" target="_blank">
            <img src="data:image/png;base64,{image_to_base64(linkedin_icon)}" width="40" height="40" />
        </a>
        <a href="https://www.indeed.com/jobs" target="_blank">
            <img src="data:image/png;base64,{image_to_base64(indeed_icon)}" width="30" height="30" />
        </a>
    </div>
""", unsafe_allow_html=True)

# Initialize session state for response if not already set
if "response" not in st.session_state:
    st.session_state.response = ""

# Translate job description if necessary
if input_text:
    input_text = translate_to_english(input_text)  # Translate to English if not already in English

if uploaded_file is not None:
    st.write("PDF Uploaded Successfully")

# Buttons for submitting input and generating results
submit1 = st.button("Generate Resume Analyses Report")
submit2 = st.button("ATS Score")
submit3 = st.button("Missing Skills")
submit4 = st.button("Potential Interview Questions")

input_prompt1 = """
You are an experienced Technical Human Resource Manager and also You are a skilled ATS (Applicant Tracking System) scanner, your task is to review the provided resume against the job description. 
Please share your professional evaluation on whether the candidate's profile aligns with the role. 
Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.first provide a ATS score for their
resume and then evaluate the resume whether it aligns with the job or not in readable paragraphs
then provide the 5 strengths and 5 weaknesses 
"""

input_prompt2 = """
You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality, 
your task is to evaluate the resume against the provided job description. Give me the percentage of match if the resume matches
the job description. First, the output should come as a percentage and then keywords missing and last final thoughts.
"""

input_prompt3 = """
You are a Expert HR, your task here is to find the skills which is not there in the resume but mentioned in the Job 
description, list out those missing skills, the output should be first the title should be 
Missing Skills 
1.
2.
so on list all the missing skills.
"""
input_prompt4 = """
You are an experienced Technical Human Resource Manager and skilled reqruiter in the every field esspecially techinical,
your task is to reveiew the given job description and list out 10 potential interview questions from it which are very important
for the interview, i want practical questions only.
"""

report_title = ""

if submit1 and uploaded_file is not None:
    pdf_content = input_pdf_setup(uploaded_file)
    response = get_gemini_response(input_text, pdf_content, input_prompt1)
    st.session_state.response = response  # Store response in session state
    report_title = "ATS Resume Analysis Report"  # Title for resume analysis report

elif submit2 and uploaded_file is not None:
    pdf_content = input_pdf_setup(uploaded_file)
    response = get_gemini_response(input_text, pdf_content, input_prompt2)
    st.session_state.response = response  # Store response in session state
    report_title = "ATS Score Report"  # Title for percentage match report

elif submit3 and uploaded_file is not None:
        pdf_content = input_pdf_setup(uploaded_file)
        response = get_gemini_response(input_text, pdf_content, input_prompt3)
        st.session_state.response = response
        report_title = "ATS Missing Skills Report"
        
elif submit4 and uploaded_file is not None:
        pdf_content = input_pdf_setup(uploaded_file)
        response = get_gemini_response(input_text, pdf_content, input_prompt4)
        st.session_state.response = response
        report_title = "ATS Potential Interview Questions"
    

# Only show the selectbox and download options after the response has been generated
if "response" in st.session_state and st.session_state.response:
    st.subheader("The Response is")
    st.write(st.session_state.response)  # Display response from session state

    # File format selection and download buttons
    file_format = st.selectbox("Select report format:", ["Text", "PDF"], key="file_format_selectbox")

    if file_format == "Text":
        report_text = f"Job Description:\n{input_text}\n\nResume Analysis:\n{st.session_state.response}"
        st.download_button(
            label="Download Report as Text",
            data=report_text,
            file_name="resume_analysis_report.txt",
            mime="text/plain"
        )
    elif file_format == "PDF":
        # Generate the PDF with the dynamic title
        pdf_buffer = generate_pdf(input_text, st.session_state.response, report_title)
        st.download_button(
            label="Download PDF Report",
            data=pdf_buffer,
            file_name="resume_analysis_report.pdf",
            mime="application/pdf"
        )
else:
    # Fallback when no response is available
    st.write("No response available. Please provide input and submit.")