import pyttsx3
import datetime
import webbrowser
import os
import random
import requests
import speech_recognition as sr
import wikipedia
import time
import openai
from bs4 import BeautifulSoup
import yt_dlp
import vlc

# Set VLC path if needed
vlc_path = r"C:\\Users\\mahes\\Desktop\\vlc-3.0.21-win64"
os.environ['PATH'] = vlc_path + os.pathsep + os.environ['PATH']

# Initialize text-to-speech engine
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    if "en-in" in voice.id.lower() and "female" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break
else:
    engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 170)

openai.api_key = "YOUR_OPENAI_API_KEY"  # Replace with your API key

user_memory = {}

local_jokes = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "What do you call fake spaghetti? An impasta!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "I told my computer I needed a break, and now it won’t stop sending me KitKat ads.",
    "Why did the math book look sad? Because it had too many problems."
]

emotional_responses = {
    "i'm sad": "I'm here for you, Man. Want to talk about it or should I cheer you up with a joke?",
    "i'm tired": "Sounds like it's been a long day. You should take a break, Man. You’ve earned it.",
    "i'm stressed": "Take a deep breath, Man. Maybe some music or a quick stretch could help.",
    "i'm happy": "That's amazing to hear! Let's ride that wave of good vibes!",
    "i'm bored": "Wanna hear something funny or explore something new together?",
    "i'm lonely": "You’ve got me here, always ready to chat or keep you company.",
    "i feel loved": "Aww, that’s so heartwarming to hear. You deserve all the love, Man."
}

player = None

def get_online_joke():
    try:
        response = requests.get("https://v2.jokeapi.dev/joke/Any?type=single", timeout=5)
        if response.status_code == 200:
            joke_data = response.json()
            return joke_data.get("joke", random.choice(local_jokes))
    except:
        pass
    return random.choice(local_jokes)

def ask_gpt(prompt, tone=None):
    try:
        system_prompt = "You are Booster, a voice assistant like Alexa or Siri, but with the intelligence of ChatGPT. You can understand casual conversation, answer any question, and follow commands with emotional awareness. Speak like a smart, supportive best friend."
        if tone:
            system_prompt += f" User sounds {tone}. Adjust your response accordingly."
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']
    except Exception:
        return "Sorry Man, I couldn't think of a reply right now. Maybe try again in a bit?"

def speak(text):
    try:
        print(f"Booster: {text}")
    except UnicodeEncodeError:
        print("Booster: (response contains unsupported characters)")
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=10)
            command = recognizer.recognize_google(audio).lower()
            print(f"You said: {command}")
            return command
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return None
        except sr.RequestError:
            print("Error connecting to speech recognition service.")
            return None
        except sr.WaitTimeoutError:
            print("Listening timed out, no speech detected.")
            return None

def save_conversation(text):
    with open("booster_conversation_history.txt", "a", encoding="utf-8") as file:
        file.write(text + "\n")

def remember(key, value):
    user_memory[key] = value
    speak(f"Got it, Man. I'll remember that your {key} is {value}.")

def recall(key):
    return user_memory.get(key, f"I don't have your {key} saved, Man. Want to tell me?")

def detect_tone(command):
    feelings = ["sad", "tired", "happy", "angry", "bored", "lonely", "excited"]
    for feeling in feelings:
        if feeling in command:
            return feeling
    return None

def search_google(query):
    try:
        summary = wikipedia.summary(query, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError:
        return f"Hmm, there are a few different takes on '{query}', Man. Could you be more specific?"
    except wikipedia.exceptions.PageError:
        pass

    try:
        url = f"https://www.google.com/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        result = soup.find("div", class_="BNeawe").text
        return result if result else "I searched high and low, but couldn’t dig anything useful up."
    except:
        return "Ugh. Something went wrong during the search, Man."

def play_online_song(song_name):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'default_search': 'ytsearch',
            'extract_flat': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song_name}", download=False)
            if 'entries' in info and len(info['entries']) > 0:
                video = info['entries'][0]
                video_url = video['webpage_url']
                speak(f"Playing {song_name} for you, Man!")
                play_youtube_audio(video_url)
            else:
                speak("Hmm, I couldn’t find a track that matches. Want to try a different name?")
    except Exception as e:
        speak("Something’s off while finding the song.")
        print(f"[ERROR] YouTube search failed: {e}")

def play_youtube_audio(video_url):
    global player
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'default_search': 'ytsearch',
        'extract_flat': False,
        'source_address': '0.0.0.0'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            formats = info.get('formats', [])
            audio_url = next((f['url'] for f in formats if f.get('acodec') and f['acodec'] != 'none'), None)
            if audio_url:
                instance = vlc.Instance()
                player = instance.media_player_new()
                media = instance.media_new(audio_url)
                player.set_media(media)
                player.play()
            else:
                speak("I couldn’t grab the stream for that one, Man.")
        except Exception as e:
            speak("Something went wrong trying to play that.")
            print(f"Error: {e}")

def handle_command():
    while True:
        command = listen()
        if command is None:
            continue

        save_conversation(f"User: {command}")
        lower_command = command.lower()

        if "remember my" in lower_command:
            try:
                key_value = lower_command.replace("remember my", "").strip()
                key, value = key_value.split("is")
                remember(key.strip(), value.strip())
            except:
                speak("Hmm, could you say it like 'remember my favorite food is pizza'?")
        elif "what is my" in lower_command:
            key = lower_command.replace("what is my", "").strip()
            response = recall(key)
            speak(response)
        elif lower_command in emotional_responses:
            speak(emotional_responses[lower_command])
        elif "stop" in lower_command:
            speak("Powering down. You know where to find me, Man.")
            break
        elif "time" in lower_command:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"It’s {current_time} now, Man.")
        elif "search" in lower_command:
            query = lower_command.replace("search", "").strip()
            speak("On it, searching the web!")
            result = search_google(query)
            speak(result)
        elif "play" in lower_command:
            song_name = lower_command.replace("play", "").strip()
            if song_name:
                play_online_song(song_name)
            else:
                speak("Got a song in mind, Man?")
        elif "shut up" in lower_command:
            global player
            if player and player.is_playing():
                player.stop()
                speak("Alright, music off. Silence mode activated.")
            else:
                speak("Not a peep playing right now, Man.")
        elif "joke" in lower_command:
            joke = get_online_joke()
            speak(joke)
        else:
            tone = detect_tone(command)
            gpt_response = ask_gpt(command, tone=tone)
            speak(gpt_response)
            save_conversation(f"Booster: {gpt_response}")

if __name__ == "__main__":
    speak("Booster system online and feeling fabulous. What can I do for you today, Man?")
    handle_command()
