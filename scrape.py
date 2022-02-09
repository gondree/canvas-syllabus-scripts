#!/usr/bin/env python3

import sys, os, json, yaml
import pdfkit, re
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from canvasapi import Canvas

def scrape_course_syllabus(course, term, path):
    """For a course, try to download the syllabus and any local attachments
    """
    if course.enrollment_term_id != term:
        return
    if course.workflow_state != 'available':
        return

    # get the html for the syllabus
    body = course.syllabus_body
    if body == None or len(body) == 0:
        return
    name = course.name.split()[0][:-1]

    # generate a PDF
    pdfkit.from_string(body, path+name+'.pdf')

    # find canvas-resident files referenced in syllabus, and download them
    prog = re.compile('courses/'+str(course.id)+'/files/(\d+)\?')
    result = prog.findall(body)
    if result == None:
        return

    for fid in result:
        f = course.get_file(fid)
        f.download(path+name+'-attachment-'+f.display_name)

    return


def download_all_syllabi(OPT):
    """Scrape content from each course in this term
    """
    canvas = Canvas(OPT['API_URL'], OPT['API_KEY'])
    for a in canvas.get_accounts():
        print(a.id, a.name)
        for c in a.get_courses(enrollment_term_id=OPT['TERM'], published=True, include='syllabus_body'):
            scrape_course_syllabus(c, term=OPT['TERM'], path=OPT['download'])


if __name__ == '__main__':
    """Downloads all syllabi and related files
    """
    parser = ArgumentParser(description='Scrape Canvas syllabi',
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("--config", type=str, 
        dest='config', required=True,
        help="Path to YAML confgig file")
    parser.add_argument("--download", type=str, 
        dest='download', default=None, required=True,
        help="Path to download files")
    OPT = vars(parser.parse_args())

    # get options from the yml config file
    try:
        with open(OPT['config'], 'r') as file:
            config = yaml.load(file)
            OPT.update(config)
    except yaml.YAMLError as e:
        print("Error in configuration file:", e)

    # check path exists, if download was selected
    if not OPT['download'].endswith('/'):
        OPT['download'] = OPT['output'] + '/'
    if not os.path.isdir(OPT['download']):
        os.mkdir(OPT['download'])

    # download syllabi
    download_all_syllabi(OPT)
