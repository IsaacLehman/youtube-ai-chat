# AI YouTube Chatbot

This is a Python-based CLI chatbot that uses OpenAI's API to chat with the user. It also can use YouTube transcripts to provide additional context to the chat.

## Features

- Chat with the user using OpenAI's API
- Use YouTube transcripts to provide relevant context
  - searches Google Search to pick the most relevant videos
- Web scraping capabilities
- Google search functionality

## Usage

1. Ensure you replace the `OPEN_AI_API_KEY` with your own OpenAI API key.
2. You can run the program using the following command:

```bash
python youtube.py
```

## CLI Commands

- `q | quit`: Quit the program
- `h | history`: Show the chat history
- `d | delete`: Delete the chat history
- `c | clear`: Clear the terminal
- `y | youtube`: Toggle youtube mode

## Dependencies

- `openai`: For interacting with OpenAI's API
- `beautifulsoup4`: For web scraping
- `requests`: For making HTTP requests
- `urllib`: For URL encoding and decoding
- `re`: For regular expressions
- `copy`: For creating copies of mutable objects
- `os`: For interacting with the operating system

## Author

- Isaac Lehman

## Date

- 2023-12-30

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
