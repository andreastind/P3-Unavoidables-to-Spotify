import requests
from bs4 import BeautifulSoup
from os.path import exists


def get_soup(stored_soup=False, decade=2020):
    '''Scrapes the content tag from Andreas Graulund's website. 
    
    Credit goes to Andreas Graulund for maintaining and allowing me to do 
    weekly scraping of his website.
    
    Arguments:
        stored_soup: whether we should use a locally stored version of the page
    
    Returns:
        res: the content tag of the scraped site as html
    '''

    url = f"https://andyg.dk/p3trends/unavoidables/{decade}"

    # to minimize calls to his website, we store the soup when testing
    if stored_soup:
        if not exists("data/local_page.html"):
            print("local_page.html not found, fetching from website.")
            page = requests.get(url)
            with open("data/local_page.html", "wb") as f:
                f.write(page.content)    

    # when not testing, we scrape
    else:
        page = requests.get(url)
        with open("data/local_page.html", "wb") as f:
            f.write(page.content)    

    # save html file locally for later use
    with open("data/local_page.html") as f:
        page_content = f.read()

    # parse and find content (where the track info is)
    soup = BeautifulSoup(page_content, "html.parser")
    res  = soup.find(id="content")

    return res


def scrape_cleaning(res):
    '''Finds relevant data (week number, track info, time stamp) within the 
    content tag given as input. The relevant tags are cleaned and returned as a
    tuple.
    
    Arguments:
        res: the content tag from Andreas Graulund's website 
    
    Returns:
        weekly: tuple of cleaned, scraped data, length of tuples is equal to 
            total number of tracks
    '''
    
    # find table head
    week_info_head = res.find_all("th", class_="week-info")
    
    # week structure was changed after 948 weeks, why we handle differently
    week_info_body1 = [x.find("a").text.strip().replace(u"\xa0", u" ") 
                       for x in week_info_head[:-948]]
    week_info_body2 = [x.text.strip().replace(u"\xa0", u" ") 
                       for x in week_info_head[-948:]]

    # concatenating the splits
    week_info_body = week_info_body1 + week_info_body2

    # padding week numbers to two digits
    week_info_body = [" ".join([y.rjust(2, "0") for y in x.split()]) 
                      for x in week_info_body]
    
    # finding wide and narrow time stamps
    time_wide = res.find_all("span", class_="time--wide")
    time_narrow = res.find_all("span", class_="time--narrow")

    # removing nonrelevant time stamps and cleaning them
    # excludes combination of side and secondary classes
    time_wide_list = [x.text.strip() for x in time_wide if \
        (x.parent.parent.has_attr("class") 
         and x.parent.parent["class"][-1] == "side") or 
        (x.parent.has_attr("class")
         and x.parent["class"][-1] == "side")
        ]

    time_narrow_list = [x.text.strip() for x in time_narrow if \
        (x.parent.parent.has_attr("class") 
         and x.parent.parent["class"][-1] == "side") or 
        (x.parent.has_attr("class") 
         and x.parent["class"][-1] == "side")
        ]

    # find main tags (where track title and artists are located)
    main = res.find_all("td", class_="main")
    
    # combine week, time, and main data into a tuple
    weekly = (week_info_body, time_wide_list, time_narrow_list, main)
    return weekly


if __name__ == '__main__':
    res = get_soup()
    weekly = scrape_cleaning(res)
    print("Successfully scraped {} tracks from P3 Trends!".format(len(weekly[0])))
    