"""
Setup Required:
We need to install the dependencies to the project.
Using Terminal: pip install openai              - OpenAI API dependencies
                pip install fastapi uvicorn     - Web dependencies
                pip install aiofiles jinja2     - UI dependencies
                pip install websockets          - WebSockets dependencies
                pip install python-dotenv       - Environment Variable dependencies (.env)
                pip3 freeze > requirements.txt  - Generate requirements.txt

Calling the program:
Using Terminal: uvicorn main_webV3:app --reload
                --reload means reload the app whenever changes are made
                url: http://127.0.0.1:8000/
"""

from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv

load_dotenv()

# Get the OpenAI API KEY environment variable (.env)
openai = OpenAI(
    api_key=os.getenv("OPENAI_API_SECRET_KEY")
)

# Global Variables
app = FastAPI()
templates = Jinja2Templates(directory="pageTemplates")
chat_responses = []


chat_log = [{"role":"system", "content": "You are a Python tutor AI"}]


# +----------------------------------------------------------------------
# | Chatbot WebSocket Prompt Endpoint
# +----------------------------------------------------------------------
@app.websocket("/ws")
async def chat(websocket: WebSocket):

    # Establish connection between server and client
    await websocket.accept()

    # Keep the connection active while True
    while True:
        user_input = await websocket.receive_text()     # Wait for User Input

        chat_log.append({"role": "user", "content": user_input})    # Chat Log provides communication context
        chat_responses.append(user_input)

        try:
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=chat_log,
                temperature=0.6,
                stream=True         # openAI API will stream response instead of one final response
            )

            ai_response = ""

            # Handle real-time streaming of the response
            for chunk in response:      # each portion of the stream is a chunk
                if chunk.choices[0].delta.content is not None:
                    ai_response += chunk.choices[0].delta.content
                    await websocket.send_text(chunk.choices[0].delta.content)       # Return response

            chat_responses.append(ai_response)

        except Exception as e:
            await websocket.send_text(f'Error:  {str(e)}')
            break       # End WebSocket connection


# +----------------------------------------------------------------------
# | Chatbot Prompt Endpoint
# +----------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})


# +----------------------------------------------------------------------
# | Chatbot Response
# +----------------------------------------------------------------------
@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):

    chat_log.append({"role": "user", "content": user_input})
    chat_responses.append(user_input)

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=chat_log,
        temperature=0.6
    )

    bot_response = response.choices[0].message.content
    chat_log.append({"role": "assistant", "content": bot_response})
    chat_responses.append(bot_response)

    # Send the response message content
    return templates.TemplateResponse("home.html", {"request":request,"chat_responses":chat_responses})


# +----------------------------------------------------------------------
# | Image Generator Prompt Endpoint
# +----------------------------------------------------------------------
@app.get("/image", response_class=HTMLResponse)
async def image_page(request: Request):
    return templates.TemplateResponse("image.html", {"request": request})


# +----------------------------------------------------------------------
# | Image Generator Response
# +----------------------------------------------------------------------
@app.post("/image",response_class=HTMLResponse)
async def create_image(request: Request, user_input: Annotated[str, Form()]):

    response = openai.images.generate(
        prompt=user_input,
        n=1,
        size="256x256"
    )

    image_url = response.data[0].url
    # print(image_url)
    return templates.TemplateResponse("image.html", {"request": request, "image_url": image_url})