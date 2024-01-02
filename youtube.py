"""
Title: AI YouTube Chatbot
Author: Isaac Lehman
Date: 2023-12-30
----------------------------------------
Description:
    This is a chatbot that uses OpenAI's API to chat with the user. It can also use YouTube transcripts to provide context.
----------------------------------------
Usage:
    python youtube.py

CLI Commands:
    q | quit: Quit the program
    h | history: Show the chat history
    d | delete: Delete the chat history
    c | clear: Clear the terminal
    y | youtube: Toggle youtube mode
"""
# Import web scraping modules from ./modules/web_scrape.py
from openai import OpenAI
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import copy, os, urllib, requests, datetime
import tiktoken

# ==================================================================================================
# Web Scraping Functions
# ==================================================================================================
def get_soup(url):
    """
    Returns a BeautifulSoup object of the url
    """
    # Get the soup of the url
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    } 
    try:
        page = requests.get(url, headers=headers, timeout=10)
        page.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f'Error: {e} - {url}')
        return None

    soup = BeautifulSoup(page.content, 'html.parser')
    return soup


# ==================================================================================================
# YouTube Functions
# ==================================================================================================
def google_search_youtube(query, num_results=10):
    """
    Returns a list of urls from the Google search results
    """
    # Create the Google search url and get the soup
    url = f'https://google.com/search?q={urllib.parse.quote(query)}+site:youtube.com&num={num_results}&gbv=1'
    soup = get_soup(url)

    # Find all the search result links
    result_links = [link for link in soup('a') if link['href'].startswith('/url?q=')]

    # Initialize an empty list to hold the results
    results = []

    # Loop through the result divs
    for link in result_links:
        # Find the link and title within each link
        url = link['href']
        title = link.parent.parent.find('h3')
        if title:
            title = title.text.strip()
        else:
            title = ""

        # Skip if the link is not a YouTube video
        if 'youtube.com/watch' not in url:
            continue

        # Clean up the link
        url = url[url.index('=')+1:url.index('&')]
        url = urllib.parse.unquote(url)

        # Skip if the link is already in the results
        if any([result['url'] == url for result in results]):
            continue

        # Add the link and title to the results list as a dictionary
        results.append({'url': url, 'title': title})

    return results


def get_youtube_search_results(query, num_results=10):
    """
    Returns a list of transcripts from the YouTube search results
    """
    videos = google_search_youtube(query, num_results + 10) # Get 10 extra URLs in case some of them don't have transcripts

    transcripts = [] # [{url, transcript}] an array of objects
    for video in videos:
        if len(transcripts) >= num_results:
            break # Stop if we have enough transcripts

        try:
            video_id = video['url'].split('v=')[1]
            transcript = YouTubeTranscriptApi.get_transcript(video_id) # https://github.com/jdepoix/youtube-transcript-api
        except Exception as e:
            continue # Skip this video if there is no transcript
        
        transcripts.append({
            'url': f'https://www.youtube.com/watch?v={video_id}', 
            'title': video['title'],
            'video_id': video_id, # This is the same as the video_id in the url
            'transcript': [{'text': t['text'].replace(u'\xa0', u' ').replace('\n', ' '), **t} for t in transcript] # Fix the non-breaking space
        })

    return transcripts


# ==================================================================================================
# AI Functions
# ==================================================================================================
OPEN_AI_API_KEY = '<YOUR API KEY HERE>
chat_history = [{
    'role': 'system',
    'content': f'You are a helpful AI assistant who always responds in plain text and designed to be interacted with in a terminal. Sometimes you will be given youtube transcripts to provide context. Respond to the user as if you were a human. Current Date: {datetime.datetime.now().strftime("%Y-%m-%d")}'
}] # Global variable to store chat history

client = OpenAI(
    api_key=OPEN_AI_API_KEY,
    max_retries=2, # number of times to retry on requests returning 503
    timeout=60.0, # time (in seconds) to wait for a response from the API
)


def chat(msgs, model='gpt-3.5-turbo-1106', stream=False):
    """
    Function to chat with the AI
    """
    # Remove all keys except for role and content
    msgs_copy = []
    for msg in msgs:
        msgs_copy.append({
            'role': msg['role'],
            'content': msg['content']
        })
    
    # Get AI response
    response = client.chat.completions.create(
        messages=msgs_copy,
        model=model,
        temperature=0.9,
        stream=stream
    )

    response_msg = ''
    if stream:
        for msg in response:
            if msg.choices:
                current_msg = msg.choices[0].delta.content or ""
                response_msg += current_msg
                print(current_msg, end='', flush=True) # Print the current message
        return response_msg
    else:
        return response.choices[0].message.content



# ==================================================================================================
# Helper Functions
# ==================================================================================================
def get_token_count(text):
    """
    Returns the number of tokens in the text using the GPT-4 tokenizer tiktoken
    """
    encoder = tiktoken.encoding_for_model("gpt-4")
    return len(encoder.encode(text))


def get_chat_history_token_count(chat_history):
    """
    Returns the number of tokens in the chat history using the GPT-4 tokenizer tiktoken
    """
    return sum([get_token_count(chat_msg['content']) for chat_msg in chat_history])


def print_line(char='-', num=50):
    """
    Prints a line of characters
    """
    print(char * num)


def print_help():
    """
    Prints the help menu
    """
    print_line('=')
    print('HELP MENU: ')
    print_line('-')
    print('q | quit: Quit the program')
    print('h | history: Show the chat history')
    print('d | delete: Delete the chat history')
    print('c | clear: Clear the terminal')
    print('y | youtube: Toggle youtube mode')


def print_chat_history(chat_history):
    """
    Prints the chat history
    """
    print_line('=')
    print('CHAT HISTORY: ')
    for chat_msg in chat_history:
        print(chat_msg['role'].upper() + ': ' + chat_msg['content'])
        # Print the context if there is any
        if 'context' in chat_msg and len(chat_msg['context']) > 0:
            print_line('-', 25)
            print('CONTEXT: ')
            for transcript_object in chat_msg['context']:
                print('\t- YouTube URL: ', transcript_object['url'])
                print('\t- Video Title: ', transcript_object['title'])
                # Calculate video duration
                start_time = transcript_object['transcript'][0]['start']
                duration = transcript_object['transcript'][-1]['start'] + transcript_object['transcript'][-1]['duration'] - start_time
                duration = round(duration, 2)  # Round to 2 decimal places
                print('\t- Video Duration: ', duration, ' seconds', ' - ', duration / 60, ' minutes')
                print('\t- Transcript Excerpt: ', ' '.join([part['text'] for part in transcript_object['transcript']])[0:250] + '...')
                # if not the last transcript object, print a line
                if transcript_object != chat_msg['context'][-1]:
                    print_line('-', 15)


def search_query_prompt(user_input):
    """
    Returns a prompt for the user to generate a search query
    """
    return {
        'role': 'user',
        'content': f"""
            Please generate a concise natural language search query for the following user input which would be used to search google:
            {user_input}

            Do not include any intro or exit text, only return only the natural language search query.
            Search Query:
        """
    }


def context_final_prompt(user_input):
    """
    Returns a prompt for the user to respond to the user input with the context provided
    """
    return {
        'role': 'user',
        'content': f"""
            Please respond to the following user input with the context provided:
            {user_input}

            Please cite the context in your response and provide inline citations with a source list at the bottom of your response.    
            Example inline citation: [1]
            Example source list: [1] https://www.youtube.com/watch?v=JWzDZ7wo0XQ "The History of the World: Every Year"
        """
    }


# ==================================================================================================
# Main Function
# ==================================================================================================
if __name__ == '__main__':
    """
    Main function
    """
    running = True
    youtube_on = True
    print('Welcome to the AI YouTube Chatbot!')
    print_help()
    while running:
        print_line('=')
        # Get user input
        user_input = input(f'You {"[Youtube On]" if youtube_on else "[Youtube Off]"}: ')
        # Check if user wants to quit
        if user_input.lower() == 'quit' or user_input.lower() == 'q':
            print('Goodbye!')
            running = False
            break
        # Check if user wants to print help menu
        elif user_input.lower() == 'help':
            print_help()
            continue
        # Check if user wants to show chat history
        elif user_input.lower() == 'history' or user_input.lower() == 'h':
            print_chat_history(chat_history)
            continue
        # Check if user wants to delete chat history
        elif user_input.lower() == 'delete' or user_input.lower() == 'd':
            print_line('=')
            print('CHAT HISTORY DELETED!')
            chat_history = []
            continue
        # Check if user wants to clear terminal
        elif user_input.lower() == 'clear' or user_input.lower() == 'c':
            os.system('cls' if os.name == 'nt' else 'clear')
            continue
        # Check if user wants to toggle youtube mode
        elif user_input.lower() == 'youtube' or user_input.lower() == 'y':
            youtube_on = not youtube_on
            print_line('=')
            print('YOUTUBE MODE: ', youtube_on)
            continue

        # Add user input to chat history
        chat_history.append({
            'role': 'user',
            'content': user_input
        })

        # Try and get some context from the user
        transcript_objects = []
        temp_chat_history = copy.deepcopy(chat_history)
        if youtube_on:
            print_line('-', 25)
            chat_history.append(search_query_prompt(user_input))
            search_query = chat(chat_history, 'gpt-3.5-turbo-1106')
            # Clean up the search query
            search_query = search_query.replace('\n', ' ').replace('\t', ' ').replace('  ', ' ').strip()
            # Remove quotes since they exclude results in google search
            search_query = search_query.replace('"', '')
            # pop the last chat history
            chat_history.pop()
            print('SEARCH QUERY: ', search_query)
            
            # Get the top 3 YouTube search results
            transcript_objects = get_youtube_search_results(search_query, 3) # [{url, transcript}] an array of objects     


            # Temporarily add the contexts to the chat history
            print('CONTEXT(s): ')
            for transcript_object in transcript_objects:
                print('- ', transcript_object['url'] + ' - ' + transcript_object['title'])
                temp_chat_history.append({
                    'role': 'assistant',
                    'content': f"""
                    CONTEXT
                    - YouTube URL: {transcript_object['url']}
                    - Video Title: {transcript_object['title']}
                    - Video Duration: {transcript_object['transcript'][-1]['start'] + transcript_object['transcript'][-1]['duration'] - transcript_object['transcript'][0]['start']} seconds
                    - YouTube Transcript:
                    {' '.join([part['text'] for part in transcript_object['transcript']])}
                    """
                })

        
            # Ask the AI to respond to the user with the context
            temp_chat_history.append(context_final_prompt(user_input))

        # Determine which model to use
        temp_chat_history_length = sum([len(chat_msg['content']) for chat_msg in temp_chat_history])
        model = 'gpt-4-1106-preview' if temp_chat_history_length > 50000 else 'gpt-3.5-turbo-1106' # 50K characters is about 10K words which is about 20 pages of text or 12k tokens

        # Get and print the AI response
        print_line('-', 25)
        print('AI: ', end='')
        ai_response = chat(temp_chat_history, model, True) 

        # Add AI response to chat history
        chat_history.append({
            'role': 'system',
            'content': ai_response,
            'context': transcript_objects
        })
        print()
        print_line('-', 5)
        print(f'Used model: {model} - {get_chat_history_token_count(temp_chat_history)} tokens')
    
