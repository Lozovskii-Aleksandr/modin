# User manual

## Installing dependencies

To run the analyzer, you need to install all the modin dependencies that are listed on its [website](https://modin.readthedocs.io/en/latest/contributing.html#development-dependencies). Also, for the script to work, you need to install the `pytest-json` library. If you installed the dependencies from `modin` using anaconda, then to install `pytest-json` you will need to type in the console `conda install -n modin pytest-json`.

## Description of the `ParseOutputPytest` module

ParseOutputPytest is a module that has methods for receiving and then processing json from pytest.

### Method `start_test(self, path_dir: str, path_test: str, environment_variables='', args_pytest='')`

This method accepts as input:

1. `path_dir` - a string containing the path from where the test will be run. By default, the same path is considered as that of the executable script (or jupyter notepad).
2. `path_test` - a string containing the path to the specified test.
3. `environment_variables` - a string with environment variables that must be specified when running the test. If there are several variables, then they should be listed using `&&`. For example, `"set val1=2 & & set val3=4"`. By default, they are considered an empty string.
4. `args_pytest` - a string with flags with which to run pytest. For example, `"--flag1 --flag2=val3"`. By default, they are considered an empty string.

As a result, the following command is run:
`{environment_variables} python -m pytest {args_pytest} --tb=short --json={path_file_name} {path_test}`

If successful, a json is created with the test results, which is saved to the `test_analytics` folder. The json file has the name: `test_analytics\\{now_date}_{part_file_name}.json`, where `now_date` is the date and time at the current time: `{day} - {month} - {year}_{hour} - {minute} - {second}`; `part_file_name` is the name of the test, which is converted so that all the characters `"\\"` and `"/"` are replaced by `"_"`, and `"::"` replaced by `" -"`.

### Method `get_dict_name_with_error_text(self, name_file_with_analytics_from_test: str)`

As input, the method accepts the string `name_file_with_analytics_from_test`, which is the path to the json that was obtained as a result of the `start_test` method. The output is a dictionary, where the key is the name of the test, and the value is an error that occurred as a result of passing the test.

### Method `get_dict_error_with_list_test(self, dict_name_full_error: dict, length_tb: int)`

The method accepts the dictionary `dict_name_full_error` as input, which is obtained as a result of the `get_dict_name_with_error_text` method (the key is the test name, the value is the error text). The input is also an integer `length_tb`, which shows how many last lines of the error will be saved. As a result, the text of all errors is truncated to the`length_tb` of the last lines, and then grouping is carried out by them. As a result of the method, a dictionary is obtained, the key of which is the error text (already truncated to` length_tb ' of the last lines), and the value is a list with the name of all tests that have this error.

### Method `get_dict_test_duration(self, name_file_with_analytics_from_test: str)`

As input, the method accepts the string `name_file_with_analytics_from_test`, which is the path to the json that was obtained as a result of the `start_test` method. The output is a dictionary, where the key is the name of the test, and the value is the time of passing the test.

## Example of using the `ParseOutputPytest` module to output similar errors and tests where they occur

As an example of the output of similar errors, the following [notebook](https://github.com/Lozovskii-Aleksandr/modin/blob/cloud_investigated/test_analytics/example_notebook_test_minimum.ipynb), in which `ParseOutputPytest` analyzes statistics for the tests `test_io`, `test_series` and `test_map_metadata`.

## Example of using the `ParseOutputPytest` module to compare test times

As an example of the output of statistics on time, the following is given [notebook](https://github.com/Lozovskii-Aleksandr/modin/blob/cloud_investigated/test_analytics/example_notebook_cmp_duration_test.ipynb), in which `ParseOutputPytest` analyzes the temporary statistics for the `test_map_metadata` test.
