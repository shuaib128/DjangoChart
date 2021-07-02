from django.shortcuts import render
import json
import pandas as pd
from django.shortcuts import render, redirect
from .models import Data
from pathlib import Path
import os
from django.http import JsonResponse
import numpy as np
import glob
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test


# Imports for the scrapers
from collections import Counter
from selenium import webdriver
import time
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path
from selenium.webdriver.chrome.options import Options
from datetime import date, timedelta, datetime
import re
import csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
def check_admin(user):
   return user.is_superuser


# Create your views here.
def home(request):
    country = request.GET.get('country')

    csvs = Data.objects.get(country_name=country)
    df = pd.read_csv(csvs.csv_file.path)
    dates = df.columns.to_list()
    cases = []
    for i in dates:    
        cases.append(int(df[i][0]))

    context = {
        'dates': dates,
        'cases': cases,
        'country': country
    }
    return render(request, 'index.html', context)



# Update Database
@user_passes_test(check_admin)
def update_data_base(request):
    Data.objects.all().delete()
    file = f"{BASE_DIR}\media\country_csvs"
    
    for file in os.listdir(file):
        file = file.split('.')[0]
        Data.objects.create(
            country_name = file,
            csv_file = f"country_csvs/{file}.csv"
        )

    return JsonResponse("Data Base Updated", safe=False)



@user_passes_test(check_admin)
def get_database_data(request):
    file = f"{BASE_DIR}\media\country_csvs"
    for file in os.listdir(file):
        os.remove(f"{BASE_DIR}\media\country_csvs\{file}")
    # Path for chromedriver
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)


    # Default values
    y_axes_numbers_str = []
    y_axes_numbers_nums_2d = []
    rel_height = 0
    y_axes_height = 0
    num_scale = 0
    daily_datas = []
    country_based_urls = []


    # Getting the website
    driver.get("https://www.worldometers.info/coronavirus/")
    time.sleep(2)
    country_elements = driver.find_elements_by_css_selector(".mt_a")
    countrys = []
    countrys_url = []
    country_based_urls = []


    # Get country and append it in countrys list
    for country in country_elements:
        countrys.append(country.text)

    countrys = [x for x in countrys if x]
    del countrys[0]

    for url in countrys:
        j = url.lower().replace(" ", "-")
        countrys_url.append(j)

    for county in countrys_url:
        country_based_urls.append(f"https://www.worldometers.info/coronavirus/country/{county}")


    for iteration, url in enumerate(country_based_urls):
        try:
            y_axes_numbers_str = []
            y_axes_numbers_nums_2d = []
            rel_height = 0
            y_axes_height = 0
            num_scale = 0
            daily_datas = []
            # Getting the website
            driver.get(url)
            time.sleep(3)
            html = driver.find_elements_by_css_selector(".col-md-12 h3")
            time.sleep(2)

            # Get the y axces text to comare
            for i in html:
                if i.get_attribute("innerHTML") == f"Daily New Cases in {countrys[iteration]}":
                    main_colum = i.find_element_by_xpath('..')
                    axes_colum = main_colum.find_element_by_css_selector(".highcharts-yaxis-labels")
                    height = main_colum.find_element_by_css_selector("rect.highcharts-plot-background").get_attribute("height")
                    rel_height = int(height)
                    daily_data = main_colum.find_elements_by_css_selector(".highcharts-point")
                    asex_element = axes_colum.find_elements_by_tag_name("text")
                    
                    for x in asex_element:
                        y_axes_numbers_str.append(x.text)

                    for data in daily_data:
                        x_height = data.get_attribute("height")
                        daily_datas.append(x_height)

            # Get all str out of the list
            for y_axes in y_axes_numbers_str:
                x = re.findall('[0-9]+', y_axes)
                y_axes_numbers_nums_2d.append(x)

            # Convert to 1d array
            y_axes_numbers_nums = sum(y_axes_numbers_nums_2d, [])
            # Convert to int full of array
            y_axes_numbers_nums = [int(x) for x in y_axes_numbers_nums]
            # Cut last two None values
            daily_datas = [int(x) for x in daily_datas[:-2]]

            y_axes_height = max(y_axes_numbers_nums)
            y_axes_height = str(y_axes_height)+"000"
            y_axes_height = int(y_axes_height)
            num_scale = y_axes_height / rel_height

            multiplied_height_list = [height * num_scale for height in daily_datas]
            multiplied_height_list = [round(x) for x in multiplied_height_list]


            # Get the dates
            sdate = date(2020, 2, 16) # start date
            time_string = datetime.today().strftime('%Y-%m-%d')
            edate = datetime.fromisoformat(time_string).date() # end date
            delta = edate - sdate # as timedelta
            days = []

            for i in range(delta.days + 1):
                day = sdate + timedelta(days=i)
                day = str(day)
                days.append(day)

            if len(days) != len(multiplied_height_list):
                empty_keys = int(len(days) - len(multiplied_height_list))

                for i in range(0, empty_keys):
                    multiplied_height_list.insert(i, 0)

            dictionary = dict(zip(days, multiplied_height_list))
            # for key, value in dictionary.items():
            #     print(key, ' : ', value)
            dic_dicsonary = [dictionary]

            with open(f'{BASE_DIR}\media\country_csvs\{countrys[iteration]}.csv', 'w') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames = days)
                writer.writeheader()
                for data in dic_dicsonary:
                    writer.writerow(data)


        except Exception:
            y_axes_numbers_str = []
            y_axes_numbers_nums_2d = []
            rel_height = 0
            y_axes_height = 0
            num_scale = 0
            daily_datas = []
            pass

    return JsonResponse("Data Was Collected", safe=False)