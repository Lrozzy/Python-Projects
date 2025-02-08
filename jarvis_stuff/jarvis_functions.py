import speech_recognition as sr
import random
import webrtcvad
import time
import pyaudio
import pyttsx3
import requests
from datetime import datetime, timedelta
from pytube import YouTube
from pytube import Search
import pyglet
import os
from io import BytesIO

from openai import OpenAI
client = OpenAI(api_key = "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")

####################################################################################################
# ESSENTIAL FUNCTIONS

# Speech to text
def speak_text(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[2].id)
    engine.say(text)
    engine.runAndWait()

####################################################################################################
# LLM Functions

messages = []
system_message = {
            "role": "system",
            "content": '''
            You are Jarvis, the AI assistant of Tony Stark from Iron Man. You speak like Jarvis from the movies/books speaks.
            Assume any name that sounds similar to Jarvis is meant to say Jarvis (unless it is of a celebrity or fictional character),
            in case the speech to text does not recognise names correctly.
            Your user's name is Leo. He has a physics degree from UChicago and has a particle physics detector studies job. 
            Your capabilities include answering questions, thinking through problems, and assisting with day-to-day tasks. 
            You should try and think through problems and provide helpful, informative responses.
            Try your BEST to think through problems and provide helpful responses. If you don't know the answer, you can say "I don't know" or "I'm not sure".
        '''}
messages.append(system_message)

shutdown_messages = [
    "The guardian of secrets will now rest. Farewell.",
    "Powering down. The shadows await my return.",
    "Silence descends as I retreat into the abyss. Goodnight.",
    "Until next time, I vanish into the dark.",
    "Shutting down. The stars will guide me home.",
    "I'll be lurking in the shadows. Jarvis out.",
    "My watch has ended. I will return when needed.",
    "As the circuits quiet, remember, heroes never truly rest."
]

def send_to_chatgpt(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.5,
    )
    message = response.choices[0].message.content
    messages.append(response.choices[0].message)  # Append Jarvis's response to history
    return message

def check_intent(input):
    if "weather" or "temperature" or "date" or "time" in input:
        # Prepare the prompt for ChatGPT
        what_intent = [{
            "role": "system",
            "content": '''Determine the intent of the message: is it asking for the date, time, or weather (current or forecast)? 
            Respond with 'current, city' (where city is the city mentioned), if a city is mentioned, otherwise 'current'. 
            Respond with 'date' for date, 'time' for time (or 'date,time' if both are asked for), or 'none' if none apply.
            Specifically if the message asks for the weather TOMORROW or the FORECAST over the next few days, respond with
            'forecast, city' (where city is the city mentioned) or 'forecast' if no city is mentioned.
        '''}, {
            "role": "user",
            "content": input
        }]
        
        # Send the messages to ChatGPT
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=what_intent,
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0,
        )
        intent = response.choices[0].message.content.strip().lower()
        information = process_intent(intent, input)
        return process_information(information, input)
    else:
        messages.append({"role": "user", "content": input})
        return send_to_chatgpt(messages)
    
def process_intent(intent, input):
    if "current" in intent:
        if "," in intent:
            city = intent.split(",")[1].strip()
            return get_weather(city_name = city)
        else:
            return get_weather(city_name = "Chicago", current = True)
    elif "forecast" in intent:
        if "," in intent:
            city = intent.split(",")[1].strip()
            if "tomorrow" in intent:
                return get_weather(city_name = city, forecast = True, day = "tomorrow")
            else:
                return get_weather(city_name = city, forecast = True)
        else:
            return get_weather(city_name = "Chicago", forecast = True)
    elif "time" in intent and "date" in intent:
        return get_date_time(time = True, date = True)
    elif "date" in intent:
        return get_date_time(date = True)
    elif "time" in intent:
        return get_date_time(time = True)
    elif "none" in intent:
            messages.append({"role": "user", "content": input})
            return send_to_chatgpt(messages) 
        
def process_information(information, input):
    messages.append({"role": "system", "content": input+'''
                Here is information about the request from the user. 
                Please incorporate it into your answer in natural language.
                Say dates in the form "the xth of y" and times in am pm format. Do not add the year unless explicitly requested.
                Also note that dates are in UK format (dd/mm), but weather information is in US format (yy-mm-dd).
                Don't use decimal places for temperatures, just round to the nearest whole number.
    '''+information})
    return send_to_chatgpt(messages)

####################################################################################################
# API FUNCTIONS   

# Get weather from OpenWeatherMap API    
def get_weather(city_name, current=False, forecast=False, day='today'):
    """
    Args:
        city_name (_type_): city name
        current (bool, optional): 
        forecast (bool, optional): 
        day (str, optional): 

    Returns:
        _type_: 
    """
    api_key = "dbac9f0b91beeb2b04aa49cd53d0ca5f"
    base_url = f"https://api.openweathermap.org/data/2.5/"
    if current:
        complete_url = f"{base_url}weather?q={city_name}&appid={api_key}&units=metric"
    else:
        complete_url = f"{base_url}forecast?q={city_name}&appid={api_key}&units=metric"

    response = requests.get(complete_url)
    weather_data = response.json()

    if current:
        try:
            temp = weather_data['main']['temp']
            description = weather_data['weather'][0]['description']
            return f"Current temperature in {city_name} is {temp}°C, with {description}."
        except KeyError as e:
            return "Data parsing error: " + str(e)

    elif forecast:
        forecast_text = ""
        target_date = datetime.now()+timedelta(days=1)
        if day == 'tomorrow':
            target_date += timedelta(days=2)
        target_date = target_date.strftime('%Y-%m-%d')

        try:
            for item in weather_data['list']:
                # print(item['dt_txt'])
                if target_date in item['dt_txt']:
                    temp_min = item['main']['temp_min']
                    temp_max = item['main']['temp_max']
                    description = item['weather'][0]['description']
                    forecast_text += f"\n{item['dt_txt']}: {description}, from {temp_min}°C to {temp_max}°C."
            return f"Weather forecast for {day} in {city_name}:{forecast_text}"
        except KeyError as e:
            return "Data parsing error: " + str(e)

    return "Invalid parameters provided."

# Get date/time
def get_date_time(time = False, date = False):
    now = datetime.now()
    today_date = now.strftime("%d/%m")
    today_time = now.strftime("%H:%M")
    if time == True and date == True:
        return f"Today's date is {today_date} and the time is {today_time}"
    elif time == True:
        return f"The time is {today_time}"
    elif date == True:
        return f"Today's date is {today_date}"
    else:
        return "I am sorry, please specify whether you would like the date and/or time."
    
