# ai stuff
import openai

# syntax highlighting
from pygments import highlight
from pygments.lexers import guess_lexer
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
import colorama
from prompt_toolkit import prompt
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
# init colors
colorama.init(convert=True)

#dotenv stuff
import sys
import os
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('OPENAI_MODEL')

# audio stuff
import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from io import BytesIO
import keyboard
import time
import threading
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module='pydub')


def remove_first_and_last_line(multiline_string):
    lines = multiline_string.strip().split('\n')
    return '\n'.join(lines[1:-1])

# syntax highlighting
def colorize_code(code):

    lines = code.split('\n')
    language = lines[0][3:].strip() 
    try:
        lexer = get_lexer_by_name(language)
    except:
        lexer = guess_lexer(code)

#   formatter = TerminalFormatter(bg='dark', colorscheme=COLOR_SCHEME)
    formatter = TerminalFormatter(bg='dark')
    return highlight(remove_first_and_last_line(code), lexer, formatter)

def count_backticks(response):
    count = 0
    for char in response:
        if char == '`':
            count += 1
    return count

def get_multiline_input(prompt_message):
    result = prompt(prompt_message, multiline=True)
    return result

def print_full_message_iteratively(response):

    # create variables to collect the stream of chunks
    collected_chunks = []
    collected_messages = []

    # Initialize an empty string to store the code block
    code_block = ""
    # Initialize a flag to indicate whether we're inside a code block
    in_code_block = False
    backtickCounter = 0
    chunksCounter = 0
    maxAllowedChunks = 2

    # iterate through the stream of events
    for chunk in response:
        chunk_message = chunk['choices'][0]['delta']  # extract the message
        collected_messages.append(chunk_message)  # save the message
        collected_chunks.append(chunk)  # save the event response
        if not chunk_message: continue

        backtickCounter += count_backticks(chunk_message.content)
        if backtickCounter > 0:
            chunksCounter += 1

        if maxAllowedChunks < chunksCounter:
            chunksCounter = 0
            backtickCounter = 0


        if backtickCounter >= 3:
            chunksCounter = 0
            backtickCounter = 0
            in_code_block = not in_code_block

        
        if in_code_block :
            code_block += chunk_message.content
            continue

        if not code_block == "" and not in_code_block:
            code_block += chunk_message.content
            print(colorize_code(code_block), end="")
            code_block = ''
            print("\n")
            continue

        if backtickCounter <= 1:
            print(chunk_message.content, end="", flush=True)

    return ''.join([m.get('content', '') for m in collected_messages])

class AudioRecorder:
    def __init__(self):
        self.isRecording = False
        self.buffer = np.empty((0,2), dtype='int16')

    def record_audio(self):
        print("Recording...")
        with sd.InputStream(samplerate=44100, channels=2, device=1, dtype='int16') as stream:
            while self.isRecording:
                data, overflowed = stream.read(stream.read_available)
                self.buffer = np.append(self.buffer, data, axis=0)
        print("Recording complete!")

    def convert_recording_to_audio_bytes(self):
    
        # Convert the NumPy array to audio
        audio = AudioSegment(self.buffer.tobytes(), frame_rate=44100, sample_width=self.buffer.dtype.itemsize, channels=2)

        # Save it to a BytesIO object
        mp3_fp = BytesIO()
        mp3_fp.name = "temporary.mp3"
        audio.export(mp3_fp, format="mp3")

        # Rewind the BytesIO object
        mp3_fp.seek(0)
        return mp3_fp

    def enter_audio_recording_mode(self):
        text = FormattedText([
            ('#808080', 'Hold R to record... ')
        ])
        print_formatted_text(text)

        while True:
            if keyboard.is_pressed('r') and not self.isRecording:
                self.isRecording = True

                #Start recording in another thread
                threading.Thread(target=self.record_audio).start()
            elif not keyboard.is_pressed('r') and self.isRecording:
                self.isRecording = False
                sd.stop()

                mp3_fp = self.convert_recording_to_audio_bytes()

                transcript = openai.Audio.transcribe("whisper-1", mp3_fp, language="en")

                print("\n" + colorama.Fore.RED + 'You' + ": " + colorama.Style.RESET_ALL, end="")
                print(transcript.text)
                return transcript.text

            time.sleep(0.1)


def main(): 
    try:
        messages = []
        # This is the chatbots personality.
        system_msg = "From now on, your name shall be Perzival, you'll be acting with an attitude and some sass, but still be helpful and concise, try and sound as human as possible. You shall also refer to me as Lou."
        # This is the chatbot's name.
        chatbot_name = "Perzival"


        messages.append({"role": "system", "content": system_msg})
        print("Starting chat. . .")
        while input != "quit()": 

            text = FormattedText([
                ('#ff0066', 'You: ')
            ])

            state = sys.argv[1]
            match state:
                case "voice":
                    recorder = AudioRecorder()
                    text = recorder.enter_audio_recording_mode()
                case _:
                    text = get_multiline_input(text)


            if text == "voice":
                text = AudioRecorder.enter_audio_recording_mode()
                

            messages.append({"role": "user", "content": text})


            print("\n" + colorama.Fore.BLUE + chatbot_name + ": " + colorama.Style.RESET_ALL, end="")
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=0,
                stream=True  # again, we set stream=True
            )
            
            # print the response iteratively as it streams in, colorizing code blocks, and returning the reply content for the context
            full_reply_content = print_full_message_iteratively(response)

            messages.append({"role": "assistant", "content": full_reply_content})
            print("\n")
    except KeyboardInterrupt:
        sys.exit(0) # or 1, or whatever
    

if __name__ == '__main__':
    main()