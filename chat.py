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

#dotenv stuff
import sys
import os
from dotenv import load_dotenv
load_dotenv()

# audio stuff
import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from io import BytesIO
import threading
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module='pydub')

# init coloros
colorama.init(convert=True)


openai.api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('OPENAI_MODEL')

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

myrecording = None
recording = False
def do_nothing():
    return

def record_audio():
    global myrecording
    global recording

    print("Recording...")
    myrecording = sd.rec(frames=int(60 * 44100), samplerate=44100, channels=2)
    sd.wait()
    print("Recording complete!")

def enter_audio_recording_mode():
    global recording  # Add this line
    global myrecording  # Add this line

    threading.Thread(target=record_audio).start()

    while True:
        text = FormattedText([
            ('#808080', 'Y/N: ')
        ])

        text = get_multiline_input(text)

        if text.lower() == "y":
            # Stop the recording
            recording = False
            sd.stop()

            # Convert the NumPy array to audio
            audio = AudioSegment(myrecording.tobytes(), frame_rate=44100, sample_width=myrecording.dtype.itemsize, channels=2)

            # Save it to a BytesIO object
            wav_fp = BytesIO()
            wav_fp.name = "temporary.mp3"
            audio.export(wav_fp, format="mp3")

            # Rewind the BytesIO object
            wav_fp.seek(0)

            # Pass the BytesIO object directly to OpenAI's API
            transcript = openai.Audio.transcribe("whisper-1", wav_fp)

            # Print the transcript
            print("\n" + colorama.Fore.RED + 'You' + ": " + colorama.Style.RESET_ALL, end="")
            print(transcript.text)

            return transcript.text
        elif text.lower() == "n":
            # Stop the recording
            recording = False
            sd.stop()
            return "just gimme a moment, I'm thinking. . ."



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

            text = get_multiline_input(text)
            if text == "voice":
                text = enter_audio_recording_mode()

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