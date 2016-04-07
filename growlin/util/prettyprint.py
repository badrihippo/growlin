from datetime import datetime, timedelta
def pretty_date(then, now=None, birthday=None):
    if not now: now = datetime.now()
    delta = now-then
    if delta < timedelta(0):
        raise ValueError('Cannot handle future dates: %s is before %s' % (then, now))
    if birthday and birthday.month == then.month and birthday.day == then.day:
        if delta.days/365 < 1 : # Less than a year ago
            return 'on your birthday'
        else:
            age = then.year-birthday.year
            return 'on your %dth birthday' % age
    else:
        if delta < timedelta(0, 3600):
            return '%d minutes ago' % (delta.seconds/60)
        elif delta < timedelta(0, 3900):
            return 'about an hour ago'
        elif delta < timedelta(1) and then.day == now.day:
            return then.strftime('at %I:%M %p today')
        elif delta < timedelta(7):
            return then.strftime('last %A')
        else:
            return then.strftime('on %d %b %Y')
