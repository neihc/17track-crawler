import re
from dateutil.parser import parse


class TrackingEvent:
    def __init__(self, **kwargs):
        self.date = kwargs.get('date')
        if isinstance(self.date, str):
            self.date = parse(self.date)

        self.detail = kwargs.get('detail')

    def to_dict(self):
        return dict(date=self.date.isoformat(), detail=self.detail)


class TrackingNumber:
    def __init__(self, **kwargs):
        self.tracking_number = kwargs.get('tracking_number')
        self.status = kwargs.get('status')
        self.original_country = kwargs.get('original_country')
        self.destination_country = kwargs.get('destination_country')
        self.events = kwargs.get('events')

    @classmethod
    def create_from_17track_clipboard(cls, tracking_detail):
        TRACKING_NUMBER_REGEX = r'Number: ([0-9a-zA-Z]+)\n'
        PACKAGE_STATUS_REGEX = r'Package status: (.+)\n'
        COUNTRY_REGEX = r'Region: (.+)\n'
        EVENT_REGEX = r'([0-9|:|\-| ]{16,16})   (.+)\n'

        try:
            tracking_number = re.search(TRACKING_NUMBER_REGEX, tracking_detail)[1]
            status = re.search(PACKAGE_STATUS_REGEX, tracking_detail)[1]
            countries = re.search(COUNTRY_REGEX, tracking_detail)[1].split('>')
            events = re.findall(EVENT_REGEX, tracking_detail)
        except:
            import pdb; pdb.set_trace()
            pass

        return cls(
            tracking_number=tracking_number,
            status=status,
            original_country=countries[0],
            destination_country=countries[1],
            events=[TrackingEvent(date=e[0], detail=e[1]) for e in events],
        )

    def __str__(self):
        return f'{self.tracking_number} {self.status}'

    def to_dict(self):
        return dict(
            tracking_number=self.tracking_number,
            status=self.status,
            original_country=self.original_country,
            destination_country=self.destination_country,
            events=[e.to_dict() for e in self.events],
        )
