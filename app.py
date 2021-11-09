from flask import Flask, render_template
import requests
import json
import iso8601
import calendar
import urllib3
import matplotlib.pyplot as plt

# Feel free to import additional libraries if you like

app = Flask(__name__, static_url_path='/static')

urllib3.disable_warnings()

# Paste the API-key you have received as the value for "x-api-key"
headers = {
        "Content-Type": "application/json",
        "Accept": "application/hal+json",
        "x-api-key": "860393E332148661C34F8579297ACB000E15F770AC4BD945D5FD745867F590061CAE9599A99075210572"
}


# Example of function for REST API call to get data from Lime
def get_api_data(headers, url):
    # First call to get first data page from the API
    response = requests.get(url=url,
                            headers=headers,
                            data=None,
                            verify=False)

    # Convert response string into json data and get embedded limeobjects
    json_data = json.loads(response.text)
    limeobjects = json_data.get("_embedded").get("limeobjects")

    # Check for more data pages and get thoose too
    nextpage = json_data.get("_links").get("next")
    while nextpage is not None:
        url = nextpage["href"]
        response = requests.get(url=url,
                                headers=headers,
                                data=None,
                                verify=False)

        json_data = json.loads(response.text)
        limeobjects += json_data.get("_embedded").get("limeobjects")
        nextpage = json_data.get("_links").get("next")

    return limeobjects


# Index page
@app.route('/')
def index():
    #data = get_api_data(headers=headers, url=)
    return render_template('home.html')


# Example page
@app.route('/example')
def example():

    # Example of API call to get deals
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
    #https://api-test.lime-crm.com/client/table-view/deal
    params = "?probability=1.0&min-closeddate=2020-11-08T23:59Z&max-closeddate=2021-11-08T23:59Z"
    url = base_url + params
    response_deals = get_api_data(headers=headers, url=url)
    response_all = get_api_data(headers=headers, url=base_url)

    def averageValue():
        totalvalue = 0
        for d in response_deals:
            totalvalue += d["value"]

        return totalvalue/len(response_deals)

    #print(averageValue())

    def dealsPerMonth():
        monthDict = dict.fromkeys(calendar.month_name[1:13], 0)
        for d in response_deals:
            month_nr = iso8601.parse_date(d["closeddate"]).month
            month = calendar.month_name[month_nr]
            monthDict[month] += 1

        return monthDict

    def getIDs(response):
        companyIDs = []
        for d in response:
            companyIDs.append(d["company"])
        return companyIDs

    def getAllCompanyNames():
        companyIDs = getIDs(response_all)
        IDNameDict = {}
        for companyID in companyIDs:
            first = next(x for x in response_all if x["company"] == companyID)
            company_url = first["_links"]["relation_company"]["href"]
            print(company_url)
            response_company = requests.get(headers=headers, url=company_url, data=None, verify=False)
            json_data = json.loads(response_company.text)
            company_name = json_data.get("name")
            IDNameDict[companyID] = company_name

        return IDNameDict

    def getSpecificNames(response):
        companyNames = []
        for n in getIDs(response):
            companyNames.append(IDNameDict[id])

        return companyNames

    #Skapa en dictionary för alla företag/customers mha company id.
    #Skapar inte en dictionary för namnen för det tar för mkt tid o köra request på alla 22 (istället för 12, inga duplicates).

    IDNameDict = getAllCompanyNames()

    def valuePerCustomer():
        compValueDict = {}
        for d in response_deals:
            companyID = d["company"]
            if d["company"] in compValueDict:
                compValueDict[companyID] += d["value"]
            else:
                compValueDict[companyID] = d["value"]

        for id in compValueDict:
            compValueDict[IDNameDict[id]] = compValueDict.pop(id)

        return compValueDict

    print(valuePerCustomer())
    #takes a dictionary of companies and uses the keys to find the company names based on the company id.

    def getCustomers():
        return valuePerCustomer().keys()

    boughtThePastYear = getCustomers()


    def getInactive():
        base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
        params = "?probability=1.0&max-closeddate=2020-11-08T23:59Z"
        before2020URL = base_url + params
        data_until_2020 = get_api_data(headers=headers, url=before2020URL)
        inactiveNames = getSpecificNames(data_until_2020)
        inactiveCompanies = set(inactiveNames) - set(boughtThePastYear)
        return inactiveCompanies

    def getProspects():
        base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
        params = "?not-probability=1.0"
        noDealsURL = base_url + params
        no_deals_data = get_api_data(headers=headers, url=noDealsURL)
        prospectNames = getSpecificNames(no_deals_data)
        prospectCompanies = set(prospectNames) - set(boughtThePastYear)
        return prospectCompanies


#skulle kunna ta ner alla namn.

    #print(averageValue())
    #print(dealsPerMonth())
    #print(valuePerCustomer())
    #print(boughtThePastYear)
    #print(getProspects())
    print(getInactive())

    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1)

    dealsPerMonth = dealsPerMonth()
    ax1.bar(dealsPerMonth.keys(), dealsPerMonth.values())
    ax1.set_title("Deals Per Month")
    ax1.set_ylabel("Number of deals")
    ax1.set_xlabel("Month")

    perCustomer = valuePerCustomer()
    ax2.bar(perCustomer.keys(), perCustomer.values())
    ax2.set_title("Value Per Customer")
    ax2.set_ylabel("Value in kr")
    ax2.set_xlabel("Company")

    fig.savefig("dealsandvalue.png")


#customer o månad map,

    """
    [YOUR CODE HERE]
    In this exmaple, this is where you can do something with the data in
    'response_deals' before you return it below.
    """

    if len(response_deals) > 0:
        return render_template('example.html', response=response_deals, averageValue=averageValue(), prospects=getProspects(),
                               customers=getCustomers(), inactives=getInactive())
    else:
        msg = 'No deals found'
        return render_template('example.html', msg=msg)



# You can add more pages to your app, like this:
@app.route('/myroute')
def myroute():
    mydata = [{'name': 'apple'}, {'name': 'mango'}, {'name': 'banana'}]
    """
    For mytemplate.html to rendered you have to create the mytemplate.html
    page inside the templates-folder. And then add a link to your page in the
    _navbar.html-file, located in templates/includes/
    """
    return render_template('mytemplate.html', items=mydata)


# DEBUGGING
"""
If you want to debug your app, one of the ways you can do that is to use:
import pdb; pdb.set_trace()
Add that line of code anywhere, and it will act as a breakpoint and halt
your application
"""

if __name__ == '__main__':
    app.secret_key = 'somethingsecret'
    app.run(debug=True)
