.. You should enable this project on travis-ci.org and coveralls.io to make
   these badges work. The necessary Travis and Coverage config files have been
   generated for you.

.. image:: https://travis-ci.org//ckanext-tracker.svg?branch=master
    :target: https://travis-ci.org//ckanext-tracker

.. image:: https://coveralls.io/repos//ckanext-tracker/badge.svg
  :target: https://coveralls.io/r//ckanext-tracker

.. image:: https://pypip.in/download/ckanext-tracker/badge.svg
    :target: https://pypi.python.org/pypi//ckanext-tracker/
    :alt: Downloads

.. image:: https://pypip.in/version/ckanext-tracker/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-tracker/
    :alt: Latest Version

.. image:: https://pypip.in/py_versions/ckanext-tracker/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-tracker/
    :alt: Supported Python versions

.. image:: https://pypip.in/status/ckanext-tracker/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-tracker/
    :alt: Development Status

.. image:: https://pypip.in/license/ckanext-tracker/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-tracker/
    :alt: License

===============
ckanext-tracker
===============

.. Put a description of your extension here:
   What does it do? What features does it have?
   Consider including some screenshots or embedding a video!


--------------------
Latest Notes & TODOs
--------------------

- [ATTENTION 1]
   resourcetracker_ogr is used to replace datastore functionalities previously served by datapusher or xloader. Making use of this sub-plugin will cause compatibility issues and malfunctioning of several ckan extensions that rely on either datapusher or xloader and their respective hooks and triggers.
- [ATTENTION 2]
   datastoretracker and its subplugins are using datapusher/xloader hooks and triggers and will soon be disabled and replaced by ogr trackers and thus it is not adviced to be further developed.

- [TODO 1]
   Making use of resourcetracker_ogr is already causing existing extensions that were served through datapusher/xloader and/or datastoretracker to not work properly. Two extensions that already need to be upgraded are ckanext-xlstocsv and ckanext-validation.
- [TODO 2]
   resourcetracker_ogr is currently blocking triggers coming from datastore actions. This could result in data loss and should be further investigated, for example in the cases of a datastore_update or datastore_upsert.


------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-tracker:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-tracker Python package into your virtual environment::

     pip install ckanext-tracker

3. Add ``tracker`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


----------------------------
Additional Plugin Interfaces
----------------------------

**Additional trackers Info**

Inside ckanext-tracker are included sub-plugins that extend functionality. These sub-plugins use the correct hooks to populate redis queries and trigger the correct workers. The ones including an underscore '_' inherit properties from their parent, as named before the underscore.
The current list of sub-plugins includes::

      datastoretracker_geoserver
      datastoretracker_xlstocsv
      packagetracker_ckantockan
      packagetracker_ckantockan_donl
      packagetracker_ckantockan_oneckan
      packagetracker_ckantockan_oneckan_rotterdam
      packagetracker_ogr
      resourcetracker_ckantockan
      resourcetracker_ckantockan_donl
      resourcetracker_ckantockan_oneckan
      resourcetracker_geonetwork
      resourcetracker_geoserver
      resourcetracker_ogr



**Additional trackers READMEs**

Tracker Geoserver `README <docs/resourcetracker_geoserver.rst>`_

---------------
Config Settings
---------------

Document any optional config settings here. For example::

    # The minimum number of hours to wait before re-checking a resource
    # (optional, default: 24).
    ckanext.tracker.some_setting = some_default_value


------------------------
Development Installation
------------------------

To install ckanext-tracker for development, activate your CKAN virtualenv and
do::

    git clone https://github.com//ckanext-tracker.git
    cd ckanext-tracker
    python setup.py develop
    pip install -r dev-requirements.txt


-----------------
Running the Tests
-----------------

To run the tests, do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.tracker --cover-inclusive --cover-erase --cover-tests


---------------------------------
Registering ckanext-tracker on PyPI
---------------------------------

ckanext-tracker should be availabe on PyPI as
https://pypi.python.org/pypi/ckanext-tracker. If that link doesn't work, then
you can register the project on PyPI for the first time by following these
steps:

1. Create a source distribution of the project::

     python setup.py sdist

2. Register the project::

     python setup.py register

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the first release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.1 then do::

       git tag 0.0.1
       git push --tags


----------------------------------------
Releasing a New Version of ckanext-tracker
----------------------------------------

ckanext-tracker is availabe on PyPI as https://pypi.python.org/pypi/ckanext-tracker.
To publish a new version to PyPI follow these steps:

1. Update the version number in the ``setup.py`` file.
   See `PEP 440 <http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers>`_
   for how to choose version numbers.

2. Create a source distribution of the new version::

     python setup.py sdist

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the new release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.2 then do::

       git tag 0.0.2
       git push --tags