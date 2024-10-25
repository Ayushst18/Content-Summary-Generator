#Importing all the required Libraries
import streamlit as st      #for frontend user interface
from dotenv import load_dotenv      #to load environment variables
import os     
import google.generativeai as genai     #to use gemini pro LLM model
import pvleopard    #to generate audio to text transcript
from tempfile import NamedTemporaryFile     #used so to download audio file for temporary needs
from pytubefix import YouTube      #for audio downloading of YouTube videos
import textwrap
from youtube_transcript_api import YouTubeTranscriptApi     #To check transcripts of the videos and if available then to extract it

load_dotenv()  ## load all the environment variables



#Here to add our provided generativeai api key to get the access of Gemini Pro
genai.configure(api_key="API KEY")


#Fixed prompt to generate summary of the following content
prompt = """Generate a comprehensive summary of a YouTube video based on the provided transcript.
Summary should include the main information, key topics discussed, target audience, and the overall theme of the video. 
Consider the following guidelines:

Identify and summarize the main topics covered in the video.

Highlight the key points, insights, or arguments presented by the speaker.

Determine who the target audience for the video is and why.

Clearly articulate the central theme or purpose of the video.

Ensure that the summary is concise, engaging, and informative.

If applicable, mention any notable examples, anecdotes, or case studies discussed in the video.

Use clear and straightforward language to make the summary accessible to a wide audience."""


#This function will take the youtube transcript and check for the transcript availability.
#If Fails to get transcript, goes to the audio transcript generation
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]

        # Attempt to get transcript from YouTubeTranscriptApi
        try:
            transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = ""
            for i in transcript_text:
                transcript += " " + i["text"]
            return transcript
        except Exception as e:
            print(f"Error fetching transcript: {e}")

        # If transcript API fails, try audio transcription
        audio_path = download_audio(youtube_video_url)
        if audio_path:
            return transcribe_audio(audio_path)

        return None  # No transcript found

    except Exception as e:
        raise e



#This is used here for generating Summary of the follwoing transcript of the content providing the prompt and transcript.
def generate_gemini_content(transcript_text, prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt + transcript_text)
    return response.text



#As api fails to get available transcript, programs redirects to downloading the audio file of the content.
import urllib.error

def download_audio(url):
    try:
        with NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            audio_path = temp_file.name

            yt = YouTube(url)
            # Remove order_by and desc to test basic functionality
            audio_streams = yt.streams.filter(only_audio=True)
            audio_stream = audio_streams.first()

            if audio_stream:
                audio_stream.download(filename=audio_path)
                print(f"Audio downloaded to temporary file: {audio_path}")
            else:
                print("No audio stream available")
            return audio_path

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None

#Transcription of audio using Speech to Text API of picovoice ai model
def transcribe_audio(audio_path):
    try:
        access_key = "API KEY" 

        handle = pvleopard.create(access_key)
        transcript, words = handle.process_file(audio_path)

        wrapped_transcript = textwrap.fill(transcript, width=80)

        print("Transcription:")
        print(wrapped_transcript)

        output_file_path = "transcript.txt"
        with open(output_file_path, "w") as output_file:
            output_file.write(transcript)

        print(f"Transcript saved to {output_file_path}")

        return transcript

    except Exception as e:
        print(f"Error during transcription: {e}")
        return None
    
#As the transcript gets extracted, Audio file gets deleted successfully. 
    finally:
        if audio_path:
            os.remove(audio_path)
            print(f"Temporary audio file deleted: {audio_path}")



#Streamlit usage for the Frontend User Interface
st.title("YouTube Transcript to Detailed Summarizer")
youtube_link = st.text_input("Enter YouTube Video Link:")



#main function, where user will provide youtube video link to generate the summary
if youtube_link:
    video_id = youtube_link.split("=")[1]
    print(video_id)
    #Added this to show thumbnail of the video.
    st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

if st.button("Get Summary"):
    transcript_text = extract_transcript_details(youtube_link)

    if transcript_text:
        summary = generate_gemini_content(transcript_text, prompt)
        st.markdown("## Summary:")
        st.write(summary)
#Takes time to process but at the end provides the output using LLM Model a readable summary of the content.
