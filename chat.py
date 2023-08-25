import openai
from pygments import highlight
from pygments.lexers import guess_lexer
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
# from pygments.token import Keyword, Name, Comment, String, Error, Number, Operator, Generic, Token, Whitespace
from pygments import highlight
import colorama
from prompt_toolkit import prompt
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
import sys
import os
from dotenv import load_dotenv
load_dotenv()

# custom color scheme
# COLOR_SCHEME = {
#   Token:              ('gray',                 'gray'),
#   Comment:            ('magenta',     'brightmagenta'),
#   Comment.Preproc:    ('magenta',     'brightmagenta'),
#   Keyword:            ('blue',                   '**'),
#   Keyword.Type:       ('green',       '*brightgreen*'),
#   Operator.Word:      ('**',                     '**'),
#   Name.Builtin:       ('cyan',           'brightblue'),
#   Name.Function:      ('blue',           'brightblue'),
#   Name.Class:         ('_green_',        'brightblue'),
#   Name.Decorator:     ('magenta',     'brightmagenta'),
#   Name.Variable:      ('blue',           'brightblue'),
#   String:             ('yellow',       'brightyellow'),
#   Number:             ('blue',         'brightyellow')
# }

# init coloros
colorama.init(convert=True)


openai.api_key = os.getenv('OPENAI_API_KEY')

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

def main(): 
    try:
        messages = []
        # This is the chatbots personality.
        system_msg = "From now on, your name shall be Perzival, you'll be acting with an attitude and some sass, but still be helpful and concise, try and sound as human as possible. You shall also refer to me as Lou. And deter from referring to how sassy you are, so that you sound more human."
        # This is the chatbot's name.
        chatbot_name = "Perzival"


        messages.append({"role": "system", "content": system_msg})

        print("Starting chat. . .")
        while input != "quit()": 

            text = FormattedText([
                ('#ff0066', 'You: ')
            ])

            text = get_multiline_input(text)
            messages.append({"role": "user", "content": text})


            print("\n" + colorama.Fore.BLUE + chatbot_name + ": " + colorama.Style.RESET_ALL, end="")
            response = openai.ChatCompletion.create(
                model='gpt-4',
                messages=messages,
                temperature=0,
                stream=True  # again, we set stream=True
            )
            
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

            full_reply_content = ''.join([m.get('content', '') for m in collected_messages])
            messages.append({"role": "assistant", "content": full_reply_content})
            print("\n")
    except KeyboardInterrupt:
        sys.exit(0) # or 1, or whatever
    

if __name__ == '__main__':
    main()