"""This module contains all the functionality for gathering, filtering
and returning COVID news articles.
"""
import json
import sched
import time
import requests
import logging

# Configures the base logging level and log file to be used for this module.
logging.basicConfig(filename='sys.log', level=logging.DEBUG)

# Initialises the scheduler and allows it to be used.
news_scheduler = sched.scheduler(time.time, time.sleep)

# Stores the titles of all removed articles, to ensure they aren't displayed
# Again after being removed.
removed_article_titles = []

# Stores dictionaries of all covid news articles, making it easier to schdule.
# And remove updates to the news.
covid_news = []

# Contains data on all items in the scheduler queue, allowing articles to be.
# Removed from the scheduler queue.
news_queue_info = []


def get_config_data(func_name: str, config_file_name: str = "config.json")\
        -> tuple[str, str, str, str] | str | tuple[str, str]:
    """Extracts the data pertaining to the covid_news_handling module from the
    provided config file.

    A try except is used to get the encoding style to be used, and to check if
    a valid/present config file has been provided. If one hasn't been provided
    the event is logged and the dashboard is shutdown. Otherwise, the encoding
    style is extracted (data loaded as a json and the value of the 'encoding'
    key is found). The config file is opened again with the required encoding
    style, loaded as a json, with the data relating to the
    'covid_news_handling' key being found and the required values being
    extracted. A while loop is used to ensure all values are present in
    the config file, if they aren't, the event is logged and the dashboard is
    shutdown, and each value is returned to the respective functions.

    Args:
        func_name (str): The name of the function data is being returned to,
            given as a string. This allows for certain values to be returned
            to certain functions (no wasted variables).
        config_file_name (str): The name of the config file data is being taken
            from, given as a string. This allows for data in the config file
            to be used throughout the module and to customise the program.

    Returns:
        tuple[str, str, str, str]: (queries, language, sort_by, news_api_key).
            The parameters to be used in the news API call, returned as a
            tuple of strings. This allows the user to change the parameters
            used within the news API call (further customise the dashboard).
        str: displayed_content. The data from the article to be displayed in
            the content section of the news article widgets on the dashboard.
            This again lets the user customise the news section of the
            dashboard.
        tuple[str, str]: (num_displayed_articles, no_articles_message). The
            number of news articles to display on each page and the message
            that is displayed when there are no unremoved articles remaining,
            returned as a tuple of strings, allowing the user to change the
            number of displayed articles and the no articles message via the
            config file.
    """
    logging.debug("Entering the get_config_data function.")

    # Get the encoding style to be used throughout the module.
    try:
        get_encoding = open(config_file_name, 'r')
    except FileNotFoundError:
        logging.critical("Config file missing or cannot be located.")

    # Loads the json data and gets the value of the 'encoding' key.
    data = json.load(get_encoding)
    program_encoding = data['encoding']
    get_encoding.close()

    # Opens the file with the given encoding to get the rest of the data.
    with open(config_file_name, 'r', encoding=program_encoding) as\
            configuration_file:
        data = json.load(configuration_file)
        json_news_data = data['covid_news_handling']
        queries = json_news_data['queries']
        language = json_news_data['language']
        sort_by = json_news_data['sort_by']
        displayed_content = json_news_data['displayed_content']
        num_displayed_articles = json_news_data['num_displayed_articles']
        no_articles_message = json_news_data['no_articles_message']
        news_api_key = json_news_data['news_api_key']

        # Ensures a complete config file is provided before progressing.
        while (queries and language and sort_by and displayed_content
                and num_displayed_articles and no_articles_message
                and news_api_key) is not None:
            # Returns different values depending on the function calling it.
            if func_name == 'news_API_request':
                logging.info("Exiting get_config_data function as intended")
                return (queries, language, sort_by, news_api_key)

            if func_name == 'news_processor':
                logging.info("Exiting get_config_data function as intended")
                return displayed_content

            if func_name == 'remove_and_limit_news_articles':
                logging.info("Exiting get_config_data function as intended")
                return (num_displayed_articles, no_articles_message)

        logging.error("Incomplete config file provided, dashboard stopped.")


# Functions relating to the news API request.
def news_API_request(covid_terms: str = "Covid COVID-19 coronavirus") -> None:
    """Makes a complete URL from multiple parameters, then calling a function
    to process this data.

    A base URL that searches for everything with given terms within a title,
    has the queries being searched for, the language of the returned articles
    (english), the way to sort articles by (most recent articles first) and the
    API key (retrieved from the get_config_data function (returned from the
    config file)) added to it. A GET request if then made with the complete
    URL, with the returned JSON data being processed by the news_processor()
    function.

    Args:
        covid_terms (str): A string containing the terms that articles must
            contain in the title, in order to be returned. This is added to
            the complete URL and ensures that only COVID related articles are
            returned.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Entering the news_API_request function.")
    base_url = "https://newsapi.org/v2/everything?qInTitle="

    # The parameters for the GET request are retrieved from the config file.
    queries, language, sort_by, news_api_key = get_config_data(
            "news_API_request", "config.json")

    # Assembles the complete URL to be used in the GET request.
    complete_url = base_url + queries\
        + "&language=" + language\
        + "&sortBy=" + sort_by\
        + "&apiKey=" + news_api_key

    # Makes a HTTP request, receiving the result and assigning a JSON object
    # Of the returned data, allowing it to be used/ manipulated.
    logging.info("News API requets made.")
    covid_request = requests.get(complete_url)
    test_news_api_request(covid_request.json())
    logging.info("News API request received as intended.")

    logging.debug("Calling the news_processor function.")
    news_processor(covid_request.json())

    logging.debug("Exiting the news_API_request function.")
    return None


def news_processor(covid_news_data) -> None:
    """Processes the news articles, adding them to the list of articles if
    they haven't been removed or are already in the list.

    Accesses all article dictionaries in the JSON data, then looks through each
    article, if it hasn't been removed and isn't already in the global list
    of articles, then it is added to the global list as a dictionary containing
    a 'title' (headline) and 'content' (displayed content returned from the
    config file via the get_config_data function) key value pairs, doing this
    ensures that the articles can be displayed on the dashboard.

    Args:
        json: covid_news_data. This is a json object containing data on each
            article returned by the API call, this allows article data to be
            accessed as a dictionary, making it easier to access the title and
            description of each article.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Entering the news_processor function.")

    articles = covid_news_data['articles']
    displayed_content = get_config_data("news_processor", "config.json")
    logging.info("Config data received as intended.")

    # Each article that hasn't already been removed and isn't already
    # in the list of articles is added to the list of articles.
    for article in articles:
        if article not in covid_news:
            if article['title'] not in removed_article_titles:
                covid_news.append({
                    "title": article['title'],
                    "content": article[displayed_content]
                })
                logging.info(f"Article with title, {article['title']} added")

    logging.debug("Exiting the news_processor function.")

    return None


# Functions for scheduling and removing updates to news articles.
def update_news(update_interval: int, update_name: str, repeat: bool) -> None:
    """Schedules updates for news articles using the sched module.

    The sched module is used to schedule and queue updates to news articles,
    then using .run(), blocking is set to false to allow the program to
    continue executing. A dictionary containing the event_id (update
    identifier), event_name and repeat_update key value pairs is added to the
    global list tracking each of the scheduled updates if there isn't already
    an identical update in the list (helps schedule repeat updates and prevent
    duplicates from appearing in the list).

    Args:
        update_interval (int): The time delay (as enter is used instead of
            enterabs) for the scheudled update, given as an integer. This is
            used to dictate the time the scheduled update will run at.
        update_name (str): The name of the scheduled upate, given as a string.
            This is used as a linking value, making it possible to match
            values in the global queue to events in the scheduler queue and
            remove them. --> Used as the value in the 'event_name' key value
            pair.
        repeat (bool): A boolean value indicating whether the update has been
            scheduled to repeat every day. This is used to decide if updates
            should be removed once they have expired and is the value in the
            'repeat_update' key value pair.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Entering the update_news function.")
    # Covid data is given priority over the news to ensure
    # There are no clashes.
    news_scheduler.enter(update_interval, 1, news_API_request,)
    news_scheduler.run(blocking=False)

    # The newest item in the scheduler queue is the desired update to add.
    queue_length = len(news_scheduler.queue) - 1

    logging.info(f"Update: {news_scheduler.queue[queue_length]} added")
    logging.info("to queue.")

    update_to_add = {
                     'event_id': news_scheduler.queue[queue_length],
                     'event_name': update_name,
                     'repeat_update': repeat}

    # The update is only added if it isn't already in the list.
    duplicate_tracker = False
    for update in news_queue_info:
        if update_to_add == update:
            duplicate_tracker = True

    if duplicate_tracker is False:
        news_queue_info.append(update_to_add)
        logging.info("Update added to global list.")

    logging.debug("Exiting the update_news function.")

    return None


def remove_news_update(removed_update_name: str, expired: bool) -> None:
    """Removes any expired news articles or any articles that have been
    manuallyremoved by the user.

    If an update has expired, a loop is used to find the update and remove it
    from the global list of updates. Otherwise, updates need to be removed
    manually, this is done by searching for the removed udpate in the list
    of updates and removing it from the scheduler queue (the event id is
    assigned to a variable and then used to remove the update) and global list.
    A try accept is used to catch any repeat upates that have already expired
    (not in the update queue) but are still manually removed.

    Args:
        removed_update_name (str): The name of the update to be removed, given
            as a string. This enables the update to be removed from the
            scheduler queue (Allows for the event ID to be found) and is used
            to ensure the correct update is removed, regardless of whether it
            had expired or was manually removed.
        expired (bool): A boolean value indicating whether or not a scheduled
            update currently being displayed has already expired. Consequently
            , this is used to help remove any expired updates.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Entering the remove_news_update function.")
    # Expired updates are removed from the global list of articles.
    if expired is True:
        for update in news_queue_info:
            if update['event_name'] == removed_update_name:
                logging.info("Expired update removed from global list.")
                news_queue_info.remove(update)

    # Iterates through the global list of events, if the removed event.
    # Is in the global list, it is removed from the queue and the list.
    for update in news_queue_info:
        if update["event_name"] == removed_update_name:
            event_to_remove = update['event_id']

            # Events must be in (and removed from) both the global list
            # And the queue if the event has not expired.
            news_queue_info.remove(update)

            try:
                news_scheduler.cancel(event_to_remove)
                logging.info("Update removed from queue and list.")
            except ValueError:
                logging.warning("Repeat update removed from list.")

    logging.debug("Exiting the remove_news_update function.")

    return None


def remove_and_limit_news_articles(news_articles_list: list,
                                   removed_article: list = []) \
                                   -> tuple[list, list]:
    """Removes any articles that are provided and limits the number of
    displayed articles to four unremoved articles.

    If an article is passed as a parameter, it is added to the global list of
    removed articles. A loop is used to find all the all the articles that
    haven't been removed yet (added to a local list), another loop is then
    used to add a maximum of four (or however many are specified in the config
    file) of these articles to the list of articles that are returned. If
    there are no articles left to display, a message is displayed to notify
    the user.

    Args:
        news_articles_list (list): All news articles returned by a News API
            call (stored as a list). This allows for news articles to be
            updated once the user removes an article.
        removed_article (list): The article to be removed from the dashboard,
            given as a list containing a single article title (if nothing is
            provided, it is set to an empty list). This is used to stop
            displaying removed articles on the dashboard.

    Returns:
        tuple: (news_articles_list, return_articles). A tuple containing the
            original list of news articles along with a list of the four
            unremoved articles to be displayed on the dashboard. This prevents
            excessive API calls from being made as the original list of
            articles are maintained and ensures the user doesn't have to scroll
            to far for articles by limiting the number of displayed articles to
            four.
    """
    logging.debug("Entering the remove_and_limit_news_articles function.")
    return_articles = []
    unremoved_articles = []
    article_counter = 0
    # Gets the number of articles and message (when no articles remain).
    # To display from the config file.
    num_displayed_articles, no_articles_message = get_config_data(
            "remove_and_limit_news_articles", "config.json")
    logging.info("Data retrieved from config file as intended.")

    # If there are no articles left, nothing happens.
    if len(news_articles_list) == 0:
        return news_articles_list

    if len(removed_article) > 0:
        logging.info("Removed article title added to global list of articles.")
        removed_article_titles.append(removed_article)

    # Only displaying articles that haven't already been removed.
    for article_counter in range(0, len(news_articles_list)):
        # Allows the title key of the articles to be accessed.
        current_article = news_articles_list[article_counter]
        if current_article['title'] not in removed_article_titles:
            unremoved_articles.append(current_article)

        article_counter += 1

    # If no articles are left, a message is displayed to notify the user.
    if len(unremoved_articles) == 0:
        out_of_articles_message = {'title': '',
                                   'content': no_articles_message}
        return_articles.append(out_of_articles_message)
        logging.warning("No news articles remaining.")

    # The number of displayed articles is limited to what is specified.
    # In the config file.
    for article in range(0, len(unremoved_articles)):
        if len(return_articles) < int(num_displayed_articles):
            return_articles.append(unremoved_articles[article])

    logging.info(f"{(news_articles_list, return_articles)} returned.")
    logging.debug("Exiting the remove_and_limit_news_articles function.")

    return (news_articles_list, return_articles)


def return_covid_news() -> list:
    """Returns the global list of covid news.

    Returns:
        list: covid_news. The global list containing news articles is
            returned. This allows this function to act as a getter method for
            main.py, enabling covid_news articles to be returned without
            needing to make another API call.
    """
    logging.debug("Entering and exiting the return_covid_news function.")
    logging.info("Covid news is returned.")
    return covid_news


# Test functions
def test_news_api_request(covid_request: dict) -> None:
    """Tests the news_api_request function, checking that data is returned
    by the API call and that articles are also returned by the API call.

    Args:
        covid_request (dict): A dictionary representing the data returned by
            the API call. This is used to check whether data and articles are
            returned by the news API call.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    # Checks to see if data is returned, logging the result.
    if covid_request is None:
        logging.critical("No data returned by news API request.")
        raise SystemExit
    # Checks to see if articles are returned, logging the result.
    else:
        logging.info("Data returned by API.")
        if covid_request['articles'] is None:
            logging.error("No articles returned in API call.")
            raise SystemExit

    return None


def test_update_news() -> None:
    """Sentence

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """


def test_remove_news_update() -> None:
    """Sentence

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
