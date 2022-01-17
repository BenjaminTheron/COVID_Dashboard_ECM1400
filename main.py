"""This module contains all the functionality for displaying the user
interface, including displaying news and COVID stats.
"""
import time
import json
import logging
from flask import render_template, Flask, request
from covid_data_handler import covid_API_request, return_covid_data
from covid_data_handler import schedule_covid_updates, remove_covid_data_update
from covid_news_handling import news_API_request, return_covid_news
from covid_news_handling import remove_and_limit_news_articles, update_news
from covid_news_handling import remove_news_update

# Configures the base logging level and log file to be used for this module.
logging.basicConfig(filename='sys.log', level=logging.DEBUG)

app = Flask(__name__)

# Global lists of dictionaries to track all the scheduled updates.
# Worse for memory usage but makes it easier to carry out repeat updates.
scheduled_updates = []

# Global variables are used to ensure data and news are only updated when
# There is a scheduled update.
covid_API_request()
england_covid_data, local_covid_data = return_covid_data()
news_API_request()
covid_news = return_covid_news()
displayed_covid_articles = []


def find_config_data(func_name: str, config_file_name: str = "config.json")\
        -> tuple[str, str, str] | str | tuple[str, str]:
    """Extracts the data pertaining to the main module from the
    provided config file.

    A try except is used to get the encoding style to be used, and to check if
    a valid/present config file has been provided. If one hasn't been provided
    the event is logged and the dashboard is shutdown. Otherwise, the encoding
    style is extracted (data loaded as a json and the value of the 'encoding'
    key is found). The config file is opened again with the required encoding
    style, loaded as a json, with the data relating to the
    'main_program' key being found and the required values being
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
        tuple[str, str, str]: (image, title, location). The image, title and
            location to be displayed on the dashboard, returned as a tuple of
            strings. This lets the user change the favicon at the top of the
            page, the title and location displayed, through the use of the
            config file.
        str: base_update_interval. The base update delay to be used if one
            isn't passed into the schedule_updates function, given as a string
            . This lets the user customise the application by choosing the
            base update interval to be used.
        tuple[str, str]: base_flask_route, reroute_flask_route. The flask
            routes to be used during the execution of the program, given
            as a tuple of strings. These can be changed but will break the
            program if it is (Program can be extended to accommodate this).
    """
    logging.debug("Entering the find_config_data function.")
    # Gets the encoding to be used throughout the module.
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
        main_json_data = data['main_program']
        image = main_json_data['image']
        title = main_json_data['title']
        location = main_json_data['location']
        base_update_interval = main_json_data['base_update_interval']
        # Flask routes are stored in a further dictionary.
        flask_routes = main_json_data['flask_routes']
        base_flask_route = flask_routes['base_flask_route']
        reroute_flask_route = flask_routes['reroute_flask_route']

        # Ensures a complete config file is provided before progressing.
        while (image and title and location and base_update_interval
                and base_flask_route and reroute_flask_route) is not None:
            # Returns different values depending on the function calling it.
            if func_name == "render_webpage":
                logging.info("Exiting find_config_data function as intended")
                return (image, title, location)

            if func_name == "schedule_update":
                logging.info("Exiting find_config_data function as intended")
                return base_update_interval

            if func_name == "global":
                logging.info("Exiting find_config_data function as intended")
                return (base_flask_route, reroute_flask_route)

        logging.error("Incomplete config file provided, dashboard stopped.")


logging.debug("Entering the find_config_data function.")
# Retrieves the flask routes to be used, from the config file.
base_flask_route, reroute_flask_route = find_config_data(
    "global", "config.json")
logging.info("Base and reroute flask routes retrieved as intended.")


# Flask functions that display the dashboard.
@app.route(base_flask_route)
def render_webpage():
    """Fills in (with covid data and news articles) and displays
    the provided render template if the URL starts with a /.

    Gets the data to display in the template via getter functions, calling
    functions to display news articles (if there are any).

    Uses the requests module (imported from flask) to check if the user
    has scheduled an update and/ or has clicked the cross to remove a news
    article, calling the respective functions to deal with the events.

    Moreover, this function also checks to see if any repeat updates need to be
    scheduled, done by checking the dictionary keys if the time is between
    23:59 and 24:00. While this makes the time complexity of the program
    O(n^2), it has little effect on performance when there are few updates
    being displayed/stored.

    Additionally, this function is always calls the remove scheduled update
    function, to see if an updates have expired and need to be removed.

    Returns:
        function: render_template(). Returns the render_template function that
            has been imported from the flask module, along with the parameters
            required for the function to display the dashboard with all the
            relevant data.
    """
    logging.debug("Entering the render_webpage function.")

    # Lets for the global variables to be assigned (altered) in the function.
    global england_covid_data, local_covid_data, displayed_covid_articles
    global covid_news

    logging.debug("Calling the find_config_data function.")
    # Gets the image, title and location to be used from the config file.
    image, title, location = find_config_data("render_webpage", "config.json")

    # Finds the current time (hrs and mins) to help reschedule repeat updates.
    current_time = time.localtime()
    current_time_hrs = current_time[3]
    current_time_mins = current_time[4]

    logging.debug("Calling the return_covid_data/news functions.")
    # Updates the news and covid data if any changes have been made.
    england_covid_data, local_covid_data = return_covid_data()
    covid_news = return_covid_news()

    # Finds articles to display (if there are any left).
    if len(displayed_covid_articles) == 0 and len(covid_news) > 0:
        logging.debug("Calling the remove_and_limit_news_articles function.")
        covid_news, displayed_covid_articles = (
            remove_and_limit_news_articles(covid_news))

    # Checks to see if the user has removed a news article.
    if request.args.get("notif") is not None:
        logging.debug("remove_and_update_news_articles function is called.")
        remove_and_update_news_article()

    logging.info("remove_scheduled_update function is called as intended.")
    remove_scheduled_update()

    # Checks to see if any repeat updates need to be scheduled.
    if current_time_hrs == 23 and current_time_mins == 59:
        for update in scheduled_updates:
            if update['repeat'] is True:
                # Schedule_update cannot be called as it would add another.
                # Instance of the update to the list of updates.
                logging.debug("The repeat updates function is called.")
                repeat_updates_scheduler(update)

    # For any update the user has to enter a name.
    if request.args.get("two") is not None:
        logging.info("The user has scheduled an update.")
        entered_time = request.args.get("update")
        repeat_updates = request.args.get("repeat")
        update_covid = request.args.get("covid-data")
        news_update = request.args.get("news")

        # Schedules covid data and news updates depending on what boxes
        # Were pressed.
        logging.info("Schedule_update function is called as intended.")
        if update_covid == 'covid-data' and news_update == 'news':
            schedule_update(request.args.get("two"),
                            entered_time, repeat_updates,
                            update_covid, news_update)

        # Schedules an update if only the covid box has been ticked.
        elif update_covid == 'covid-data':
            schedule_update(request.args.get("two"),
                            entered_time, repeat_updates,
                            update_covid, news_update)

        # Does the same as above, but if the news box has been ticked.
        elif news_update == 'news':
            schedule_update(request.args.get("two"),
                            entered_time, repeat_updates,
                            update_covid, news_update)

    # To ensure lines are under 79 characters.
    # Replacement variables need to be used.
    england_7cases = england_covid_data['newCasesBySpecimenDate']
    local_7cases = local_covid_data['newCasesBySpecimenDate']
    h_cases = str(england_covid_data['hospitalCases'])
    total_deaths = str(england_covid_data['cumDailyNsoDeathsByDeathDate'])

    logging.info("Render template is returned and displayed as intended.")
    # Returns a render template and all the needed data to display the page.
    return render_template('index.html',
                           # The favicon is a picture of the UoE logo.
                           image=image,
                           updates=scheduled_updates,
                           title=title,
                           location=location,
                           local_7day_infections=local_7cases,
                           nation_location='England',
                           national_7day_infections=england_7cases,
                           hospital_cases=("Hospital cases: " + h_cases),
                           deaths_total=("Total deaths: " + total_deaths),
                           news_articles=displayed_covid_articles)


@app.route(reroute_flask_route)
def render_webpage_reroute():
    """This function re-routes execution back to the render_template()
    function after the URL has changed.

    Returns:
        function: render_webpage(). Returns the render_webpage() function,
            allowing for the render template to be displayed even when the URL
            changes to /index after 60 seconds.
    """
    logging.warning("URL changed.")
    logging.debug("Entering and exiting render_webpage_reroute.")
    return render_webpage()


def remove_and_update_news_article() -> None:
    """Stores a removed article and stops displaying it on the dashboard.

    The requests module is used to get the title of the removed article,
    this is then added to a local list and the remove_and_limit_news_articles()
    function is called with the required parameters to update the articles
    displayed on the dashboard.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Entering the remove_and_update_news_article function.")
    # Lets the global variables be assigned (updated) within the function.
    global covid_news
    global displayed_covid_articles
    removed_article = []

    removed_article.append(request.args.get("notif"))

    # If an article has been removed the news is updated.
    if len(removed_article) > 0 and removed_article[0] is not None:
        # To ensure PEP8 is met this variable transfer is required.
        logging.debug("remove_and_limit_news_articles function called")
        return_tuple = remove_and_limit_news_articles(covid_news,
                                                      removed_article[0])
        logging.info("Global list of displayed articles is updated.")
        covid_news, displayed_covid_articles = return_tuple

    logging.debug("Exiting the remove_and_update_news_article function.")
    return None


# Functions for scheduling and removing updates.
def schedule_update(update_name: str, given_time: str, repeat: bool,
                    covid_update: bool, news_update: bool) -> None:
    """This function schedules updates with data provided by the user from the
    COVID dashboard.

    Puts the boolean parameters into a format that is easier to manipulate,
    the time delay for the scheduled update is then calculated using the
    given_time parameter. Title and content key:value pairs are then added
    to a local dictionary (this dictionary is then added to the global list
    of scheduled updates if an identical update hasn't been scheduled before).
    The schedule_covid_updates and update_news are then used (with the
    required parameters being inputted) to schedule the updates respectively.
    Note, 'covid', 'news', 'repeat' and 'time' key value pairs are added to
    make it easier to remove updates and schedule repeat updates.

    Args:
        update_name (str): This is the name of scheduled update as a string,
            it's assigned to the 'title' key in the dictionary of the update,
            passed into the respective schedule update functions and is the
            'title' displayed on the dashboard.
        given_time (str): The desired time for the update to occur, given as a
            string in 24 hour format. This is passed into the update_buffer
            function to find the time delay for the update and is assigned to
            the 'time' key in the dictionary for the update.
        repeat (bool): A boolean value indicating whether the update is a
            repeat or not. This is passed into the respective update functions
            and is assigned to the 'repeat' key in the dictionary for the
            update.
        covid_update (bool): A boolean value indicating whether covid data
            should be updated. Akin to above, but is assigned to the 'covid'
            key in the dictionary for the update.
        news_update (bool): A boolean value indicating whether the news
            articles should be updated. Akin to above, but is assigned to the
            'news' key in the dictionary for the update.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Entering the schedule_update function.")
    schedule_dictionary = {}

    if covid_update is not None:
        covid_update = True
    else:
        covid_update = False

    if news_update is not None:
        news_update = True
    else:
        news_update = False

    if repeat is not None:
        repeat = True
    else:
        repeat = False

    # If no time is entered, the buffer is the value found in the config file.
    # Otherwise the buffer is the value returned by time_buffer().
    if given_time == "":
        logging.warning("No time entered for update.")
        logging.debug("find_config_data function is called.")
        update_buffer = int(find_config_data("schedule_update", "config.json"))
        given_time = "00:00"

    else:
        # To allow for string slicing, the time is passed as a string.
        logging.debug("time_buffer function is called.")
        update_buffer = time_buffer(str(given_time))

    # Adds the scheduled update to the list, so it can be displayed.
    schedule_dictionary['title'] = update_name

    schedule_dictionary['content'] = "COVID Update: " \
        + str(covid_update) + "\nNews Update: " \
        + str(news_update) + "\nRepeat Update: " \
        + str(repeat) + "\nUpdate at: " \
        + str(given_time)
    # The int conversion removes any decimal points.
    # The str conversion maintains consistency.

    schedule_dictionary['covid'] = covid_update
    schedule_dictionary['news'] = news_update
    schedule_dictionary['repeat'] = repeat
    schedule_dictionary['time'] = given_time

    duplicate_update = False
    # A loop to ensure duplicate updates are not added displayed.
    for update in scheduled_updates:
        if schedule_dictionary == update:
            duplicate_update = True

    if duplicate_update is False:
        # Adds the scheduled update to the global list of all updates.
        logging.info("Scheduled update is added to global list of all updates")
        scheduled_updates.append(schedule_dictionary)

    # Doing this ensures that news and data can be updated separately.
    logging.info("Respective schedule update functions are called.")
    # Schedules the respective updates.
    if news_update is True and covid_update is True:
        schedule_covid_updates(update_buffer, update_name, repeat)
        update_news(update_buffer, update_name, repeat)

    elif covid_update is True:
        schedule_covid_updates(update_buffer, update_name, repeat)

    elif news_update is True:
        update_news(update_buffer, update_name, repeat)

    logging.debug("Exiting the schedule_update function.")

    return None


def repeat_updates_scheduler(update: dict) -> None:
    """Called if the time is between 23:59 and 24:00 and schedules any repeat
    updates for the next day.

    Finds the time delay between midnight and the time of the update (via
    the time_buffer function). The schedule_covid_updates and update_news
    functions are then called directly (prevents duplicates from being added
    to the scheduled_updates global list) and respectively.

    Args:
        update (dict): A dictionary containing the all the key: value pairs (
            update data) about an update. Used to find the time buffer and
            schedule the respective updates.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Entering the repeat_updates_scheduler function.")
    # Finds the time delay.
    time_delay = time_buffer(update['time'])

    logging.info("Respective functions called to schedule update.")
    # Schedules the respective updates.
    if update['covid'] is True and update['covid'] is True:
        schedule_covid_updates(time_delay, update['title'], True)
        update_news(time_delay, update['title'], True)

    elif update['covid'] is True:
        schedule_covid_updates(time_delay, update['title'], True)

    elif update['news'] is True:
        update_news(time_delay, update['title'], True)

    logging.debug("Exiting the repeat_updates_scheduler function.")
    return None


def remove_scheduled_update() -> None:
    """Removes scheduled updates from the respective global list of updates
    and the scheduler update queue(s), stopping them from being displayed on
    the dashboard.

    The request function is used to check if the user has removed an update,
    if they have (update name matches value returned by request), the update
    is removed from the global list of updates and the events are removed from
    their respective update queue. This function then goes through each item
    in the list of updates to check for any 'expired' update (ones that have
    already happened). Any expired updates are then removed from the global
    list of scheduled updates; the remove_covid_data_update and
    remove_news_update functions are called respectively to update the global
    lists for covid data and news articles.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Entering the remove_scheduled_update function.")
    # Removes updates and events if the user removes an update.
    if request.args.get("update_item") is not None:
        logging.info("The user has removed a scheduled update widget.")
        for update in scheduled_updates:
            if update['title'] == request.args.get("update_item"):
                scheduled_updates.remove(update)

                logging.info(f"Functions called to remove {update}.")
                # Function calls to remove the update.
                remove_news_update(update['title'], False)
                remove_covid_data_update(update['title'], False)

    for update in scheduled_updates:
        # String slicing is used to check whether the time of the update is.
        # Less than the current time, if it is, the update is removed.
        update_time = update['time']
        current_time = time.localtime()
        if int(update_time[:2:]) == current_time[3]\
                and int(update_time[3::]) <= current_time[4]:

            logging.info(f"{update} has expired")
            scheduled_updates.remove(update)

            # The global lists holding the news and covid updates need to be.
            # Updated accordingly.
            logging.info("Respective functions called to remove update.")
            if update['covid'] is True and update['news'] is True:
                remove_covid_data_update(update['title'], True)
                remove_news_update(update['title'], True)

            elif update['covid'] is True:
                remove_covid_data_update(update['title'], True)

            elif update['news'] is True:
                remove_news_update(update['title'], True)

    logging.debug("Exiting the removed_scheduled_update function.")

    return None


def time_buffer(given_time: str,
                current_time: tuple = time.localtime()) -> int:
    """Finds the time delay (difference between the entered time and the
    current time) to be used for scheduling an update.

    Finds the current time in seconds (using indexes from the time.localtime()
    tuple), uses string slicing to get the hours and minutes of the current
    time, converting these to find the entered time in seconds. The buffer is
    then the difference between these two values. If the entered time is in the
    past, the time between the current time and midnight, then midnight and the
    entered time is found (in seconds) and used as the buffer.

    Args:
        given_time (str): The time the user wants the update to be scheduled
            for, given in 24 hour format as a string. This is converted to
            seconds and used to find the time delay for the update.
        current_time (tuple): A tuple of values indicating the current time, if
            no value is passed in, this argument's default value is set to the
            current time (returned by the time.localtime() function). This is
            converted into seconds and used to find the time delay for the
            update.

    Return:
        int: buffer_time. An integer representing the delay in time to be used
            when scheduling an update. This is the difference between the
            entered time and the current time.
    """
    logging.debug("Entering the time_buffer function.")
    # Converts the hours and minutes to seconds and adds them together.
    # Finds the current time in seconds.
    current_time_seconds = (current_time[3] * 60 * 60)\
        + (current_time[4] * 60)

    # As a 24 hour clock is used and only numbers can be entered.
    time_hours = given_time[:2:]
    time_minutes = given_time[3::]

    # The entered time is converted into seconds.
    entered_time_seconds = (int(time_hours) * 60 * 60) \
        + (int(time_minutes) * 60)

    buffer_time = entered_time_seconds - int(current_time_seconds)

    # Updates for a time before the current time are scheduled for
    # The next day.
    if buffer_time < 0:
        logging.info("Update is scheduled for the next day.")
        now_midnight = time_buffer("24:00")
        midnight_time = time_buffer(given_time, "00:00")

        buffer_time = now_midnight + midnight_time

    logging.debug(f"Exiting time_buffer and returning {buffer_time}")

    return buffer_time


# Test Functions.
def test_render_webpage() -> None:
    """Sentence

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """


def test_render_webpage_reroute() -> None:
    """Sentence

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """


def test_remove_and_update_news_article() -> None:
    """Sentence

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """


def test_schedule_update() -> None:
    """Sentence

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """


def test_remove_scheduled_update() -> None:
    """Sentence

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """


if __name__ == '__main__':
    app.run()
