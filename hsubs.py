import requests
from json import load
from lxml import html
from collections import namedtuple


class ScheduleGenerator:
    """
    Class that generates the schedule by scraping HS's schedule page.
    """

    def __init__(self):
        self.config = load(open('config.json', 'r'))
        self.days = self.config['en_gb']['day_array']
        self.show = namedtuple('Show', ['day', 'title', 'time'])
        self.schedulelink = 'https://horriblesubs.info/release-schedule/'
        self.req = requests.get(self.schedulelink)
        self.tree = html.fromstring(self.req.text)
        self.id = 0
        self.tablelen = None
        self.title = None
        self.time = None

    def iter_schedule(self, days=None):
        if not days:
            days = self.days
        elif not isinstance(days, (list, tuple)):
            days = [days]

        for day in days:
            # tables start from 1 rather than from 0, 1 day = 1 table
            dayindex = self.days.index(day) + 1
            expr_str = f'//*[@id="post-63"]/div/table[{dayindex}]'
            self.tablelen = len(self.tree.xpath(expr_str)[0].getchildren())

            for table in range(self.tablelen):
                self.title = self.tree.xpath(expr_str)[0].getchildren()[table].getchildren()[0].getchildren()[0].text
                self.time = self.tree.xpath(expr_str)[0].getchildren()[table].getchildren()[1].text
                yield self.show(day, self.title, self.time)

    def update_schedule(self):
        self.req = requests.get(self.schedulelink)
        self.tree = html.fromstring(self.req.text)
        self.id += 1
        print(f"Update successful, id: {self.id}")

    def pretty_print(self):
        for day in self.days:
            print(day)
            for item in self.iter_schedule(day):
                if item.day is day:
                    print(f'• {item.title} @ {item.time} PST')
            print('-----------------------------------------')
