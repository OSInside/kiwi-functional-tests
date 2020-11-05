# kiwi-functional-tests

KIWI openQA functional tests using the images from the staging project on OBS.


## Prerequisites

You need access to an openQA instance, where either the job groups, test suites
& products have been configured or where you have operator access so that you
can create these yourself. For testing purposes, you can setup a local instance
as described in the
[documentation](https://open.qa/docs/#_openqa_in_a_container).

Furthermore, you need to have a valid account in openSUSE's instance of the
[Open Build Service](https://build.opensuse.org) and
[`osc`](https://en.opensuse.org/openSUSE:OSC) set up.

Last but not least, you'll need [poetry](https://python-poetry.org/) to utilize
the scripts shipped in this repository.

Before proceeding further, be sure to install the dependencies and run `poetry
install`.


## Setup on openQA

You can apply the necessary settings automatically using the `settings.py`
script as follows:
```ShellSession
poetry run ./settings.py --server $URL_TO_MY_INSTANCE
```

If you are running a local instance, then you will have to add the domain
`opensuse.org` to the `download_domains` option in `/etc/openqa/openqa.ini`:
```ini
[global]
download_domains = opensuse.org
```

## Schedule a test run

Test runs are scheduled using the script `schedule_test_run.py`. It will by
default schedule **all** tests for all distributions & versions on
[o3](https://openqa.opensuse.org) and create a state file which contains the
started job ids:
```ShellSession
$ poetry run ./schedule_test_run.py
Wrote build state into kiwi_build_20210430_1619795290_483278.pickle
```

The created `.pickle` file can be fed into the monitoring script `monitor.py` to
query the current state of the jobs:
```ShellSession
$ poetry run ./monitor.py -p kiwi_build_20210430_1619795290_483278.pickle
https://openqa.opensuse.org/tests/876: state: passed, result: done
https://openqa.opensuse.org/tests/877: state: passed, result: done
https://openqa.opensuse.org/tests/886: state: failed, result: done
https://openqa.opensuse.org/tests/920: state: failed, result: done
https://openqa.opensuse.org/tests/921: state: skipped, result: cancelled
https://openqa.opensuse.org/tests/922: state: failed, result: done
```

or to cancel them all:
```ShellSession
$ poetry run ./monitor.py -c kiwi_build_20210430_1619795290_483278.pickle
```
