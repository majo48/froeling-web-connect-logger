"""
    This file contains code for querying the connect-web registered account
    Copyright (c) 2020 M. Jonasse (martin.jonasse@mail.ch)

    This module uses the Google Chrome webdriver, Firefox (geckodriver) is buggy and slow.
    Follow the instructions provided in https://sites.google.com/a/chromium.org/chromedriver/home
    The current implementation in MacBook is /usr/local/bin/chromedriver --version
    ChromeDriver 87.0.4280.88 (89e2380a3e36c3464b5dd1302349b1382549290d-refs/branch-heads/4280@{#1761})

"""
from logger import local_settings, database
from selenium import webdriver
from sys import platform
import time
import os
import traceback


class Session:
    """ login to a HTML session, scrape key: value pairs from website and logout """
    MAXTRY = 10

    def __init__(self, login_url, username, password):
        """ initialize a logging session with connect-web """
        self._success = False
        try:
            self._login(login_url, username, password)
            self._get_system_info()
            self._get_boiler_info()
            self._get_heating_info()
            self._get_tank_info()
            self._get_fead_info()
            self._logout()
            self._success = True
        except Exception as e:
            etype = type(e).__name__
            print(self.now() + ' >>> Error(' + etype + '), ' + str(e))
            traceback.print_exc()
        finally:
            pass

    def is_successfull(self):
        """ True if the session (login .. logout) was successfull """
        return self._success

    def __wait_for_component(self, component_name):
        """ wait-check for component_name response """
        count = 1
        while count <= self.MAXTRY:
            get_component_tags = self.driver.find_elements_by_tag_name("mat-card-title")
            time.sleep(1)
            if len(get_component_tags) == 1:
                element = get_component_tags[0].text
                if element.startswith(component_name):
                    break
            count += 1
        else:
            raise Exception(
                'The browser timed out (' + component_name +
                ' information page), bad connection?'
            )

    def __get_value_pairs(self, driver, page_id):
        """ get value pairs from the WebDriver object """
        keys = driver.find_elements_by_xpath("//div[@class='key']")
        if page_id == 'System':
            values = driver.find_elements_by_xpath("//div[@class='value']") # proper spelling in html source
        else:
            values = driver.find_elements_by_xpath("//div[@calss='value']")  # BEWARE: typo in html source
        idx = 0
        while idx < len(keys):
            key = keys[idx].text
            value = values[idx].text
            pair = self.__split_value_unit(value)
            value = pair['value']
            tunit = pair['unit']
            page_idx = str(idx+1)
            if len(page_idx) == 1:
                page_idx = '0' + page_idx
            self.infos.append({
                'customer_id': local_settings.customer_id(),
                'timestamp': self.timestamp,
                'page_id': page_id,
                'page_key' : page_id + page_idx,
                'label': key,
                'value': value,
                'tunit': tunit
            })
            idx += 1 # next key

    def __split_value_unit(self, value_unit):
        """ properly split values and technical units """
        units = { 'percent': '%', 'degrees': '°C', 'hours': 'h', 'tons': 't', 'kilograms': 'kg' }
        spos = value_unit.rfind(' ')
        if spos != -1:
            # may contain a technical unit
            u = value_unit[spos+1:]
            v = value_unit[:spos]
            if u in units.values():
                return { 'value': v, 'unit': u}
        return {'value': value_unit, 'unit': ''}

    def _login(self, login_url, username, password):
        """ login to the connect-web.froeling.com site """
        self.timestamp = self.now()
        print(self.timestamp + ' >>> login in to url: ' + login_url)
        self.infos = []
        # start webdriver service
        xtime = time.time()
        if platform == "win32":
            cdpath = 'C:/WebDriver/bin/chromedriver.exe'
        else:  # OSX and LInux
            cdpath = '/usr/local/bin/chromedriver'
        self.driver = webdriver.Chrome(executable_path=cdpath)
        print(self.timestamp + ' >>> started webdriver in ' + str(round(time.time() - xtime, 3)) + 'secs.' )
        # open login page
        xtime = time.time()
        self.driver.get(login_url)
        print(self.timestamp + ' >>> loaded login page in ' + str(round(time.time() - xtime, 3)) + 'secs.')
        time.sleep(4) # do absolutely nothing for the first 5 seconds
        # wait-check for response
        count = 1
        while count <= self.MAXTRY:
            time.sleep(1)
            input_tags = self.driver.find_elements_by_tag_name("input")
            button_tags = self.driver.find_elements_by_tag_name("button")
            if len(input_tags) >= 2 and len(button_tags) >= 1:
                break
            count += 1
        else:
            dt = self.timestamp.replace(' ', 'T')
            self.driver.save_screenshot('save' + dt + 'screenhot.png')
            with open('save'+dt+'webpage.html', 'w') as f:
                f.write(self.driver.page_source)
            raise Exception('The browser timed out (login), bad connection @ ' + login_url)
        # fill out login form
        input_tags[0].send_keys(username)
        input_tags[1].send_keys(password)
        button_tags[0].click()
        # wait-check for response after login
        count = 1
        while count <= self.MAXTRY:
            time.sleep(1)
            url = self.driver.current_url
            if url == local_settings.facility_url():
                break
            count += 1
        else:
            raise Exception('The browser timed out (first page), bad connection?')
        print(self.now() + ' >>> successfull login')

    def _get_system_info(self):
        """ scrape infos from the facility info site """
        print(self.now() + ' >>> system info')
        self.driver.get(local_settings.facility_info_url())
        # wait for response
        count = 1
        while count <= self.MAXTRY:
            time.sleep(1)
            get_tags = self.driver.find_elements_by_tag_name("froeling-facility-detail-container")
            if len(get_tags) == 1:
                break
            count += 1
        else:
            raise Exception('The browser timed out (facility information page), bad connection?')
        self.__get_value_pairs(self.driver, 'System')

    def _get_boiler_info(self):
        """ scrape infos from the components->boiler info site """
        print(self.now() + ' >>> boiler info')
        self.driver.get(local_settings.boiler_info_url())
        self.__wait_for_component('Boiler')
        self.__get_value_pairs(self.driver, 'Boiler')

    def _get_heating_info(self):
        """ scrape infos from the components->heating info site """
        print(self.now() + ' >>> heating circuit 01 info')
        self.driver.get(local_settings.heating_info_url())
        self.__wait_for_component('Heating')
        self.__get_value_pairs(self.driver, 'Heating')

    def _get_tank_info(self):
        """ scrape infos from the components->tank info site """
        print(self.now() + ' >>> DHW tank 01 info')
        self.driver.get(local_settings.tank_info_url())
        self.__wait_for_component('DHW')
        self.__get_value_pairs(self.driver, 'Tank')

    def _get_fead_info(self):
        """ scrape infos from the components->feed info site """
        print(self.now() + ' >>> feed system info')
        self.driver.get(local_settings.feed_info_url())
        self.__wait_for_component('Feed')
        self.__get_value_pairs(self.driver, 'Feed')

    def _logout(self):
        """ logout from the connect-web.froeling.com site """
        print(self.now() + ' >>> logout')
        self.driver.quit()
        # persist data to SQLite database
        db = database.Database()
        for info in self.infos:
            db.insert_log(info)

    def now(self):
        """ get current time as string """
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


if __name__ == '__main__':
    print('So sorry, the ' + os.path.basename(__file__) + ' module does not run as a standalone.')

