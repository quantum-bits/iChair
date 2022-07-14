import datetime

NO_OVERLAP_TIME_BLOCKS = "Time blocks for a given day within a course offering cannot overlap."
ENDING_BEFORE_BEGINNING_TIME = "Ending time must be after beginning time."

ALL_SEMESTERS_ID = -1
NO_ROOM_SELECTED_ID = -1
NO_YEAR_SELECTED_ID = -1

DAY_SORTER_DICT = {
        'M': 0,
        'T': 1,
        'W': 2,
        'R': 3,
        'F': 4
    }

# https://www.w3schools.com/python/python_datetime.asp
SANDBOX_YEAR_BEGIN_ON = datetime.datetime(2010, 8, 25)
SANDBOX_YEAR_END_ON = datetime.datetime(2011, 5, 31)
SANDBOX_SUMMER_BEGIN_ON = datetime.datetime(2010, 6, 1)
SANDBOX_SUMMER_END_ON = datetime.datetime(2010, 8, 20)
SANDBOX_FALL_BEGIN_ON = datetime.datetime(2010, 8, 25)
SANDBOX_FALL_END_ON = datetime.datetime(2010, 12, 15)
SANDBOX_JTERM_BEGIN_ON = datetime.datetime(2011, 1, 1)
SANDBOX_JTERM_END_ON = datetime.datetime(2011, 1, 30)
SANDBOX_SPRING_BEGIN_ON = datetime.datetime(2011, 2, 1)
SANDBOX_SPRING_END_ON = datetime.datetime(2011, 5, 31)

SEMESTER_NAME_SUMMER = 'Summer'
SEMESTER_NAME_FALL = 'Fall'
SEMESTER_NAME_JTERM = 'J-Term'
SEMESTER_NAME_SPRING = 'Spring'