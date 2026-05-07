
# Setup environment

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

## Set up osirisdata

Now you can install the python library **osirisdata** and all dependencies. Therefore you can  run:

```bash
make install
```

### Use OsirisIO

This is a short example on how to use the OsirisIO function:

Initialize:
```python
OSIRIS = OsirisIO(connection="mongodb://localhost:27017/", database="osiris")
```

Delete all activities:
```python
OSIRIS.delete_collection('activities')
```

Add a new activity:
```python
OSIRIS.add_activity(activity)
```

### Use OpenAlexParser

Setup OpenAlexParser, you have to find out your institute id from OpenAlex.
```python
OSIRIS = OsirisIO(connection="mongodb://localhost:27017/", database="osiris")
OPENALEX = OpenAlexParser(OSIRIS, YourInstituteId, YourEmail)
```
