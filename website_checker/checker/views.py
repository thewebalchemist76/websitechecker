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
import io
import sys
from django.http import HttpResponse
import csv
from django.views.decorators.csrf import csrf_exempt

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
    # Prepare CSV data
    csv_data = io.StringIO()  # Create a StringIO object to hold CSV data
    fieldnames = ['Website', 'Status', 'Title', 'Description', 'Business Summary', 'Emails', 'Phones', 'Facebook', 'Instagram']

    # Use DictWriter to write the CSV data
    writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
    writer.writeheader()  # Write the header row

    for data in websites_data:
        # Create a new dictionary with the required fieldnames to avoid extra fields in the CSV
        row_data = {
            'Website': data['url'],
            'Status': data['status'],  # Use 'status' instead of 'is_down'
            'Title': data['title'],
            'Description': data['description'],
            'Business Summary': data['business_summary'],
            'Emails': ', '.join(data['emails']) if data['emails'] else 'No emails found',
            'Phones': ', '.join(data['phones']) if data['phones'] else 'No phones found',
            'Facebook': ', '.join(data['facebook_links']) if data['facebook_links'] else 'No Facebook links found',
            'Instagram': ', '.join(data['instagram_links']) if data['instagram_links'] else 'No Instagram links found',
        }

        # Write the data row
        writer.writerow(row_data)

    print("CSV Data:", csv_data.getvalue())  # Debugging line
    return csv_data.getvalue()


@csrf_exempt
def home(request):
    if request.method == 'POST':
        website_urls = request.POST.get('website_urls', '').strip()
        urls_list = website_urls.splitlines()
        urls_list = list(filter(None, urls_list))

        print("Request Method:", request.method)  # Debugging line
        print("Website URLs:", urls_list)  # Debugging line

        websites_data = []
        for url in urls_list:
            try:
                response = requests.get(url)
                is_down = response.status_code != 200
                soup = BeautifulSoup(response.content, 'html.parser')

                if soup:
                    title = soup.title
                    if title:
                        title = title.string.strip() if title.string else 'No title available'
                    else:
                        title = 'No title available'

                    description_tag = soup.find('meta', attrs={'name': 'description'})
                    description = description_tag['content'].strip() if description_tag else 'No description available'

                    website_text = soup.get_text()

                    business_summary = get_business_summary(website_text)

                    emails = extract_emails(website_text)

                    phones = extract_phones(website_text)

                    facebook_links, instagram_links = extract_social_media_links(soup)
                    facebook_links = list(set(facebook_links))
                    instagram_links = list(set(instagram_links))
                else:
                    is_down = True
                    title = 'No title available'
                    description = 'No description available'
                    business_summary = 'Unable to retrieve website content.'
                    emails = []
                    phones = []
                    facebook_links = []
                    instagram_links = []

            except requests.exceptions.RequestException:
                is_down = True
                title = 'No title available'
                description = 'No description available'
                business_summary = 'Unable to retrieve website content.'
                emails = []
                phones = []
                facebook_links = []
                instagram_links = []
                pass

            status = 'UP' if not is_down else 'Down'
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
                'status': status,
            })
        # Save websites_data in the session, regardless of which button was clicked
        request.session['websites_data'] = websites_data
        print("Session data in home view: ", request.session['websites_data'])  # Print session data

        # Check if the request is for CSV download
        if 'download_csv' in request.POST:
            # Generate the URL for the download view using reverse
            download_url = reverse('download_csv')
            # Redirect to the download view
            return HttpResponseRedirect(download_url)

        # For normal POST request, render the result table
        print("Websites Data:", websites_data)  # Debugging line
        return render(request, 'checker/home.html', {'websites_data': websites_data})
    # For GET request, display the form to enter website URLs
    return render(request, 'checker/home.html')

def download_csv(request):
    if request.method == 'POST':
        websites_data = request.session.get('websites_data', None)
        print("Session data in download_csv view: ", websites_data)  # Print session data
        if websites_data is None:
            return HttpResponse("No data to download.")
        else:
            csv_file = io.StringIO()
            writer = csv.writer(csv_file)
            writer.writerow(['Website', 'Status', 'Title', 'Description', 'Business Summary', 'Emails', 'Phones', 'Facebook', 'Instagram'])
            for data in websites_data:
                writer.writerow([data['url'], data['status'], data['title'], data['description'], data['business_summary'], ', '.join(data['emails']), ', '.join(data['phones']), ', '.join(data['facebook_links']), ', '.join(data['instagram_links'])])
            csv_file.seek(0)
            response = HttpResponse(csv_file, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=websites_data.csv'
            return response
    else:
        return HttpResponse("Invalid request method for CSV download.")
