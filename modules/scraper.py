from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common import exceptions

from modules import file_io
import re


class Scraper(object):
    """Able to start up a browser, to authenticate to Instagram and get
    followers and people following a specific user.
    Hint:
        verbose 0: Not print, 1: print, 2: print and output
    """

    def __init__(self, verbose=0):
        # Set chrome to English language
        options = webdriver.ChromeOptions()
        options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
        # Need chromedriver with main.py in same directory
        self.driver = webdriver.Chrome(options=options)

        # 0: Not print, 1: print, 2: print and output
        self.verbose = verbose

    def close(self):
        """Close the browser."""
        self.driver.close()

    def authenticate(self, username, password):
        """Log in to Instagram with the provided credentials."""
        url = 'https://www.instagram.com/'
        file_io.write_to_log(self.verbose, '\nLogging in…')
        # Navigating to Instagram
        self.driver.get(url)

        # Wait web until find username
        WebDriverWait(self.driver, 30).until(expected_conditions.presence_of_element_located((By.NAME, 'username')))

        # Find input
        username_input = self.driver.find_elements_by_name('username')[0]
        password_input = self.driver.find_elements_by_name('password')[0]
        file_io.write_to_log(self.verbose, "Inputing username and password...")

        # Enter username and password
        username_input.send_keys(username)
        password_input.send_keys(password)

        # Wait until find login button
        login_x_path = '//*[@id="loginForm"]/div/div[3]/button/div'
        WebDriverWait(self.driver, 30).until(
            expected_conditions.presence_of_element_located((By.XPATH, login_x_path)))
        # Find login button
        login_click = self.driver.find_elements_by_xpath(login_x_path)[0]
        login_click.click()

        # Don't save Login info
        info_x_path = '//*[@id="react-root"]/section/main/div/div/div/div/button'
        WebDriverWait(self.driver, 30).until(
            expected_conditions.presence_of_element_located((By.XPATH, info_x_path)))
        info_click = self.driver.find_elements_by_xpath(info_x_path)[0]
        file_io.write_to_log(self.verbose, "don't save login info...")
        info_click.click()

        # Don't open notification
        # Sometimes notification x path will change, so use try except to handle
        try:
            notification_x_path = '/html/body/div[4]/div/div/div/div[3]/button[2]'
            WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located((By.XPATH, notification_x_path)))
            notification_click = self.driver.find_elements_by_xpath(notification_x_path)[0]
            notification_click.click()
        except exceptions.TimeoutException:
            notification_x_path = '/html/body/div[5]/div/div/div/div[3]/button[2]'
            WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located((By.XPATH, notification_x_path)))
            notification_click = self.driver.find_elements_by_xpath(notification_x_path)[0]
            notification_click.click()
        file_io.write_to_log(self.verbose, "don't turn on notifications...")

        file_io.write_to_log(self.verbose, "Log in success")

    def get_users(self, target, group):
        # Navigate
        self._navigate(target)

        # Get expected number
        expected_number = self._get_expected_number(group)

        # Store all expected users
        expected_list = []
        # if private then return
        if self._is_private():
            file_io.write_to_log(self.verbose, "%s is private" % target)
            return expected_number, expected_list

        # if verified then return
        if self._is_verified():
            file_io.write_to_log(self.verbose, "%s is verified" % target)
            return expected_number, expected_list

        # Get expected link
        expected_link = self._get_link(group)

        # Open users dialog
        expected_link.click()

        # Implicit Waits - Wait for 1 second
        self.driver.implicitly_wait(5)

        # Find users container
        users_list_container = self.driver.find_element_by_xpath(
            '//div[@role="dialog"]//ul/parent::div'
        )

        # Get all the lists item included in container
        users_list = users_list_container.find_elements_by_xpath('ul//li')

        # Initialize parameters
        last_user_index = 0
        retry = 2
        initial_scrolling_speed = 5

        # While there are more users scroll and save the results
        while users_list[last_user_index] is not users_list[-1] or retry > 0:
            self._scroll(users_list_container, initial_scrolling_speed)

            for index, user in enumerate(users_list):
                if index < last_user_index:
                    continue

                try:
                    link_to_user = user.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    last_user_index = index
                    if link_to_user not in expected_list:
                        expected_list.append(link_to_user)
                        file_io.write_to_log(self.verbose,
                            '{0:.2f}% {1:s}'.format(
                                round(index / expected_number * 100, 2),
                                link_to_user
                            )
                        )
                except:
                    if initial_scrolling_speed > 1:
                        initial_scrolling_speed -= 1
                    pass

            # Update users list
            users_list = users_list_container.find_elements(By.XPATH, 'ul//li')
            if users_list[last_user_index] is users_list[-1]:
                retry -= 1

        file_io.write_to_log(self.verbose, '100% Complete')
        return expected_number, expected_list

    def _navigate(self, target):
        file_io.write_to_log(self.verbose, '\nNavigating to %s profile…' % target)
        self.driver.get('https://www.instagram.com/{}/'.format(target))

    def _get_expected_number(self, group):
        scale = 1
        scale_dict = {'': 1, 'k': 1000, 'm': 1000000}
        regex = '(\d*\.\d+|\d+)(\w?)' # fit like 2000, 2.1k, 200M
        if group == 'followers':
            match = re.search(regex + ' followers', self.driver.page_source.lower())
            expected_str = match.group(1)
            scale = scale_dict[match.group(2)]
        elif group == 'following':
            match = re.search(regex + ' following', self.driver.page_source.lower())
            expected_str = match.group(1)
            scale = scale_dict[match.group(2)]
        else:
            file_io.write_to_log(self.verbose, 'Unexpected group')
            expected_str = -1

        return int(float(expected_str) * scale)

    def _get_link(self, group):
        """Return the element linking to the users list dialog."""
        try:
            if self._is_private():
                return ""

            file_io.write_to_log(self.verbose, '\nTry to get %s link' % group)
            return WebDriverWait(self.driver, 5).until(
                expected_conditions.presence_of_element_located((By.PARTIAL_LINK_TEXT, group))
            )
        except exceptions.TimeoutException:
            return ""

    def _is_private(self):
        """Return true or false if user is private"""
        return self.driver.page_source.find("This Account is Private") > -1

    def _is_verified(self):
        """Return true or false if user is verified"""
        return self.driver.page_source.find("Verified") > -1

    def _scroll(self, element, times=1):
        """Scroll a specific element one or more times with small delay between
        them."""

        while times > 0:
            self.driver.execute_script(
                'arguments[0].scrollTop = arguments[0].scrollHeight',
                element
            )
            self.driver.implicitly_wait(0.5)
            times -= 1
