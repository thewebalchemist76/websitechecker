# website_checker/checker/views.py

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.shortcuts import render, HttpResponse
from django.urls import reverse
import requests
from bs4 import BeautifulSoup
from .utils import get_business_summary, extract_emails, extract_phones, extract_social_media_links
import spacy
import re
import csv


# Function to get a business summary from the text
def get_business_summary(text):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    business_summary = ''
    for sent in sentences:
        # You can add more conditions to extract business-specific information from the text
        if 'business' in sent.lower() or 'company' in sent.lower():
            business_summary = sent
            break
    return business_summary



# Function to extract emails from the text
def extract_emails(text):
    # Use regex pattern for email extraction
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = set(re.findall(email_pattern, text))  # Use set to eliminate duplicates
    return list(emails)

# Function to extract phone numbers from the text
def extract_phones(text):
    phone_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?(\()?\d{3}(\))?[-.\s]?\d{3}[-.\s]?\d{4}')

    phones = set()
    for match in phone_pattern.finditer(text):
        phone = match.group(0).replace('(', '').replace(')', '').replace('-', '').replace(' ', '').replace('.', '')
        phones.add(phone)

    return list(phones) if phones else ['No phones found']

# Function to extract Facebook and Instagram links from the website
def extract_social_media_links(soup):
    facebook_links = []
    instagram_links = []

    # Find all anchor tags with href attributes
    anchor_tags = soup.find_all('a', href=True)

    for tag in anchor_tags:
        href = tag['href']
        if 'facebook.com' in href:
            facebook_links.append(href)
        elif 'instagram.com' in href:
            instagram_links.append(href)

    # Return the links as lists
    return facebook_links, instagram_links

# Actual implementation of generate_csv function to convert websites_data into CSV format
def generate_csv(websites_data):
    # Create a list to hold the CSV rows
    csv_data = []

    # Add the header row to the CSV
    csv_data.append(
        ['Website', 'Status', 'Title', 'Description', 'Business Summary', 'Emails', 'Phones', 'Facebook', 'Instagram']
    )

    # Loop through the websites_data list
    for data in websites_data:
        # Extract values for each column from the dictionary
        url = data.get('url', '')
        is_down = data.get('is_down', False)
        title = data.get('title', '')
        description = data.get('description', '')
        business_summary = data.get('business_summary', '')
        emails = ', '.join(data.get('emails', []))
        phones = ', '.join(data.get('phones', []))
        facebook_links = ', '.join(data.get('facebook_links', []))
        instagram_links = ', '.join(data.get('instagram_links', []))

        # Create a row for the CSV
        row = [url, is_down, title, description, business_summary, emails, phones, facebook_links, instagram_links]

        # Append the row to csv_data
        csv_data.append(row)

    return csv_data

def download_csv(request):
    if request.method == 'POST':
        websites_data = request.session.get('websites_data')
        if websites_data:
            # Prepare CSV data
            csv_data = generate_csv(websites_data)

            # Create and return the CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="websites_data.csv"'

            # Create the CSV writer using response as the output file
            writer = csv.writer(response, lineterminator='\n')  # Use lineterminator='\n'

            # Write the rows to the CSV
            writer.writerows(csv_data)

            return response
        else:
            return HttpResponse("No data to download.")
    else:
        return HttpResponse("Invalid request method for CSV download.")




# Combine the check_websites logic with the home view function
def home(request):
    if request.method == 'POST':
        website_urls = request.POST.get('website_urls', '').strip()
        urls_list = website_urls.split('\n')
        # Remove empty strings from the list
        urls_list = list(filter(None, urls_list))

        print("Request Method:", request.method)  # Debugging line
        print("Website URLs:", urls_list)  # Debugging line

        websites_data = []
        for url in urls_list:
            try:
                response = requests.get(url)
                is_down = response.status_code != 200
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.title.string.strip() if soup.title else 'No title available'
                description = soup.find('meta', attrs={'name': 'description'})
                description = description['content'].strip() if description else 'No description available'

                # Get the website content for NLP processing
                website_text = soup.get_text()

                # Get a brief business summary
                business_summary = get_business_summary(website_text)

                # Extract emails using regex pattern
                emails = extract_emails(website_text)

                # Extract phone numbers using regex pattern
                phones = extract_phones(website_text)

                # Extract Facebook and Instagram links from the website
                facebook_links, instagram_links = extract_social_media_links(soup)

            except requests.exceptions.RequestException:
                is_down = True
                title = 'No title available'
                description = 'No description available'
                business_summary = 'Unable to retrieve website content.'
                emails = []
                phones = []
                facebook_links = []
                instagram_links = []

            websites_data.append({
                'url': url,
                'is_down': is_down,
                'title': title,
                'description': description,
                'business_summary': business_summary,
                'emails': emails,
                'phones': phones,
                'facebook_links': facebook_links,
                'instagram_links': instagram_links,
            })

        # Check if the request is for CSV download
        if request.POST.get('download_csv'):
            print("Session Data:", request.session.get('websites_data'))  # Debugging line

            # Save websites_data in the session
            request.session['websites_data'] = websites_data
            # Generate the URL for the download view using reverse
            download_url = reverse('download_csv')
            # Redirect to the download view
            return HttpResponseRedirect(download_url)

        # For normal POST request, render the result table
        print("Websites Data:", websites_data)  # Debugging line
        return render(request, 'checker/home.html', {'websites_data': websites_data})

    # For GET request, display the form to enter website URLs
    return render(request, 'checker/home.html')