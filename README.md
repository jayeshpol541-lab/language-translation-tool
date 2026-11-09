# Language Translation Tool

A full-stack internship project using Python, Flask, HTML, CSS, JavaScript, SQLite and the MyMemory Translation API.

## Features
- Select source and target languages
- Translate text through a backend API
- Swap languages, clear input and copy results
- Browser text-to-speech
- Save and display the latest 20 translations in SQLite
- Responsive desktop and mobile interface
- Basic input validation and API error handling

## Requirements
- Python 3.9 or later
- Internet connection
- VS Code (recommended)

## Run on Windows (PowerShell)

1. Extract the ZIP file and open the project folder in VS Code.
2. Open the VS Code terminal.
3. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

4. Activate it:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt:

   ```cmd
   .venv\Scripts\activate.bat
   ```

5. Install packages:

   ```powershell
   python -m pip install -r requirements.txt
   ```

6. Start the application:

   ```powershell
   python app.py
   ```

7. Open this address in your browser:

   http://127.0.0.1:5000

The SQLite database is created automatically when the app starts.

## API routes
- `GET /` — application interface
- `POST /api/translate` — translate text; JSON body: `{"text":"Hello","source":"en","target":"hi"}`
- `GET /api/history` — retrieve the latest 20 translations
- `DELETE /api/history` — clear all saved history
- `DELETE /api/history/<id>` — delete one history item
- `GET /health` — application health check

## Translation service note
This starter uses the public MyMemory translation endpoint. Its documented request parameter supports up to 500 bytes per segment. Anonymous use is limited to 5,000 characters per day; a contact email can raise the daily allowance subject to the provider's terms. Public services can be rate-limited or temporarily unavailable. For a production deployment, review the provider's current terms and consider a paid translation provider. Do not expose API keys in frontend JavaScript.

## Important
Run locally with `python app.py`. Flask debug mode is enabled for development only. Turn debug mode off before deploying publicly. Do not submit real private or sensitive text to a public translation service.
