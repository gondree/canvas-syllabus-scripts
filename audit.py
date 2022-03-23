#!/usr/bin/env python3

import sys, os, json, yaml
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from canvasapi import Canvas

def check_course_visibility(course, term, update=False):
    """For a specific course, check that course is:
     - in this term and published
     - has a syllabus visible to the institution (public_syllabus_to_auth)
       or is otherwise public
    """
    if course.enrollment_term_id != term:
        return 0
    if course.workflow_state != 'available':
        return 0

    problem_tabs = [t for t in course.get_tabs() if t.id == 'syllabus' and hasattr(t, 'hidden') and t.hidden == True]
    if len(problem_tabs) > 0:
        print("***", course.name, "has syllabus page hidden")

    if course.public_syllabus_to_auth or course.public_syllabus:
        return 0
    print("-->", course.name, course.workflow_state, course.enrollment_term_id)

    if update:
        if not (course.public_syllabus_to_auth or course.public_syllabus):
            course.update(course={'public_syllabus_to_auth':True})
    return 1


def check_for_inaccessible_syllabi(OPT):
    """Counts, and optionally updates, all courses
    """
    canvas = Canvas(OPT['API_URL'], OPT['API_KEY'])

    total = 0
    for a in canvas.get_accounts():
        print(a.id, a.name)
        for c in a.get_courses(enrollment_term_id=OPT['TERM'], published=True):
            total += check_course_visibility(c, term=OPT['TERM'], update=OPT['update'])

    if not OPT['update']:
        print("There are", total, "courses that are not accessible")
    else:
        print("There were", total, "courses that were updated")


if __name__ == '__main__':
    """Audits to see if syllabi are available at the institutional level
    """
    parser = ArgumentParser(description='Scrape Canvas syllabi',
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("--config", type=str, 
        dest='config', required=True,
        help="Path to YAML confgig file")
    parser.add_argument("--update", type=bool, 
        dest='update', default=False, required=False,
        help="To update settings")
    parser.add_argument("--verbose", type=bool,
        dest='verbose', default=False, required=False)
    OPT = vars(parser.parse_args())

    # get options from the yml config file
    try:
        with open(OPT['config'], 'r') as file:
            config = yaml.load(file)
            OPT.update(config)
    except yaml.YAMLError as e:
        print("Error in configuration file:", e)

    # audit, and possibly update, syllabi visibility
    check_for_inaccessible_syllabi(OPT)

