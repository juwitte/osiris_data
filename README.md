# OSIRIS data

This Python library and scripts help with data handling in and out of OSIRIS.

Use `OsirisIO` to operate on the MongoDB of your OSIRIS. This included import of new activities with automated validation.

>**_ATTENTION_**: This library is under active development and should be used with caution. If you plan to change the data of your OSIRIS instance directly on MongoDB, we recommend to NOT directly work on of your live system. Work on a copy instead and dump/restore your changes back into the live system afterwards.


## Setup 
### Environment

This library need Python to be installed. Please look up [how to install](https://wiki.python.org/moin/BeginnersGuide/Download) the latest Python version on your OS. You will also need `pip` to install packages.

When you have Python installed, you can create an virtual environment (see [here](https://docs.python.org/3/library/venv.html) for more information on python virtual environments). 

This command will create a folder named 'venv' and all needed files for the virtual environment with in the folder:

```bash
python3 -m venv ./venv
```

Next step is to start the virtual environment:

```bash
source ./venv/bin/activate
```

### Install osirisdata

Now you can install the python library **osirisdata** and all dependencies. Therefore you can run:

```bash
make install
```

## Use Library

### OsirisIO

This is a short example on how to use the OsirisIO function:

First you have to initialize a instance of OsirisIO with your MongoDB connection information. OsirisIO will automatically build [pydantic](https://pydantic.dev/docs/) models for the all defined activity types of your OSIRIS instance. This can be turned off by setting `validation` to `False`. The option `validate_extra` is used to define how the pydantic models should behave when encountering field names that are not defined in the activity types of your OSIRIS instance. You can choose between `allow`, `ignore` or `forbid`, for more information see [here].(https://pydantic.dev/docs/validation/latest/api/pydantic/base_model/#pydantic.BaseModel.model_construct)

Import and initialize:
```python
from osirisdata.osiris_io import OsirisIO

OSIRIS = OsirisIO(
    connection="MONGODB CONNECTION STRING", 
    database="NAME OF YOUR OSIRIS DATABASE IN MONGODB"
    validation=True, # optional, default = True
    validate_extra='ignore' # optional, default = ignore
)
```

Here are some examples of the functions offered by OsirisIO.

Delete a whole collection like this:
```python
OSIRIS.delete_collection('activities')
```
This will delete the all entries in the `activities` collection


To add a new activity to OSIRIS you can build up a Python `dict` with all needed information and simply add the activity with `add_activity()`:
```python
activity = {
    "title": "OSIRIS data",
    "date": {
        "year": 2026,
        "month": 5,
        "day": 7
    }, ...
}

OSIRIS.add_activity(activity)
```
> **_NOTE:_**  The `add_activity` function will automatically validate the activity dictionary with the pydantic model for the activity type. You can turn off the functionality in the initialization step of OsirisIO.


### OpenAlexParser

Setup OpenAlexParser, you have to find out your institute id from OpenAlex.
```python
OSIRIS = OsirisIO(connection="mongodb://localhost:27017/", database="osiris")
OPENALEX = OpenAlexParser(OSIRIS, YourInstituteId, YourEmail)
```
