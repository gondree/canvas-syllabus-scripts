# canvas-syllabus-scripts
Scripts using the Canvas API to grab syllabus data.


## Usage Example

To audit:

```
python audit.py --config your_config.yml
```

To audit and update:

```
python audit.py --config your_config.yml --update
```

To scrape syllabi:

```
python scrape.py --config your_config.yml --download path-to-downloads-dir
```

## Dependencies
```
pip install canvasapi
```
