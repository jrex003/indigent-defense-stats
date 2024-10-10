import unittest, sys, os, json, warnings, requests, logging
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from unittest.mock import mock_open, patch, call

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import all of the programs modules within the parent_dir
from scraper  import Scraper
from parser  import Parser
from cleaner  import Cleaner
from updater  import Updater

SKIP_SLOW = os.getenv('SKIP_SLOW', 'false').lower().strip() == 'true'

def log(message, level='INFO'): # Provide message and info level (optional, defaulting to info)
    # configure the logger
    log = logging.getLogger(name="pid: " + str(os.getpid()))
    logging.basicConfig()
    logging.root.setLevel(level=level)
    log.info(message)

class ScraperTestCase(unittest.TestCase):
    # Defaults for each program are set at the function level.

    def test_scrape_get_ody_link(self,
                                 county = 'hays'):
        scraper_instance = Scraper()
        logger = scraper_instance.configure_logger()
        county = scraper_instance.format_county(county)
        base_url = scraper_instance.get_ody_link('hays', logger)
        self.assertIsNotNone(base_url, "No URL found for this county.")
        
    def test_scrape_main_page(self, 
                              base_url = r'http://public.co.hays.tx.us/', 
                              odyssey_version = 2003, 
                              notes = '',
                              ms_wait= None, 
                              start_date = None, 
                              end_date = None, 
                              court_calendar_link_text = None, 
                              case_number = None
                              ):
        scraper_instance = Scraper()
        logger = scraper_instance.configure_logger()
        ms_wait, start_date, end_date, court_calendar_link_text, case_number = scraper_instance.set_defaults(ms_wait, start_date, end_date, court_calendar_link_text, case_number)
        session = scraper_instance.create_session()
        main_page_html, main_soup = scraper_instance.scrape_main_page(base_url, odyssey_version, session, notes, logger, ms_wait)
        self.assertIsNotNone(main_page_html, "No main page HTML came through. main_page_html = None.")
        self.assertTrue('ssSearchHyperlink' in main_page_html, "There is no 'ssSearchHyperlink' text found in this main page html.") # Note: This validation is already being done using the 'verification_text' field.
        self.assertTrue('Hays County Courts Records Inquiry' in main_page_html, "There is no 'Hays County Courts Records Inquiry' listed in this Hays County main page HTML.")

    def test_scrape_search_page(self, 
                                base_url=r'http://public.co.hays.tx.us/', 
                                odyssey_version = 2003,
                                main_page_html=None, 
                                main_soup=None,
                                session = None, 
                                logger = None, 
                                ms_wait = None, 
                                court_calendar_link_text = None,
                                start_date = None, 
                                end_date = None,
                                case_number = None):
        # Open the mocked main page HTML
        with open(
            os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files','hays_main_page.html'), "r", encoding='utf-8'
        ) as file_handle:
            main_page_html = file_handle.read()  # Read the entire file content into a string
        # Parse the HTML content with BeautifulSoup
        main_soup = BeautifulSoup(main_page_html, "html.parser")
        # Look for the court calendar link
        scraper_instance = Scraper()
        logger = scraper_instance.configure_logger()
        ms_wait, start_date, end_date, court_calendar_link_text, case_number = scraper_instance.set_defaults(ms_wait, start_date, end_date, court_calendar_link_text, case_number)
        session = scraper_instance.create_session()
        search_url, search_page_html, search_soup = scraper_instance.scrape_search_page(base_url, odyssey_version, main_page_html, main_soup, session, logger, ms_wait, court_calendar_link_text)
        # Verify the court calendar link
        self.assertIsNotNone(main_page_html, "No search url came through. search_url = None.")
        self.assertTrue(search_url == r'http://public.co.hays.tx.us/Search.aspx?ID=900', "The link was not properly parsed from the test main page HTML.")
        self.assertIsNotNone(search_page_html, "No search HTML came through. search_page_html = None.")
        self.assertIsNotNone(search_soup, "No search HTML parsed into beautiful soup came through. search_soup = None.")
        # Verify the html or soup of the search page -- need to write more validation here: What do I want to know about it?
        # self.assertTrue(??????, ??????)
        
    def test_get_hidden_values(self, 
                            odyssey_version = 2003, 
                            main_soup = None,
                            search_soup = None,
                            logger = None, 
                            ms_wait = None, 
                            court_calendar_link_text = None,
                            start_date = None, 
                            end_date = None,
                            case_number = None):        
        # Open the mocked main page HTML
        with open(
            os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files','hays_main_page.html'), "r", encoding='utf-8'
        ) as file_handle:
            main_page_html = file_handle.read()  # Read the entire file content into a string
        # Parse the HTML content with BeautifulSoup
        main_soup = BeautifulSoup(main_page_html, "html.parser")

        # Open the mocked search page HTML
        with open(
            os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files','hays_search_page.html'), "r", encoding='utf-8'
        ) as file_handle:
            search_page_html = file_handle.read()  # Read the entire file content into a string
        # Parse the HTML content with BeautifulSoup
        search_soup = BeautifulSoup(search_page_html, "html.parser")
        
        #Run the function
        scraper_instance = Scraper()
        logger = scraper_instance.configure_logger()
        ms_wait, start_date, end_date, court_calendar_link_text, case_number = scraper_instance.set_defaults(ms_wait, start_date, end_date, court_calendar_link_text, case_number)
        hidden_values = scraper_instance.get_hidden_values(odyssey_version, main_soup, search_soup, logger)
        self.assertIsNotNone(hidden_values, "No hidden values came through. hidden_values = None.")
        self.assertTrue(type(hidden_values) == dict, "The hidden values fields is not a dictionary but it needs to be.")

    # Note: This doesn't run the scrape function directly the way the others do. The scrape function requires other functions to run first to populate variables in the class name space first.
    def test_scrape_individual_case(self,
                                    base_url = None,
                                    search_url = None, 
                                    hidden_values = None, 
                                    case_number = 'CR-16-0002-A',
                                    county = 'hays',
                                    judicial_officers = [], 
                                    ms_wait = None, 
                                    start_date = None, 
                                    end_date = None, 
                                    court_calendar_link_text = None,
                                    case_html_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files', 'test_data', 'hays', "case_html")
                                    ):
        # This starts a timer to compare the run start time to the last updated time of the resulting HTML to ensure the HTML was created after run start time
        now = datetime.now()

        # makes the test directory
        os.makedirs(case_html_path, exist_ok=True)

        # Call the functions being tested. In this case, the functions being called are all of the subfunctions required and effectively replicates the shape of scrape.
        scraper_instance = Scraper()
        ms_wait, start_date, end_date, court_calendar_link_text, case_number = scraper_instance.set_defaults(ms_wait, start_date, end_date, court_calendar_link_text, case_number)
        logger = scraper_instance.configure_logger()
        county = scraper_instance.format_county(county)
        session = scraper_instance.create_session()
        case_html_path = scraper_instance.make_directories(county) if not case_html_path else case_html_path
        base_url, odyssey_version, notes = scraper_instance.get_ody_link(county, logger)
        main_page_html, main_soup = scraper_instance.scrape_main_page(base_url, odyssey_version, session, notes, logger, ms_wait)
        search_url, search_page_html, search_soup = scraper_instance.scrape_search_page(base_url, odyssey_version, main_page_html, main_soup, session, logger, ms_wait, court_calendar_link_text)
        hidden_values = scraper_instance.get_hidden_values(odyssey_version, main_soup, search_soup, logger)
        scraper_instance.scrape_individual_case(base_url, search_url, hidden_values, case_number, case_html_path, session, logger, ms_wait)

        # Test #1: Did the scraper create a new file called 12947592.html in the right location?
        # this creates the file path, checks to see if the HTML file is there, and then checks to see that HTML file has been updated since the program started running.
        test_case_html_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files','test_data','hays','case_html','12947592.html')
        self.assertTrue(os.path.isfile(test_case_html_path), "There is no HTML file the correct name in the correct folder.")
            # this gets the time the file was last updated and converts it from unix integer to date time
        test_html_updated_time = os.path.getmtime(test_case_html_path)
        seconds = int(test_html_updated_time)
        microseconds = int((test_html_updated_time - seconds) * 1e6)
        test_html_updated_time = datetime.fromtimestamp(seconds) + timedelta(microseconds=microseconds)
        self.assertTrue(test_html_updated_time > now, "This HTML has not been updated since this test started running.")

        # Test #2: Is the resulting HTML file longer than 1000 characters?
        with open(test_case_html_path, "r") as file_handle:
            case_soup = BeautifulSoup(file_handle, "html.parser", from_encoding="UTF-8")   
        self.assertTrue(len(case_soup.text) > 1000, "This HTML is smaller than 1000 characters and may be an error.")

        # Test #3: Does the resulting HTML file container the cause number in the expected header location?
        self.assertTrue(test_html_updated_time > now)
        # Parse the HTML in the expected location for the cause number.
        case_number_html = case_soup.select('div[class="ssCaseDetailCaseNbr"] > span')[0].text
        self.assertTrue(case_number_html=='CR-16-0002-A', "The cause number is not where it was expected to be in the HTML.")
        #self.logger.info(f"Scraper test sucessful for cause number CR-16-0002-A.")

    # This begins the tests related the scrape_cases function for scraping multiple cases.

    def test_scrape_jo_list(self, 
                            base_url = r'http://public.co.hays.tx.us/',
                            odyssey_version = 2003, 
                            notes = '',
                            search_soup = None, 
                            judicial_officers = None,
                            ms_wait = None, 
                            start_date = None, 
                            end_date = None, 
                            court_calendar_link_text = None, 
                            case_number = None,
                            county = 'hays',
                            session = None,
                            logger = None,
                            ):
        # This test requires that certain dependency functions run first.
        scraper_instance = Scraper()
        ms_wait, start_date, end_date, court_calendar_link_text, case_number = scraper_instance.set_defaults(ms_wait, start_date, end_date, court_calendar_link_text, case_number)
        logger = scraper_instance.configure_logger()
        county = scraper_instance.format_county(county)
        session = scraper_instance.create_session()
        main_page_html, main_soup = scraper_instance.scrape_main_page(base_url, odyssey_version, session, notes, logger, ms_wait)
        search_url, search_page_html, search_soup = scraper_instance.scrape_search_page(base_url, odyssey_version, main_page_html, main_soup, session, logger, ms_wait, court_calendar_link_text)
        judicial_officers, judicial_officer_to_ID = scraper_instance.scrape_jo_list(odyssey_version, search_soup, judicial_officers, logger)
        log(f'Number of judicial officers found: {len(judicial_officers)}')
        self.assertIsNotNone(judicial_officers, "No judicial officers came through. judicial_officers = None.")
        self.assertTrue(type(judicial_officers)==list, "The judicial_officers variable is not a list but it should be.")
        self.assertIsNotNone(judicial_officer_to_ID, "No judicial officers IDs came through. judicial_officers_to_ID = None.")
        self.assertTrue(type(judicial_officer_to_ID)==dict, "The judicial_officers_to_ID variable is not a dictionary but it should be.")

    def test_scrape_results_page(self, 
                                 odyssey_version = 2003, 
                                 county = 'hays',
                                 base_url = r'http://public.co.hays.tx.us/', 
                                 search_url = r'http://public.co.hays.tx.us/Search.aspx?ID=900', 
                                 hidden_values = None, 
                                 JO_id = '39607', # 'Boyer, Bruce'
                                 date_string = '07-01-2024',
                                 notes = '',
                                 ms_wait = None, 
                                 start_date = None, 
                                 end_date = None, 
                                 court_calendar_link_text = None, 
                                 case_number = None
                                 ):

        # Read in the test 'hidden values' that are necessary for searching a case
        with open(
            os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files','test_hidden_values.txt'), "r", encoding='utf-8'
        ) as file_handle:
            hidden_values = file_handle.read()  # Read the entire file content into a string        
        hidden_values = hidden_values.replace("'", "\"")
        hidden_values = json.loads(hidden_values)
        scraper_instance = Scraper()
        ms_wait, start_date, end_date, court_calendar_link_text, case_number = scraper_instance.set_defaults(ms_wait, start_date, end_date, court_calendar_link_text, case_number)
        logger = scraper_instance.configure_logger()
        county = scraper_instance.format_county(county)
        session = scraper_instance.create_session()
        # Open the example main page HTML
        with open(
            os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files','hays_main_page.html'), "r", encoding='utf-8'
        ) as file_handle:
            main_page_html = file_handle.read()  # Read the entire file content into a string
        # Parse the HTML content with BeautifulSoup
        main_soup = BeautifulSoup(main_page_html, "html.parser")

        # This test requires that certain dependency functions run first.
        search_url, search_page_html, search_soup = scraper_instance.scrape_search_page(base_url, odyssey_version, main_page_html, main_soup, session, logger, ms_wait, court_calendar_link_text)
        results_html, results_soup = scraper_instance.scrape_results_page(odyssey_version, base_url, search_url, hidden_values, JO_id, date_string, session, logger, ms_wait)
        self.assertIsNotNone(results_soup, "No results page HTML came through. results_soup = None.")
        self.assertTrue("Record Count" in results_html, "'Record Count' was not the results page HTML, but it should have been.") # Note: This is already validated by "verification_text" within the request_page_with_retry function.
        # TODO: Add more validation here of what one should expect from the results page HTML.

    # This unit test for scrape_cases also covers unit testing for scrape_case_data_pre2017 and scrape_case_data_post2017. Only one or the other is used, and scrape_cases is mostly the pre or post2017 code.
    # In the future unit tests could be written for:
        #def scrape_case_data_pre2017()
        #def scrape_case_data_post2017()

    @unittest.skipIf(SKIP_SLOW, "slow")
    def test_scrape_multiple_cases(self, 
                          county = 'hays',
                          odyssey_version = 2003, 
                          base_url = r'http://public.co.hays.tx.us/', 
                          search_url = r'https://public.co.hays.tx.us/Search.aspx?ID=900', 
                          hidden_values = None, 
                          judicial_officers = ['Boyer, Bruce'], 
                          judicial_officer_to_ID = {'Boyer, Bruce':'39607'},
                          JO_id = '39607',
                          date_string = '07-01-2024',
                          court_calendar_link_text = None,
                          case_number = None,
                          ms_wait = 200,
                          start_date = '2024-07-01',
                          end_date = '2024-07-01',
                          case_html_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files', 'test_data', 'hays', "case_html")
                          ):
        # This starts a timer to compare the run start time to the last updated time of the resulting HTML to ensure the HTML was created after run start time
        now = datetime.now()

        # makes the test directory
        os.makedirs(case_html_path, exist_ok=True)

        # Open the example main page HTML
        with open(
            os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files','hays_main_page.html'), "r", encoding='utf-8'
        ) as file_handle:
            main_page_html = file_handle.read()  # Read the entire file content into a string
        # Parse the HTML content with BeautifulSoup
        main_soup = BeautifulSoup(main_page_html, "html.parser")

        # Read in the test 'hidden values' that are necessary for searching a case
        with open(
            os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files','test_hidden_values.txt'), "r", encoding='utf-8'
        ) as file_handle:
            hidden_values = file_handle.read()  # Read the entire file content into a string        
        hidden_values = hidden_values.replace("'", "\"")
        hidden_values = json.loads(hidden_values)

        # There are some live depency functions that have to be run before the primary code can be run. 
        scraper_instance = Scraper()
        session = scraper_instance.create_session()
        ms_wait, start_date, end_date, court_calendar_link_text, case_number = scraper_instance.set_defaults(ms_wait, start_date, end_date, court_calendar_link_text, case_number)
        logger = scraper_instance.configure_logger()
        case_html_path = scraper_instance.make_directories(county) if not case_html_path else case_html_path
        search_url, search_page_html, search_soup = scraper_instance.scrape_search_page(base_url, odyssey_version, main_page_html, main_soup, session, logger, ms_wait, court_calendar_link_text)
        results_html, results_soup = scraper_instance.scrape_results_page(odyssey_version, base_url, search_url, hidden_values, JO_id, date_string, session, logger, ms_wait)
        scraper_instance.scrape_multiple_cases(county, odyssey_version, base_url, search_url, hidden_values, judicial_officers, judicial_officer_to_ID, case_html_path, logger, session, ms_wait, start_date, end_date)

        # Test #1: Did the scraper create a new file called test_12947592.html in the right location?
        #This creates the file path, checks to see if the HTML file is there, and then checks to see that HTML file has been updated since the program started running.
        test_case_html_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files','test_data','hays','case_html','12947592.html')
        self.assertTrue(os.path.isfile(test_case_html_path), "There is no HTML file the correct name in the correct folder.")
            #This gets the time the file was last updated and converts it from unix integer to date time
        test_html_updated_time = os.path.getmtime(test_case_html_path)
        seconds = int(test_html_updated_time)
        microseconds = int((test_html_updated_time - seconds) * 1e6)
        test_html_updated_time = datetime.fromtimestamp(seconds) + timedelta(microseconds=microseconds)
        self.assertTrue(test_html_updated_time > now, "This HTML has not been updated since this test started running.")

        # Test #2: Is the resulting HTML file longer than 1000 characters?
        with open(test_case_html_path, "r") as file_handle:
            case_soup = BeautifulSoup(file_handle, "html.parser", from_encoding="UTF-8")   
        self.assertTrue(len(case_soup.text) > 1000, "This HTML is smaller than 1000 characters and may be an error.")

        # Test #3: Does the resulting HTML file container the cause number in the expected header location?
        self.assertTrue(test_html_updated_time > now)
        # Parse the HTML in the expected location for the cause number.
        case_number_html = case_soup.select('div[class="ssCaseDetailCaseNbr"] > span')[0].text
        self.assertTrue(case_number_html=='CR-16-0002-A', "The cause number is not where it was expected to be in the HTML.")
        #self.logger.info(f"Scraper test sucessful for cause number CR-16-0002-A.")

class ParseTestCase(unittest.TestCase):

    def test_parser_defaults(self):
        now = datetime.now()
        now_string = now.strftime("%H:%M:%S")
        # Call the function being tested
        parser_instance = Parser()
        parser_instance.parse(county = 'hays', case_number = '51652356', test = True)

        # Test #1: Check to see if there is a JSON called 51652356.json created in the correct location and that it was updated since this test started running
        test_case_json_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files', 'test_data', 'hays', 'case_json', 'test_51652356.json')
        self.assertTrue(os.path.isfile(test_case_json_path), "There is no JSON file the correct name in the correct folder.")
        #This gets the time the file was last updated and converts it from unix integer to date time
        test_json_updated_time = os.path.getmtime(test_case_json_path)
        seconds = int(test_json_updated_time)
        microseconds = int((test_json_updated_time - seconds) * 1e6)
        test_json_updated_time = datetime.fromtimestamp(seconds) + timedelta(microseconds=microseconds)
        test_json_updated_time_string = test_json_updated_time.strftime("%H:%M:%S")
        self.assertTrue(test_json_updated_time > now, 'The JSON has not been updated since the program started running.')

        # Test #2: Check to see that JSON parsed all of the necessary fields and did so properly. 
        #Run the json against the field validation database
        def validate_field(field):
            
            # This locates where a field should be in the JSON based on its logical level (top level, charge level, party level, etc.) 
            def field_locator(logical_level):
                if logical_level == 'top':
                    location = json_dict
                elif logical_level == 'party':
                    location = json_dict['party information']
                elif logical_level == 'charge': # This only looks at the first charge in the JSON
                    location = json_dict['charge information'][0]
                return location
            
            def check_exists(field_name, logical_level, importance):
                location = field_locator(logical_level)
                # Check for the field in the expected location: Raise error if not present if field 'necessary' but only raise warning otherwise
                if importance == 'necessary':
                    message = f"The '{field_name}' field has '{importance}' importance but is missing."
                    self.assertTrue(field_name in location, message)
                if importance == 'high' or importance == 'medium':
                    if field_name not in location:
                        message = f"The '{field_name}' field has {importance} importance but is missing."
                        warnings.warn(message, UserWarning)
                if importance == 'low':
                    # Don't bother checking.
                    pass

            def check_length(field_name, logical_level, importance, estimated_min_length):
                location = field_locator(logical_level)
                #Gets the length of the field and the field's text using the dynamic location.
                field_text = location[field_name]
                field_length = len(field_text)
                # Check for the expected length of the field: Raise error if too short if field 'necessary' but only raise warning otherwise
                if importance == 'necessary':
                    message = f"This necessary field called '{field_name}' was expected to be more than {estimated_min_length} but it is actually {field_length}: {field_text}."
                    self.assertFalse(field_length < estimated_min_length, message)
                if importance == 'high' or importance == 'medium':
                    message = f"The '{field_name}' field has an estimated minimum length of {estimated_min_length} characters, but it instead has {field_length} characters. {importance}"
                    if field_length < estimated_min_length:
                        warnings.warn(message, UserWarning)
                if importance == 'low':
                    #Don't bother checking.
                    pass

            check_exists(
                field_name = field['name'],
                logical_level = field['logical_level'],
                importance = field['importance'])
            
            check_length(
                field_name = field['name'], 
                logical_level = field['logical_level'],
                importance = field['importance'],
                estimated_min_length = field['estimated_min_length'])

        #Opening the test json
        with open(test_case_json_path, "r") as f:
            json_dict = json.load(f)

        #Opening the field validation json with expected fields and their features 
        FIELDS_VALIDATION_DICT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "resources", 'test_files', 'field_validation_list.json')
        with open(FIELDS_VALIDATION_DICT_PATH, "r") as f:
            FIELDS_VALIDATION_DICT = json.load(f)

        for field in FIELDS_VALIDATION_DICT:
            log(f"validating field: {field['name']}")
            validate_field(field)
        log(f'Field validation complete for {len(FIELDS_VALIDATION_DICT)} fields.')

class CleanTestCase(unittest.TestCase):

    def setUp(self):
        self.cleaner = Cleaner() # Create Cleaner instance here to avoid repeating this in every test

    # Create mock functions
    @patch('os.makedirs') 
    @patch('os.path.exists', return_value=False)
    def test_get_or_create_folder_path(self, mock_exists, mock_makedirs):
        mock_exists.return_value = False
        county = "hays"
        folder_type = "case_json"
        expected_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "hays", "case_json")

        folder_path = self.cleaner.get_or_create_folder_path(county, folder_type)

        mock_exists.assert_called_once_with(expected_path)  # Check if os.path.exists was called
        mock_makedirs.assert_called_once_with(expected_path)  # Check if os.makedirs was called
        self.assertEqual(folder_path, expected_path)  # Check that the path is correct

        # Test when folder already exists
        mock_exists.return_value = True
        folder_path = self.cleaner.get_or_create_folder_path(county, folder_type)
        mock_makedirs.assert_called_once() # Should not be called again

    def test_load_json_file(self):
        # Test successful load
        with patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}'):
            result = self.cleaner.load_json_file("fake_path.json")
            self.assertEqual(result, {"key": "value"})

        # Test file not found
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = self.cleaner.load_json_file("nonexistent.json")
            self.assertEqual(result, {})
        
        # Test invalid JSON
        with patch("builtins.open", new_callable=mock_open, read_data='invalid json'):
            result = self.cleaner.load_json_file("invalid.json")
            self.assertEqual(result, {})

    @patch("builtins.open", new_callable=mock_open, read_data = '[{"charge_name": "Charge1", "details": "Some details"}]')
    def test_load_and_map_charge_names(self, mock_file):
        file_path = "fake_path.json"
        result = self.cleaner.load_and_map_charge_names(file_path)

        self.assertEqual(result, {"Charge1": {"charge_name": "Charge1", "details": "Some details"}})
        mock_file.assert_called_once_with(file_path, "r")

    def test_hash_defense_attorney(self):
        input_data = {
            "party information": {
                "defense attorney": "John Doe",
                "defense attorney phone number": "555-1234"
            }
        }
        result = self.cleaner.hash_defense_attorney(input_data)
        # Check that the defense_attorney field is hashed
        self.assertNotEqual(result,"John Doe:555-1234")  # Ensure it's hashed
        self.assertIsInstance(result, str)  # Check if the hash is a string
    
        # Ensure same input gives the same hash
        input_data2 = {
            "party information": {
                "defense attorney": "John Doe",
                "defense attorney phone number": "555-1234"
            }
        }
        result2 = self.cleaner.hash_defense_attorney(input_data2)
        self.assertEqual(result, result2)

        # Ensure different input gives a different hash
        input_data3 = {
            "party information": {
                "defense attorney": "Jane Doe",
                "defense attorney phone number": "555-1234"
            }
        }
        result3 = self.cleaner.hash_defense_attorney(input_data3)
        self.assertNotEqual(result, result3)

    def test_process_charges(self):
        charges = [
            {"level": "Misdemeanor", "charges": "Charge1", "statute": "123", "date": "12/01/2023"},
        ]
        charge_mapping = {"Charge1": {"mapped_field": "mapped_value"}}

        processed_charges, earliest_date = self.cleaner.process_charges(charges, charge_mapping)
    
        self.assertEqual(len(processed_charges), 1)
        self.assertEqual(processed_charges[0]['charge_date'], "2023-12-01")
        self.assertEqual(earliest_date, "2023-12-01")
    
    def test_contains_good_motion(self):
        self.assertTrue(self.cleaner.contains_good_motion("Motion To Suppress", "Event: Motion To Suppress"))
        self.assertTrue(self.cleaner.contains_good_motion("Motion To Suppress", ["Other", "Motion To Suppress"]))
        self.assertFalse(self.cleaner.contains_good_motion("Motion To Suppress", "Other Motion"))
        self.assertFalse(self.cleaner.contains_good_motion("Motion To Suppress", ["Other1", "Other2"]))

    def test_find_good_motions(self):
        case_data = [
            "Motion To Suppress", 
            "Motion to Reduce Bond", 
            "Other Event",
            "Motion for Speedy Trial"
        ]

        result = self.cleaner.find_good_motions(case_data)
        self.assertEqual(len(result), 3)
        self.assertEqual(result, ["Motion To Suppress", "Motion to Reduce Bond", "Motion for Speedy Trial"])

    @patch("cleaner.Cleaner.load_json_file")
    @patch("cleaner.Cleaner.write_json_output")
    def test_process_single_case(self, mock_write, mock_load):
        mock_load.return_value = {
            "code": "123",
            "party information": {
                "defense attorney": "John Doe",
                "defense attorney phone number": "555-1234"
            },
            "charge information": [
                {"level": "Misdemeanor", "charges": "Charge1", "statute": "123", "date": "12/01/2023"}
            ],
            "other events and hearings": ["Motion To Suppress"]
        }

        county = "test_county"
        folder_path = "case_json_folder"
        case_file = "case1.json"

        self.cleaner.process_single_case(county, folder_path, case_file)

        mock_load.assert_called_once()
        mock_write.assert_called_once()

        # Check that the output contains expected fields
        output_data = mock_write.call_args[0][1]
        self.assertIn("case_number", output_data)
        self.assertIn("charges", output_data)
        self.assertIn("motions", output_data)
        self.assertIn("defense_attorney", output_data)

    @patch("os.listdir", return_value=["case1.json", "case2.json"])
    @patch("cleaner.Cleaner.process_single_case")
    def test_process_json_files(self, mock_process, mock_listdir):
        county = "test_county"
        folder_path = "case_json_folder"

        self.cleaner.process_json_files(county, folder_path)

        self.assertEqual(mock_process.call_count, 2)
        mock_process.assert_any_call(county, folder_path, "case1.json")
        mock_process.assert_any_call(county, folder_path, "case2.json")

    @patch("builtins.open", new_callable=mock_open)
    def test_write_json_output(self, mock_file):
        file_path = "test_output.json"
        data = {"key": "value"}
        self.cleaner.write_json_output(file_path, data)

        mock_file.assert_called_once_with(file_path, "w") # Checks mocked open function was called with the correct arguments
        mock_file().write.assert_called_once_with(json.dumps(data)) # Checks that the write method was called with the json-encoded version of the data dict

    def test_clean(self):
        county = "hays"

        with patch.object(Cleaner, 'get_or_create_folder_path', return_value = "mock_path") as mock_get_folder, \
            patch.object(Cleaner, 'process_json_files') as mock_process_json_files, \
            patch('logging.info') as mock_logging_info, \
            patch('logging.error') as mock_logging_error:

            self.cleaner.clean(county)

        # Check that get_or_create_folder_path is called once with correct args
            mock_get_folder.assert_called_once_with(county, "case_json")

        # Check that process_json_files is called once with correct args
            mock_process_json_files.assert_called_once_with(county, "mock_path")

        # Check that the logging for info was called twice (start and end)
            mock_logging_info.assert_has_calls([
                call(f"Processing data for county: {county}"),
                call(f"Completed processing for county: {county}")
            ])

        # Check that error logging wasn't called
            mock_logging_error.assert_not_called()

        # Test exception handling
        with patch.object(Cleaner, 'get_or_create_folder_path', side_effect = Exception("Test error")) as mock_get_folder, \
            patch('logging.error') as mock_logging_error:

        # Call the method, this time expecting an exception to be raised
            self.cleaner.clean(county)

        # Ensure logging.error is called with the exception message
            mock_logging_error.assert_called_once_with(f"Error during cleaning process for county: {county}. Error: Test error")