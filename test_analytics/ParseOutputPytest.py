import json
import os


class ParseOutputPytest:
    def _path_to_name(self, path_test: str):
        """Using the saved test path, we generate a name, 
            replacing '\\' wand'/' with '_'"""
        text = path_test
        text = text.replace('/', '_')
        text = text.replace('\\', '_')
        text = text.replace('::', '-')
        text = text.replace('.py', '')
        return text

    def _now_date(self):
        """Get current date and time in the format: 
            {day}-{month}-{year}_{hour}-{minute}-{second}"""

        from datetime import datetime

        current_datetime = datetime.now() 
        year = current_datetime.year
        month = current_datetime.month
        day = current_datetime.day
        hour = current_datetime.hour
        minute = current_datetime.minute
        second = current_datetime.second

        date = f'{day}-{month}-{year}_{hour}-{minute}-{second}'

        return date

    def _pretty_save_file(self, file_name: str):
        """The output of pytest occurs in one line, which is not readable. 
           Using this function, we will create a new file in which json will 
            be written with all the indents."""

        with open(file_name) as f:
            data = json.load(f)

        with open(file_name, 'w') as f:
            json.dump(data, f, indent=4)

    def _get_short_error(self, full_error: str, length_tb: int) -> str:
        # Let's determine if there is a 'Remote Traceback' in the error text
        remote_error = 'Remote Traceback' in full_error
        short_error = ''

        list_line_traceback = full_error.split('\n')

        #### ---- If you need another metric, then you can register it here 

        # If there is a remote traceback, then we will consider only it
        slice_index = 0
        if remote_error:
            for i, line in enumerate(list_line_traceback):
                if 'Remote Traceback' in line:
                    slice_index = i
                    break

        # We'll keep the traceback that comes after the text 'Remote traceback'
        list_line_traceback = list_line_traceback[slice_index:]

        if len(list_line_traceback) > length_tb:
            short_error = list_line_traceback[-length_tb:]
        else:
            # Traceback is too short
            short_error = list_line_traceback

        #### ----

        short_error = '\n'.join(short_error)

        # Add, what error is remote
        if remote_error and 'Remote Traceback' not in short_error:
            short_error = f'======= Remote Traceback =======\n ... \n{short_error}'

        return short_error

    def _get_dict_name_short_error(self, dict_name_full_error: dict, length_tb: int) -> dict:
        """Accepts a dictionary and the number `length_tb` is also accepted. 
            From the full text of the error, only the last `length_tb` lines
            of the Traceback are left. If there are fewer lines in the 
            error, the entire error will be returned. If `length_tb` == 0, 
            the entire traceback text will be returned (only local or only 
            remote). If `length_tb` == 1, only the error itself will be 
            returned. 

        Args:
            dict_name_full_error (dict): dictionary, where the 
                key - test_name, and the value - full text of the error.

            length_tb (int): The number shows how many last Traceback 
                lines to leave.

        Returns:
            dict: Return dict, where key - name test, value - short text 
                of the error.
        """
        dict_name_short_error = {}
        for name, full_error in dict_name_full_error.items():
            short_error = self._get_short_error(full_error, length_tb)
            dict_name_short_error[name] = short_error

        return dict_name_short_error

    def _get_name_without_args(self, full_name: str) -> str:
        """Gets the input name of the test, which has arguments passed 
            in square brackets. Removes curly brackets and their contents.

        Args:
            full_name (str): name of the test with arguments

        Returns:
            str: test name without arguments
        """
        new_name = full_name
        if '[' in full_name:
            index = full_name.find('[')
            new_name = full_name[:index]
        return new_name

    def _get_group_test_without_args(self, list_test: list) -> list:
        """For each name without parameters, we form a list of tests 
            that begins with this name.

        Args:
            list_test (list): A list with names test with parameters.

        Returns:
            list: Dictionary, where the key is the name of the test 
                without parameters, and the value is a list of tests 
                whose name begins with the name of the key.
        """
        group_by_short_name = {}
        for name in list_test:
            short_name = self._get_name_without_args(name)
            if short_name in group_by_short_name:
                group_by_short_name[short_name].append(name)
            else:
                group_by_short_name[short_name] = [name]

        return group_by_short_name

    def start_test(self, 
                   path_dir_for_start: str, 
                   path_test: str,
                   path_dir_for_save='test_analytics\\json_analytics_from_test', 
                   environment_variables='', 
                   args_pytest='',
                   new_name=None) -> str:
        """Let's run the specified test with the passed environment variables 
            and pytest arguments. The result will be saved in json format in 
            the folder `/test_analytics/json_analytics_from_test`. The 
            console displays the location of the file and its name as a 
            result of the program.

        Args:
            path_dir_for_start (str): The path to the folder from where we will 
                run the test.

            path_test (str): The path to the test that we will run.

            path_dir_for_save (str, optional): Path where will save json file.

            environment_variables (str, optional): Environment variables. 
                If there are several of them, then we specify the next 
                variable  using ' && '. Defaults to None.

            args_pytest (str, optional): Flags for pytest. The '--tb=...' flag 
                cannot be specified. Defaults to None.

            new_name (str, optional): File name for json.

        Returns:
            str: Returns the absolute path to the created file.
        """

        # Getting the name of the file where we will save the pytest results in json format
        part_file_name = self._path_to_name(path_test)
        now_date = self._now_date()

        if new_name is None:
            path_file_name = f'{path_dir_for_save}\\{now_date}_{part_file_name}.json'
        else:
            path_file_name = f'{path_dir_for_save}\\{new_name}.json'

        print(f'Run testing -> {path_test} \n')

        # Specify the folder from where we will run the tests
        os.chdir(path_dir_for_start)

        if environment_variables != '':
            environment_variables = f'{environment_variables} &&'

        print("Execute the command:")
        command = f'{environment_variables} python -m pytest {args_pytest} --tb=short --json={path_file_name} {path_test}'
        print(f'{command}\n')
        os.system(command)

        assert os.path.exists(path_file_name), "Failed to create a report in json format."

        self._pretty_save_file(path_file_name)
        print(f'The statistics for the test are saved in a file:\n{os.path.abspath(path_file_name)}\n')

        return path_file_name

    def get_dict_name_with_error_text(self, name_file_with_analytics_from_test: str) -> dict:
        """The input is a file that is obtained as a result of the 
            `start_test` method. 

        Args:
            name_file_with_analytics_for_test (str): the name of the json 
                file where the statistics for the test are located.

        Returns:
            dict: The dictionary is returned, where the key is the name of 
                the test, and the value is traceback (if there is a remote 
                one, then we will write it, if there is no such one, then we 
                will write a local one).
        """
        with open(name_file_with_analytics_from_test) as f:
            data = json.load(f)

        list_tests = data['report']['tests']
        dict_test_name_error = {}
        for test in list_tests:
            if test["outcome"] == "failed":
                # Get test name
                test_name = test['name']

                # Get the output of pytest for a specific test
                dict_test_name_error[test_name] = test['call']['longrepr']

        return dict_test_name_error

    def get_dict_error_with_list_test(self, dict_name_full_error: dict, length_tb: int) -> dict:
        """We call the `_get_dict_name_short_error ' method, and then we 
            perform grouping by mistake.

        Args:
            dict_name_full_error (dict): dictionary, where the key - test_name, 
                and the value - full text of the error.
            length_tb (int): The number shows how many last Traceback 
                lines to leave.

        Returns:
            dict: Return dict, where key - error, and values - list of tests 
                where this error occurs
        """

        dict_name_full_error = self._get_dict_name_short_error(dict_name_full_error, length_tb)

        group_errors = dict()
        for name, text_error in dict_name_full_error.items():
            if text_error in group_errors:
                group_errors[text_error].append(name)
            else:
                group_errors[text_error] = [name]
        return group_errors

    def get_dict_test_duration(self, name_file_with_analytics_from_test: str) -> dict:
        """The input is the name of the file that is obtained as a result of 
            the `start_test` method.

        Args:
            name_file_with_analytics_from_test (str): the name of the json 
                file where the statistics for the test are located.

        Returns:
            dict: a dictionary where the key - name of the test, and the 
                value - duration of the test
        """
        with open(name_file_with_analytics_from_test) as f:
            data = json.load(f)

        list_test = data['report']['tests']

        dict_name_duration = {}

        for test in list_test:
            if test["outcome"] == "passed":
                name = test['name']
                duration = test['duration']
                dict_name_duration[name] = duration

        return dict_name_duration

    def get_group_test_with_less_time(self, path_file: str, max_duration_file: float):
        """The input is json, from which only those tests are selected that 
            pass if you drop the arguments in square brackets. After that,  
            only those tests that are executed faster than max_duration_file 
            seconds are selected from these tests.

        Args:
            path_file (str): The path to the json file that is obtained as a 
                result of the start_test command
            max_duration_file (float): Maximum duration of a test group

        Returns:
            list: A list of tests, all of which pass and run in a time less 
                than max_duration_file
        """
        with open(path_file) as f:
            data = json.load(f)['report']['tests']

        all_list_test = {}  # All tests
        not_failed_list_test = {}  # All non-failed tests
        passed_list_test= {}  # All passed tests

        for test in data:
            all_list_test[test['name']] = test['duration']

            if test['outcome'] in ['passed', 'skipped', 'xfailed']:
                not_failed_list_test[test['name']] = test['duration']

            if test['outcome'] == 'passed':
                passed_list_test[test['name']] = test['duration']

        # We get groups of tests without parameters (for all tests)
        group_by_short_name_all_test = self._get_group_test_without_args(all_list_test.keys())

        # We get groups of tests without parameters (for passed tests)
        group_by_short_name_passed_test = self._get_group_test_without_args(passed_list_test.keys())

        # We get groups of tests without parameters (for non-failed tests)
        group_by_short_name_not_failed_test = self._get_group_test_without_args(not_failed_list_test.keys())

        # We get a dictionary where the key is the name of the test 
        #   without a parameter, and the value is the duration of this group
        passed_group_test_with_sum_duration = {}
        for short_name, test_list in group_by_short_name_passed_test.items():

            # If there are no failed tests
            if len(group_by_short_name_all_test[short_name]) == len(group_by_short_name_not_failed_test[short_name]):

                # Get the time (include xfail, skipped and passed)
                group_duration = 0
                for full_name in test_list:
                    group_duration += all_list_test[full_name]

                passed_group_test_with_sum_duration[short_name] = group_duration

        sorted_list_group = sorted(passed_group_test_with_sum_duration.items(), key=lambda x: x[1])

        # Duration of the selected tests
        sum_duration = 0

        # Number of selected tests
        count_test = 0

        while sum_duration < max_duration_file and count_test < len(sorted_list_group):
            sum_duration += sorted_list_group[count_test][1]
            count_test += 1

        tmp = [i[0] for i in sorted_list_group[:count_test]]

        return sorted(tmp)

    def print_top_most_frequent_errors(self, res_dict: dict, number_line: int, count_test_print=5):
        """The input is a dictionary, from which another dictionary is 
            grouped, where the key is the truncated part of the error, 
            and the value is a list of errors in which the truncated part 
            of the error matches. Then the sorting is performed and the 5 
            most common errors are displayed.

        Args:
            res_dict (dict): A dictionary where the key is the name of the 
                test, and the value is the full text of the error.
            number_line (int): The number shows how many last Traceback 
                lines to leave.
            count_test_print (int): We will output so many errors to the console
        """
        res_dict_group = self.get_dict_error_with_list_test(res_dict, number_line)

        list_error_count_test = []
        for text_error, list_test in res_dict_group.items():
            list_error_count_test.append((text_error, len(list_test)))

        sorted_list_error = sorted(list_error_count_test, key=lambda x: x[1], reverse=True)

        # If the number of tests in the array is less than this number, 
        #   then we will output all the tests
        number_tests_print = 5 

        # If the number of tests is greater than the previous number, 
        #   then we will output the following number of tests
        number_tests_print_part = 5

        for text_error, _ in sorted_list_error[:count_test_print]:
            list_test = res_dict_group[text_error]

            print('-----------------------------------------------------------------------')
            print(text_error, '\n')
            print(f'Occurs in {len(list_test)} tests.')

            if len(list_test) < number_tests_print:
                for test in list_test:
                    print('    ', test)
            else:
                for test in list_test[:number_tests_print_part]:
                    print('    ', test)

                print(f'And also in {len(list_test) - number_tests_print_part} tests.')

            print('-----------------------------------------------------------------------')
            print('\n')
