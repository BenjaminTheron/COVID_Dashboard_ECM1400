"""This module contains all the COVID data handling functionality."""
import sched
import time
import json
import logging
from uk_covid19 import Cov19API

# Configures the base logging level and log file to be used for this module.
logging.basicConfig(filename='sys.log', level=logging.DEBUG)

# Initialises the scheduler and allows it to be used.
covid_scheduler = sched.scheduler(time.time, time.sleep)

# Global dictionaries for national and local data (makes it easier to
# schedule updates).
england_data = {}
local_data = {}

# Holds all the data on items in the queue, making it easier to remove
# Articles from the scheduler queue.
covid_queue_info = []


# Functions relating to CSV data.
def parse_csv_data(csv_filename: str) -> list:
    """Parses through a CSV file, reading and storing each line of the file.

    Opens a csv file, assigning covid_csv_file to a list of all lines in the
    file. For each line in the file, the newline character and the commas are
    removed from the file, with each line being appended to a local list
    that is then returned.

    Args:
        csv_filename (str): The name of the csv file to be parsed, given as
            a string. This allows for data to be extracted from the csv file.

    Returns:
        list: covid_csv_data. This is a list, where each index is a line from
            the csv file. This allows for the data to be accessed and modified
            much easier (specific values can be accessed much easier) than if
            it were in plain csv format.
    """
    covid_csv_data = []

    with open(csv_filename, 'r', encoding='utf8') as covid_csv_file:
        covid_csv_file = covid_csv_file.readlines()

    for index in covid_csv_file:
        # Removing the newline escape character from the line.
        index = index[:-1:]

        # Splits the line into each section, converts it to a tuple
        # And adds it to a list.
        covid_csv_data.append(tuple(index.split(",")))

    return covid_csv_data


def process_covid_csv_data(covid_csv_data: list) -> tuple[int, int, int]:
    """Goes through the list of the covid_csv_data, finding the cases over the
    last seven days, the total number of deaths and the number of people
    currently in the hospital with covid.

    Removes the titles from the list of data. Loops are then used to ensure
    a value is found for the total number of deaths and current hospital cases
    , if the first value for each respective category is incomplete. The total
    cases over the last seven days are found via a for loop that ignores the
    first entry (starts from the second day) and starts from the first day
    with a value.

    Args:
        covid_csv_data (list): Each line from a given csv file, stored as
            indexes in a list. This is contains the data for the returned
            values and is processed, enabling the returned values to be found.

    Returns:
        tuple: (last_seven_days_cases, int(current_hospital_cases),
            int(cumulative_deaths)). For consistency and ease of manipulation,
            all values are returned as integers, with the tuple allowing for
            all three values to be returned at once. This allows for values
            found via the given list to be returned/ displayed (not in this
            case).
    """
    # Removes the titles from the list of data.
    covid_csv_data.remove(covid_csv_data[0])

    last_seven_days_counter = 2
    last_seven_days_cases = 0
    # Gets initial values for deaths and hospital cases.
    current_hospital_cases = covid_csv_data[0][5]
    cumulative_deaths = covid_csv_data[0][4]
    counter_for_deaths, hospital_cases_counter = 1, 1

    # If the first value is incomplete a value is found via backtracking.
    while cumulative_deaths == '':
        cumulative_deaths = covid_csv_data[counter_for_deaths][4]
        counter_for_deaths += 1

    # Does the same as above, but for hospital cases.
    while current_hospital_cases == '':
        current_hospital_cases = covid_csv_data[hospital_cases_counter][5]
        hospital_cases_counter += 1

    # Ensures it only starts summing from the first day with a value.
    while covid_csv_data[last_seven_days_counter][6] == '':
        last_seven_days_counter += 1

    # Sums the cases from the second day.
    for day in range(last_seven_days_counter, last_seven_days_counter + 7):
        last_seven_days_cases += int(covid_csv_data[day][6])

    return (last_seven_days_cases, int(current_hospital_cases),
            int(cumulative_deaths))


# Function to get data from a configuration file.
def config_data(func_name: str, config_file_name: str = "config.json")\
        -> tuple[str, str] | str:
    """Extracts the data pertaining to the covid_data_handler module from the
    provided config file.

    A try except is used to get the encoding style to be used, and to check if
    a valid/present config file has been provided. If one hasn't been provided
    the event is logged and the dashboard is shutdown. Otherwise, the encoding
    style is extracted (data loaded as a json and the value of the 'encoding'
    key is found). The config file is opened again with the required encoding
    style, loaded as a json, with the data relating to the
    'covid_data_handler' key being found and the required values for this
    being extracted. A while loop is used to ensure all values are present in
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
        tuple[str, str]: (location, location_type). A tuple containing the
            location and type of location the user has specified in the config
            file. This lets the user change the location and location type
            displayed via the config file.
        str: commas. A yes or no string that indicates whether or not commas
            are to be added to the values displayed on the dashboard, giving
            the user a way to customise the dashboard.
    """
    logging.debug("Entering the config_data function.")
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
        covid_json_data = data['covid_data_handler']
        location = covid_json_data['location']
        location_type = covid_json_data['location_type']
        commas = covid_json_data['commas']

        # Ensures a complete config file is provided before progressing.
        while (location and location_type and commas) is not None:
            # Returns different values depending on the function calling it.
            if func_name == "process_covid_json_data":
                logging.info("Exiting config_data function as intended")
                return commas
            if func_name == "covid_API_request":
                logging.info("Exiting config_data function as intended")
                return (location, location_type)

        logging.error("Incomplete config file provided, dashboard stopped.")


# Functions for processing the COVID API request.
def covid_API_request(location: str = 'Exeter',
                      location_type: str = 'ltla') -> None:
    """Creates filters and structures for two API calls to PHE for both local
    and national COVID related data.

    Creates a national (only england data is returned) and local filter (only
    local data is returned). The location and location type to be used in the
    filter are found by calling the config data function with the required
    parameters. The structure (type and order of returned values) of the
    national (total deaths, current hospital cases and new cases every day)
    and local data (new cases every day) returned by the API calls is then
    defined. The two national and local API calls are then made, with the data
    being extracted as json data, with the value of the data key in the json
    dictionary being passed into the process_covid_json_data function.

    Args:
        location (str): The location to be used in the filter for the local
            API call, given as a string. This allows for COIVD data for a
            given local area to be returned, used and displayed.
        location_type (str): The type of location to be used in the filter for
            the local API call, given as a string. This allows for COVID data
            related to a specific area type to be manipulated and displayed.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Entering the covid_API_request function")

    global england_data, local_data

    logging.debug("Calling config_data function from covid_API_request")
    (location, location_type) = config_data("covid_API_request", "config.json")
    logging.debug("Data correctly received from config file.")

    # Used to ensure only data for England is returned.
    england_filter = [
        'areaType=nation',
        'areaName=England'
    ]

    # Used to ensure only data from the provided location is returned.
    local_filter = [
        ('areaType=' + location_type),
        ('areaName=' + location)
    ]

    # Defines the type and structure of the data returned by the API.
    england_structure = {
        "areaName": "areaName",
        "date": "date",
        "cumDailyNsoDeathsByDeathDate": "cumDailyNsoDeathsByDeathDate",
        "hospitalCases": "hospitalCases",
        "newCasesBySpecimenDate": "newCasesBySpecimenDate"
    }

    # Does the same as above, but for the provided area instead.
    local_structure = {
        "areaName": "areaName",
        "date": "date",
        "newCasesBySpecimenDate": "newCasesBySpecimenDate"
    }

    # Instantiates the Cov19 API object with the given filters and
    # Strucutre for the England call.
    england_api_call = Cov19API(filters=england_filter,
                                structure=england_structure)

    # Does the same as above but for the local call.
    local_api_call = Cov19API(filters=local_filter,
                              structure=local_structure)

    # Extracts the data as a JSON for both calls.
    england_data = england_api_call.get_json()
    local_data = local_api_call.get_json()

    test_covid_API_request(england_data, local_data)
    logging.info("Passed unit test.")

    # Extracts the data key from the local and national JSON files.
    england_data = england_data['data']
    local_data = local_data['data']

    logging.debug("Calling the process_covid_json_data function.")
    process_covid_json_data(england_data, local_data)

    logging.debug("Exiting the covid_API_request function as intended.")
    return None


def process_covid_json_data(england_covid_data: list,
                            local_covid_data: list) -> None:
    """Goes through the lists of national and local covid data, finding
    the cases over the last seven days nationally and locally, along with
    finding the total deaths and current hospital cases nationally.

    Extracts the most recent data for the hospital cases and total deaths,
    if these values are incomplete, a loop is used to backtrack until a value
    is found. the seven_day_case_calculator function is then called to find
    the cases over the last seven days at the national and local level. On top
    of this, commas are added to the values (if specified in the config file)
    and each value is assigned to the respective key in a local dictionary for
    national and local data. A setter method is then called to set the data
    values.

    Args:
        england_covid_data (list): The national COVID data, given as a list
            holding all the data values returned by the API call. This allows
            for the cases over the last seven days, total deaths and hospital
            cases to be calculated at the national level, and hence displayed.
        local_covid_data (list): The local COVID data, given as a list holding
            all the data values returned by the API call. This lets the number
            of cases over the last seven days locally be calculated and hence,
            displayed.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Enter the process_covid_json_data function as intended.")

    # Used for backtracking through the data until values are found.
    national_data_counter = 0
    england_recent_cases, local_recent_cases = (0, 0)
    england_covid_dictionary = {}
    local_covid_dictionary = {}

    # Looks at the most recent entry in the national list.
    england_covid_recent = england_covid_data[national_data_counter]

    england_hospital_cases = england_covid_recent['hospitalCases']
    england_total_deaths = england_covid_recent['cumDailyNsoDeathsByDeathDate']

    while england_hospital_cases is None or england_total_deaths is None:
        national_data_counter += 1
        england_covid_recent = england_covid_data[national_data_counter]

        if england_hospital_cases is None:
            logging.warning("Incomplete data, backtracking for hospital cases")
            england_hospital_cases = england_covid_recent['hospitalCases']

        elif england_total_deaths is None:
            logging.warning("Incomplete data, backtracking for total deaths.")
            # Done to ensure PEP8 line length limits are met.
            total_deaths = 'cumDailyNsoDeathsByDeathDate'
            england_total_deaths = england_covid_recent[total_deaths]

    logging.debug("Calling seven_day_case_calculator function")
    england_recent_cases = seven_day_case_calculator(england_covid_data)
    logging.debug("Calling seven_day_case_calculator function")
    local_recent_cases = seven_day_case_calculator(local_covid_data)

    logging.debug("Calling the config_data function for commas variable")
    # If specified in the config file, commas will be added to the values.
    commas = config_data("process_covid_json_data", "config.json")

    if commas == "yes":
        # Adds commas after every three digits, increasing readablility.
        # Values are converted to strings making them easier to manipulate.
        england_recent_cases = comma_separator(str(england_recent_cases))
        england_hospital_cases = comma_separator(str(england_hospital_cases))
        england_total_deaths = comma_separator(str(england_total_deaths))
        local_recent_cases = comma_separator(str(local_recent_cases))

    # Adds the required key : value pairs to the return dictionaries.
    total_deaths = 'cumDailyNsoDeathsByDeathDate'

    england_covid_dictionary['newCasesBySpecimenDate'] = england_recent_cases
    england_covid_dictionary['hospitalCases'] = england_hospital_cases
    england_covid_dictionary[total_deaths] = england_total_deaths

    local_covid_dictionary['newCasesBySpecimenDate'] = local_recent_cases

    logging.debug("Calling the set_covid_data function.")
    set_covid_data(england_covid_dictionary, local_covid_dictionary)

    logging.debug("Exiting the process_covid_json_data function as intended.")

    return None


def seven_day_case_calculator(covid_data: dict) -> int:
    """Finds the number of cases over the last seven days, starting from the
    first day with a provided value.

    Assigns the most recent covid data to a variable. A loop is then used to
    backtrack through the covid data until a day with a value is found (only
    done if the first day has no value). Another loop is then used to sum the
    cases over the seven days prior to the start day.

    Args:
        recent_covid_data (dict): A dictionary holding all the covid data to
            be searched through. This data is then used to find the cases over
            the last seven days.

    Returns:
        int: seven_day_cases The total number of new COVID cases over the last
            week, returned as an integer, this allows for the specification to
            be met and for the required COVID data to be displayed on screen.
    """
    logging.debug("Entering the seven_day_case_calculator function.")
    seven_day_cases = 0
    data_counter = 0

    recent_covid_data = covid_data[data_counter]

    while recent_covid_data['newCasesBySpecimenDate'] is None:
        logging.warning("Incomplete data provided, backtracking for cases.")
        data_counter += 1
        recent_covid_data = covid_data[data_counter]

    # Finds the sum of the cases over the seven day window.
    for day in range(data_counter, (data_counter + 7)):
        recent_covid_data = covid_data[day]
        seven_day_cases += int(recent_covid_data['newCasesBySpecimenDate'])

    logging.debug("Exiting seven_day_case_calculator function as intended.")
    return seven_day_cases


# Functions for scheduling and removing updates to COVID data.
def schedule_covid_updates(update_interval: int,
                           update_name: str, repeat: bool) -> None:
    """Schedules updates to COVID data via the sched module.

    Initialises a scheduled update to the COVID data with the provided update
    interval and referencing the covid_API_request function. The update is
    then scheduled with blocking set to false so the program's execution isn't
    halted until the update is executed. The scheduled event along with other
    data ("id", the name of the event and whether the update is repeating)
    that allows it to be linked, referenced and identified is added to
    the global list of scheduled events as a dictionary, if said dictionary
    doesn't already appear in the list of updates. Doing this helps schedule
    repeat updates and prevent duplicates from appearing in the list).

    Args:
        update_interval (int): The time delay for the scheduled update given
            as an int. This is required by the sched module and is the
            time the update must wait to be executed.
        update_name (str): The name of the update, given as a string. This is
            added as the value to the "event_name" key in the global
            dictionary, allowing for updates to be removed from the scheduler
            queue. The name can be used to find the ID, which is then used to
            remove the event from the queue.
        repeat (bool): A boolean value indicating whether or not the update is
            a repeating update or not. This is used to know whether or not to
            remove an update from the global list once it has expired.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Entering the schedule_covid_updates function as intended.")

    covid_scheduler.enter(update_interval, 1, covid_API_request,)
    covid_scheduler.run(blocking=False)

    # The newest item in the scheduler queue is the desired update to add
    queue_length = len(covid_scheduler.queue) - 1

    logging.info(f"Update: {covid_scheduler.queue[queue_length]} scheduled")

    update_to_add = {
                     'event_id': covid_scheduler.queue[queue_length],
                     'event_name': update_name,
                     'repeat_update': repeat}

    # The update is only added if it isn't already in the list.
    duplicate_tracker = False
    for update in covid_queue_info:
        if update_to_add == update:
            duplicate_tracker = True

    if duplicate_tracker is False:
        logging.info("Covid update added to global list of updates.")
        covid_queue_info.append(update_to_add)

    logging.debug("Exiting the schedule_covid_data function as intended.")
    return None


def remove_covid_data_update(removed_update_name: str, expired: bool) -> None:
    """Removes expired or manually removed updates from both the global
    list of updates and the queue of scheduled events.

    If an event has expired (indicated by the expired parameter being true)
    it is found in the global list of updates and removed (automatically
    removed from the list and the queue of scheduled events). Otherwise, the
    update has been manually removed, with the same happening above. On top
    of this, a variable is assigned to the value of the 'event_id' key for
    the update, this is then used to locate the value in the queue of events,
    and consequently remove it from said queue of events.

    Args:
        removed_update_name (str): The name of the update to be removed, given
            as a string. This is used to find the update and remove it from
            the global list and the queue of scheduled events.
        expired (bool): A boolean value indicating whether or not the given
            update has expired or not. This is used to determine if the update
            needs to be removed from both queues or just the global list.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Entering the remove_covid_data_update function.")
    # If an event has expired, this loop goes through the list.
    # (Of dictionaries) holding the scheduled events and removes it.
    if expired is True:
        for update in covid_queue_info:
            if update['event_name'] == removed_update_name:
                logging.info("Expired update removed as intended.")
                covid_queue_info.remove(update)

    # Iterates through the global list of events, if the removed event.
    # Is in the global list, it is removed from the queue and the list.
    for update in covid_queue_info:
        if update['event_name'] == removed_update_name:
            event_to_remove = update['event_id']

            # If the event has not expired it must be in (and removed from).
            # Both the global list and the queue.
            covid_queue_info.remove(update)

            # Used to catch repeats that are no longer in the update queue.
            try:
                covid_scheduler.cancel(event_to_remove)
                logging.info("Update removed as intended.")
            except ValueError:
                logging.warning("Repeat update not in queue removed.")

    logging.debug("Exiting the remove_covid_data_update function.")

    return None


# Getter and Setter functions for the COVID data.
def set_covid_data(england_dict: dict, local_dict: dict) -> None:
    """A setter function that sets the global lists that hold national and
    local data to the passed in parameters from the process_covid_json_data
    function. This enables the global dictionaries to be updated and returned
    to the main program.

    Args:
        england_dict (dict): A dictionary holding updated COVID data for
            England, given as a dictionary. This is used to set the global
            dictionary for national COVID data to an up-to-date value.
        local_dict (dict): A dictionary holding updated COVID data for given
            local area, given as a dictionary. This is used for the same
            reason as above, but for local data in place of national data.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """
    logging.debug("Entering the set_covid_data function.")
    global england_data, local_data

    england_data = england_dict
    local_data = local_dict
    logging.info("Global variables set as intended.")

    logging.debug("Exiting the set_covid_data function.")

    return None


def return_covid_data() -> tuple[dict, dict]:
    """A function that acts as a getter method, allowing for functions in main
    to get the national and local COVID data and then display the values on
    the dashboard.

    Returns:
        tuple: (england_data, local_data). A tuple of two values (England and
            local COVID data), this allows two values to be returned at once,
            and removes the need for excessive API calls, as the current
            national and local COVID data can be returned without needing to
            make another API call.
    """
    logging.debug("Entering and exiting the return_covid_data function.")
    logging.info(f"{(england_data, local_data)} returned")
    return (england_data, local_data)


# Testing functions:
def test_covid_API_request(eng_data: list, loc_data: list) -> None:
    """Tests the covid_API_request function during execution by checking
    whether or not the API returns data, and if that data is sufficient.
    If it isn't (at both the national and local level) SystemExit errors
    are raised.

    Args:
        eng_data (list): A list of dictionaries of the national COVID data
            returned by the API call. This is checked to ensure the program
            can continue as intended.
        loc_data (list): A list of dictionaries of the local COVID data
            returned by the API call. This is checked to ensure the program
            can continue as intended.

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """

    # Checks the national data for sufficiency.
    if eng_data is None:
        logging.error("No data returned for national COVID API call.")
        raise SystemExit
    else:
        if eng_data['data'] is None:
            logging.info("Data returned by API.")
            logging.warning("No national covid data in API data.")
            raise SystemExit

    # Checks the local data for sufficiency.
    if loc_data is None:
        logging.error("No data returned for local COVID API call.")
        raise SystemExit
    else:
        logging.info("Data returned by API.")
        if loc_data['data'] is None:
            logging.warning("No local covid data in API data.")
            raise SystemExit
    
    return None


def test_schedule_covid_updates() -> None:
    """Sentence

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """


def test_remove_covid_data_update() -> None:
    """Sentence

    Returns:
        None: Global variables are the only thing altered during the execution
            of the function, so nothing needs to be returned.
    """


# Beyond the specification.
def comma_separator(value_to_separate: str) -> str:
    """Adds commas after every three values in a number.

    Moves backwards through the string, adding each number to the number
    to be returned, once the counter is a multiple of three, a comma is
    added (done to increase readability of the dashboard). Once the end
    of the number has been reached, string slicing is used to reverse its
    order (put it back in the correct order).

    Args:
        value_to_separate (str): The number to add the commas to, given as
            a string to make it easier to manipulate and add the commas to.

    Returns:
        str: return_value. The string of the number (with commas now) to be
        returned back to the process_covid_json_data function. This allows for
        the comma separated number to be displayed on the dashboard.
    """
    logging.debug("Entering the comma_separator function.")
    # Counter is used to ensure commas are only added every three numbers.
    return_value = ''
    counter = 1
    value_to_separate = str(value_to_separate)

    # Moves from the end to the start of the number, adding a comma.
    # After every three digits.
    for digit in range(len(value_to_separate) - 1, -1, -1):
        return_value = return_value + value_to_separate[digit]

        # Once the third digit has been added, so is a comma.
        if counter % 3 == 0:
            if counter == len(value_to_separate):
                continue

            return_value = return_value + ','

        counter += 1

    return_value = return_value[-1::-1]

    logging.info(f"{return_value} returned.")
    logging.debug("Exiting the comma_separator function.")

    return return_value
