import csv
import sys
import argparse


indent = 0
indent_increment = 8

# DATA_FILE = 'sample.csv.template'
DATA_FILE = '2023.csv'

class Person():
    def __init__(self, data: dict):
        # Full Name,Company email,Reports To Email,Job Title,Departments

        if 'Full Name' in data:
            self.full_name = data['Full Name']
        else:
            self.full_name = f"{data['First name']} {data['Last name']}"
        self.email = data['Company email']
        self.reports_to = data['Reports To Email']
        self.title = data['Job Title']
        self.department = data['Departments']

        self.direct_reports = []

        self.raw_data = data

    def print(self):
        print()
        indent_print('{} - {} ({})'.format(self.full_name, self.title, self.department))
        indent_print('{}'.format(self.email))
        indent_print('Reports to: {}'.format(self.reports_to))
        indent_print('Has {} direct reports'.format(len(self.direct_reports)))
        print()

    
    def add_direct_report(self, employee):
        self.direct_reports.append(employee)

    def has_direct_reports(self) -> bool:
        return len(self.direct_reports) > 0

    def subordinates_to_csv(self, single_layer=False):
        """
        Saves a CSV file with everyone who falls under this employee
        Also includes the current employee in the list
        """

        print(f'Single layer: {single_layer}')
        subs = self.subordinates(return_people_objects=False, single_layer=single_layer)
        subs.append(self.raw_data)
        list_to_csv(subs, '{}.csv'.format(self.full_name.replace(' ', '_')), preserve_column_order=True)

    def subordinates(self, return_people_objects=True, single_layer=False) -> list:
        """
        Returns a list of ALL subordinates, not just direct reports
        """

        output = self.direct_reports
        if len(self.direct_reports) == 0:
            return output


        if single_layer == False:
            # Go deeper than just the direct reports
            while True:
                added_new = False
                for subordinate in output:
                    for employee in subordinate.direct_reports:
                        if employee not in output:
                            output.append(employee)
                            added_new = True
                            
                if added_new == False:
                    break
                
        

        if return_people_objects == False:
            # We just want an array of dictionaries so we can output a CSV file

            converted_output = []
            for employee in output:
                converted_output.append(employee.raw_data)
            output = converted_output

        return output


    def print_subordinates(self):
        """
        Print full list of subordinates
        """

        global indent

        if len(self.direct_reports) == 0:
            return

        indent_print('listing {} subordinates for {}'.format(len(self.direct_reports), self.full_name))

        indent += indent_increment

        for subordinate in self.direct_reports:

            subordinate.print()

            if subordinate.has_direct_reports():
                indent += indent_increment

                indent_print('  ** Direct reports for {}...'.format(subordinate.full_name))
                for sub2 in subordinate.direct_reports:
                    sub2.print()
                    sub2.print_subordinates()
                indent_print('  ** Finished listing direct reports for {}'.format(subordinate.full_name))

                indent -= indent_increment

        indent -= indent_increment

class Company():
    def __init__(self):
        self.employees = []


    def print(self):
        print('This Company has {} employees'.format(len(self.employees)))

    def hire(self, employee: Person):
        self.employees.append(employee)


    def find(self, email: str) -> Person:
        for employee in self.employees:
            if employee.email.lower() == email.lower():
                return employee

        return None


    def organize(self):
        """
        For each employee - populate the direct reports list
        """

        for employee in self.employees:
            supervisor = self.find(employee.reports_to)
            if supervisor:
                supervisor.add_direct_report(employee)

def list_to_csv(list_item: list, file_name: str, preserve_column_order: bool=False):
    """
    Create CSV from list of dicts
    """

    output = []
    cols = []

    for row in list_item:

        if len(output) == 0:
            # Row 1 = column headers

            if preserve_column_order:
                output.append(row['track_column_order'])
                cols = row['track_column_order']

            else:
                output.append(sorted(row.keys()))
                for col in output[0]:
                    cols.append(col)

        temp_list = []
        for col in cols:
            temp_list.append(row[col])

        output.append(temp_list)
        
    with open(file_name, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(output)


    csv_file.close()
    


def csv_to_list(file_name: str, track_column_order: bool = False) -> list:
    """
    Given a CSV file this function will return
    an array of dictionaries
    """

    headerRow = True
    columns = []
    output = []

    with open(file_name, encoding='utf8') as csv_file:

        csv_reader = csv.reader(csv_file, delimiter=',')
        

        for row in csv_reader:
            if headerRow:

                # Use the first row as column names
                columns = row
                headerRow = False

            else:

                temp_object = {}
                for idx in range(len(row)):
                    temp_object[columns[idx]] = row[idx]

                if track_column_order:
                    temp_object['track_column_order'] = columns
                output.append(temp_object)


    return output

def indent_print(msg: str):
    print('{}{}'.format(
        ' ' * indent, 
        msg
    ))

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("-e", "--email", dest="email", default="", help="One or more email addresses separated by a space", nargs=argparse.REMAINDER)
    parser.add_argument('-s', '--single', dest="single_layer", default=False, action="store_true", help="Only go a single layer deep")

    args = parser.parse_args()

    
    # because we used argparse.REMAINDER for the email
    # the other flag will not be recognized if it comes after email.
    # let's check to see if -s or --single is one of the email addresses provided
    if '-s' or '--single' in args.email:
        try:
            args.email.remove('-s')
            args.single_layer = True
        except:
            pass
        try:
            args.email.remove('--single')
            args.single_layer = True
        except:
            pass
        # args.single_layer = True
    
    


    return args

def main():

    args = parse_arguments()
    
    # only go a single layer deep when gathering subordinates?
    single_layer = args.single_layer
    supervisors_to_pull = args.email

    if len(supervisors_to_pull) == 0:
        supervisor = input("Enter the email address for the supervisor(s): ")
        supervisors_to_pull = supervisor.split(' ')
    

    data = csv_to_list(DATA_FILE, track_column_order=True)




    # Create Person object for every employee
    company = Company()
    for row in data:
        person = Person(row)
        company.hire(person)


    company.organize()



    if len(supervisors_to_pull) == 1:

        supervisor = company.find(supervisors_to_pull[0])

        if supervisor:
            supervisor.subordinates_to_csv(single_layer)
        else:
            print("Unable to find {}".format(supervisors_to_pull[0]))

    else:

        output = []
        supervisor_names = []
        for supervisor_email in supervisors_to_pull:
            supervisor = company.find(supervisor_email)
            if supervisor:
                output.append(supervisor.raw_data)
                output.extend(supervisor.subordinates(return_people_objects=False, single_layer=single_layer))
                supervisor_names.append(supervisor.full_name)
            else:
                print("Unable to find {}".format(supervisor_email))

        if len(output) > 0:
            list_to_csv(
                output,
                '{}.csv'.format(' & '.join(supervisor_names)),
                preserve_column_order=True
            )






if __name__ == '__main__':
    # sys.stdout = open("deleteme.txt", "w")


    main()

    # sys.stdout.close()