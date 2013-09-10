#!/bin/sh
cp planner/fixtures/initial_data.json planner/fixtures/old_data.json
python manage.py dumpdata -e contenttypes > planner/fixtures/initial_data.json


