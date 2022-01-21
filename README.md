# COVID_Dashboard_ECM1400
A Covid dashboard that displays current Covid data (UK and locally), along with news articles that contain COVID keywords in the headline.
Additionally, scheduled updates can be made to the Covid data and news articles.

## Prerequisites and Installation
For this project to work, the following dependencies need to be installed:

    - NewsApi to fetch the news articles, done via pip3 install newsapi-python.
        - You can sign up to NewsApi here: https://newsapi.org, and find more documentation about NewsAPI.

    - PHE COVID API to fetch the covid data, done via pip3 install uk-covid19.
        - You can find out more about the PHE COVID API here: 

    - Flask to display and manipulate the webpage, done via pip3 install flask.

    - The Requests module to get data from URLs and effectively use Flask, done via pip3 install requests.

To install this on mac (with python 3.6 or up already installed) enter:
    - pip3 install -i https://test.pypi.org/simple/ECM1400-COVID-Dashboard-Programming-Project-BenjaminTheron.

To install this on windows/ linux enter:
    - pip install -i https://test.pypi.org/simple/ECM1400-COVID-Dashboard-Programming-Project-BenjaminTheron.

Additionally, the source code for this project can be installed by entering the source URL into a 
web browser, scrolling down, clicking on the download files tab and clicking on the filename
that ends in .tar.gz.

## Project Tutorial
Before running the project, a NewsAPI API key needs to be entered into the config.json file in both the main
module (found by navigating to src/covid_dashboard_pkg, from the ECM1400_COVID_Dashboard_Programming_Project_BenjaminTheron then changing the config.json found there)
and the test module (found by doing the same as prior but going further to src/covid_dashboard_pkg/tests and then
changing the config.json found there) - if you want to use pytest to carry out testing. While in the config file,
you can change a vast multitude of variables including: location; news queries; news langauge and many, many
more. Note, it is worth going into the config file and looking at all these variables and tuning them to your
liking.

Now that the API key has been added, head to a terminal, navigate to covid_dashboard_pkg and run the command
python(3 if you're on mac) main.py. Now, head to a web browser, enter http://127.0.0.1:5000 into the URL
and press enter.

The main dashboard should now be displayed on screen. To remove news articles on the right side of the screen,
all you need to do is press the cross in the top right corner of the respective news widget. 

To schedule updates to covid data and news articles, enter a time (24hr format), name, what data you would like
to update (covid, news or both), along with if you want the update to repeat daily and press enter. To remove this
update, much akin to the news articles, just press the cross in the top right corner.

## Testing
Using a terminal and navigating to the tests folder 
(ECM1400_COVID_Dashboard_Programming_Project_BenjaminTheron/src/covid_dashboard_pkg/tests), and running the pytest
command, will execute 15 unit tests. These test the individual functionality of the functions and should come back
as passed. Note each these tests can be extended and more tests can be added (add to the test file and title them
with test_function_name to work with pytest).

Additionally, the remaining functions have test functions built into the modules that perpetually check they
are working as intended, as the function is running.

### Developer Documentation
The main.py module includes everything related to displaying the dashboard and coordinating all the other modules.

The covid_data_handler.py module contains all the COVID data handling functionality, this includes making the API 
call, processing the API call, scheduling updates, removing updates, setting and returning COVID data.

The covid_news_handling.py module contains all the news data functionality, this includes: making the API
request; processing the articles returned by the API request; scheduling news updates; removing news update;
removing the news articles from the screen; limiting the number of articles displayed on screen and
returning the articles to the main program.

If you're looking to change the program, start by looking at each respective function inside the respective
module before moving to main.py, which links them all together/ to the displayed dashboard.

### Notes
Some of the test functions at the bottom of some of the modules are 'empty' no functionality out as I ran out of time to
implement them. This is an area I can come back to afterwards to polish off the project.

Additionally there are a number of ways to extend the project:

    - Limit the number of scheduled updates.
    - Add a way for updates with no entered time to expire.
    - Re-format the text displayed for each update.
    - Restore updates from previous sessions by parsing through the log file.
    - A way to clear the log file after it reaches a certain length.

## Details

#### Authors
Benjamin Theron

#### License
MIT License

#### Link to source
https://test.pypi.org/project/ECM1400-COVID-Dashboard-Programming-Project-BenjaminTheron/
