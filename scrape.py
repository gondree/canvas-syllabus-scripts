#!/usr/bin/env python3

import sys, os, json, yaml
import pdfkit, re
import requests
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from canvasapi import Canvas
from canvasapi.exceptions import ResourceDoesNotExist

def scrape_course_syllabus(course, term, path, verbose=False):
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

    if os.path.exists(path+name+'.pdf'):
        print("--", name+'.pdf')
        return
    else:
        print("++", name+'.pdf')

    # generate a PDF
    try:
        pdfkit.from_string(body, path+name+'.pdf', options={"encoding": "utf8"})
    except IOError:
        print(">>> likely some problem with embedded content in", path+name+'.pdf')

    # find canvas-resident files referenced in syllabus, and download them
    prog = re.compile('courses/'+str(course.id)+'/files/(\d+)\?')
    result = prog.findall(body)
    if result != None:
        for fid in result:
            try:
                f = course.get_file(fid)
                fname=f.display_name.replace(':', '_')
                f.download(path+name+'-attachment-'+fname)
            except ResourceDoesNotExist:
                print(">>> some issue with downloading file id", fid, "'"+fname+"'")

    # find google-docs files referenced in syllabus, and download them
    prog = re.compile('(https://docs.google.com/document/d/.*?/.*)')
    result = prog.findall(body)
    if result != None:
        for url in result:
            pdf_url = re.sub(r"https://docs\.google\.com/document/d/(.*?)/.*", 
                        r"http://docs.google.com/document/d/\1/export?format=pdf", url)
            try:
                r = requests.get(pdf_url, allow_redirects=True)
                if r.status_code != 200:
                    continue
                header = r.headers['Content-Disposition']
                file_name = re.search(r'filename="(.*)"', header).group(1)
                open(path+name+'-attachment-gdoc-'+file_name, 'wb').write(r.content)
            except KeyError:
                print(">>> could not download", pdf_url)
            except Exception as e:
                print(">>> could not download", pdf_url, ">>>", repr(e))

    # find google-drive files referenced in syllabus, and download them
    prog = re.compile('(https://drive.google.com/file/d/.*?/.*)')
    result = prog.findall(body)
    if result != None:
        for url in result:
            file_url = re.sub(r"https://drive\.google\.com/file/d/(.*?)/.*", 
                        r"http://drive.google.com/uc?export=download&id=\1", url)
            try:
                r = requests.get(file_url, allow_redirects=True)
                if r.status_code != 200:
                    continue
                header = r.headers['Content-Disposition']
                file_name = re.search(r'filename="(.*)"', header).group(1)
                open(path+name+'-attachment-gdrive-'+file_name, 'wb').write(r.content)
            except KeyError:
                print(">>> could not download", file_url)
            except Exception as e:
                print(">>> could not download", file_url, ">>>", repr(e))

    return


def download_all_syllabi(OPT):
    """Scrape content from each course in this term
    """
    canvas = Canvas(OPT['API_URL'], OPT['API_KEY'])
    for a in canvas.get_accounts():
        print(a.id, a.name)
        for c in a.get_courses(enrollment_term_id=OPT['TERM'], published=True, include='syllabus_body'):
            scrape_course_syllabus(c, term=OPT['TERM'], path=OPT['download'], verbose=OPT['verbose'])


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

    # check path exists, if download was selected
    if not OPT['download'].endswith('/'):
        OPT['download'] = OPT['download'] + '/'
    if not os.path.isdir(OPT['download']):
        os.mkdir(OPT['download'])

    # download syllabi
    download_all_syllabi(OPT)
