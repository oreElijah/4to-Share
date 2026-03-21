import os
import streamlit as st
import requests
import urllib.parse
import base64
from streamlit.errors import StreamlitSecretNotFoundError


st.set_page_config(page_title="4to Share", page_icon=":camera:", layout="wide")

def resolve_api_base_url() -> str:
    try:
        return str(st.secrets.get("API_BASE_URL", os.getenv("API_BASE_URL", "http://localhost:8000"))).rstrip("/")
    except StreamlitSecretNotFoundError:
        return str(os.getenv("API_BASE_URL", "http://localhost:8000")).rstrip("/")


API_BASE_URL = resolve_api_base_url()

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

def get_header():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def api_url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def parse_error(response: requests.Response, fallback: str) -> str:
    try:
        data = response.json()
        if isinstance(data, dict):
            if "detail" in data:
                return str(data["detail"])
            if "message" in data:
                return str(data["message"])
    except Exception:
        pass
    return fallback


def switch_page(page: str):
    st.session_state.page = page
    st.rerun()

def login_page():
    st.title("Welcome to 4to share")

    email = st.text_input("Email: ")
    password = st.text_input("Password: ", type="password")
    if st.button("Login", type="primary", use_container_width=True):
        login_data = {
            "email": email,
            "password": password
        }

        response = requests.post(api_url("/v1/auth/login/"), json=login_data)
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["data"]["access_token"]
            profile_response = requests.get(
                api_url("/v1/user/profile/"),
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )

            if profile_response.status_code == 200:
                st.session_state.user = profile_response.json().get("data")
            else:
                st.session_state.user = None
            st.success("Login successful")
            st.rerun()
        else:
            st.error(parse_error(response, "Invalid credentials"))
    if st.button("Forgot Password?", use_container_width=True):
        switch_page("forgot_password")
    if st.button("Register", use_container_width=False, type="secondary", help="Don't have an account? Register here."):
        switch_page("register")

def register_page():
    st.title("Welcome to 4to share")
    
    username = st.text_input("Username: ")
    email = st.text_input("Email: ")
    firstname = st.text_input("First Name: ")
    lastname = st.text_input("Last Name: ")
    password = st.text_input("Password: ", type="password")

    if st.button("Register", type="primary", use_container_width=True):

        register_data = {
            "username": username,
            "email": email,
            "firstname": firstname,
            "lastname": lastname,
            "password": password
        }

        response = requests.post(api_url("/v1/auth/register/"), json=register_data)
        if response.status_code == 201:
            st.success("Registration successful. Please check your email to verify your account.")
        else:
            st.error(parse_error(response, "Registration failed. Please try again."))

    if st.button("Login", use_container_width=False, type="primary"):
        switch_page("login")


def forgot_password_page():
    st.title("Reset Password")
    email = st.text_input("Email: ")
    
    if st.button("Send Reset Email", type="primary", use_container_width=True):
        if email:
            response = requests.post(
                api_url("/v1/auth/forgot_password/"), 
                json={"email": email}
            )
            if response.status_code == 202:
                st.success("Password reset email sent. Please check your email for instructions.")
            elif response.status_code == 404:
                st.error("No user found with this email address.")
            else:
                st.error(parse_error(response, "Failed to send password reset email. Please try again."))
        else:
            st.error("Please enter your email.")
    
    if st.button("Back to Login", use_container_width=True):
        switch_page("login")


def reset_password_page(token: str):
    st.title("Set New Password")
    st.info(f"Reset token: `{token}`")
    
    new_password = st.text_input("New Password: ", type="password")
    confirm_password = st.text_input("Confirm Password: ", type="password")

    if new_password and confirm_password:
        if new_password != confirm_password:
            st.error("Passwords do not match.")
        else:
            if st.button("Reset Password", type="primary", use_container_width=True):
                response = requests.post(
                    api_url(f"/v1/auth/reset_password/{token}"),
                    json={"new_password": new_password}
                )
                if response.status_code == 200:
                    st.success("Password reset successful. You can now log in with your new password.")
                    st.balloons()
                    if st.button("Go to Login"):
                        switch_page("login")
                else:
                    st.error(parse_error(response, "Password reset failed. Token may have expired."))


def authenticated_home():
    st.title("4to Share")
    st.success("You are logged in")
    username = None
    if isinstance(st.session_state.user, dict):
        username = st.session_state.user.get("username")

    if username:
        st.sidebar.title(f"Hi {username}")
    else:
        st.sidebar.title("Hi there")

    if st.sidebar.button("Logout"):
        response = requests.get(api_url("/v1/auth/logout/"), headers=get_header())
        st.session_state.user = None
        st.session_state.token = None
        switch_page("login")
        st.rerun()

    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigate:", ["Home", "Upload"])

    if page == "Home":
        feed_page()
    else:
        upload_page()

def upload_page():
    file = st.file_uploader("Upload a photo or video", type=["jpg", "jpeg", "png", "mp4"])
    caption = st.text_input("Caption: ")

    if file and st.button("Upload", type="primary"):
        with st.spinner("Uploading..."):
            files = {"file": (file.name, file, file.type)}
            data = {"caption": caption}
            headers = get_header()

            response = requests.post(api_url("/v1/post/create_post/"), files=files, data=data, headers=headers)
            if response.status_code == 201:
                st.success("Posted")
            else:
                st.error(parse_error(response, "File upload failed. Please try again."))
    else:
        st.error("Please select a file to upload.")


def encode_text_for_overlay(text):
    if not text:
        return ""
    base64_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    return urllib.parse.quote(base64_text)


def create_transformed_url(original_url, transformation_params, caption=None):
    if caption:
        encoded_caption = encode_text_for_overlay(caption)
        text_overlay = f"l-text,ie-{encoded_caption},ly-N20,lx-20,fs-100,co-white,bg-000000A0,l-end"
        transformation_params = text_overlay

    if not transformation_params:
        return original_url

    parts = original_url.split("/")

    imagekit_id = parts[3]
    file_path = "/".join(parts[4:])
    base_url = "/".join(parts[:4])
    return f"{base_url}/tr:{transformation_params}/{file_path}"


def feed_page():
    st.title("Home")

    response = requests.get(api_url("/v1/post/feed"), headers=get_header())
    if response.status_code == 200:
        posts = response.json()["data"]["post"]

        if not posts:
            st.info("No posts yet! Be the first to share something.")
            return

        for post in posts:
            st.markdown("---")

            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{post['email']}** • {post['created_at'][:10]}")
            with col2:
                if post.get('is_owner', False):
                    if st.button("🗑️", key=f"delete_{post['id']}", help="Delete post"):
                        response = requests.delete(api_url(f"/v1/post/delete/{post['id']}"), headers=get_header())
                        if response.status_code == 200:
                            st.success("Post deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete post!")
            caption = post.get('caption', '')
            file_type = str(post.get("file_type", ""))

            if file_type.startswith("image/"):
                uniform_url = create_transformed_url(post['url'], "", caption)
                st.image(uniform_url, width=300)
            elif file_type.startswith("video/"):
                uniform_video_url = create_transformed_url(post['url'], "w-400,h-200,cm-pad_resize,bg-blurred")
                st.video(uniform_video_url, width=300)
                st.caption(caption)
            else:
                st.warning(f"Unsupported media type: {file_type}")
                st.caption(caption)

            st.markdown("")
    else:
        st.error("Failed to load feed")

if st.session_state.token:
    authenticated_home()

else:
    if "reset_token" in st.query_params:
        reset_password_page(st.query_params["reset_token"])
    elif st.session_state.page == "register":
        register_page()
    elif st.session_state.page == "forgot_password":
        forgot_password_page()
    else:
        login_page()

