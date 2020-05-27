import argparse
import csv
import logging
import os
import random
import sys


class FinnishPersonGenerator:

    def __init__(self, main_data_dir):

        # Assign properties
        self.__main_data_dir = main_data_dir
        # Weighted name picker lists (wsl = weighted select list)
        self.__weights_male_first = []
        self.__weights_female_first = []
        self.__weights_last = []
        # dict = dictionaries (in list form) that map numbers in the wsl to actual names
        self.__names_male_first = []
        self.__names_female_first = []
        self.__names_last = []
        # Initiate random seed for generator functions
        random.seed()
        # Load data
        self.load_people_objects()


    def load_people_objects(self):

        # Male first (given) names
        male_fn_file = os.sep.join((self.__main_data_dir, 'person-names/csv', 'etunimitilasto-2020-02-06-miehet.csv'))
        with open(male_fn_file, encoding='utf8') as infile:
            inreader = csv.reader(infile)
            next(inreader)  # skip the header row
            ctr = 0
            for row in inreader:
                (fname,weight) = (row[0],int(row[1].replace(',', '')))
                self.__names_male_first.append(fname)
                self.__weights_male_first.append(weight)
                ctr += 1

        # Female first (given) names
        female_fn_file = os.sep.join((self.__main_data_dir, 'person-names/csv', 'etunimitilasto-2020-02-06-naiset.csv'))
        with open(female_fn_file, encoding='utf8') as infile:
            inreader = csv.reader(infile)
            next(inreader)  # skip the header row
            ctr = 0
            for row in inreader:
                (fname,weight) = (row[0],int(row[1].replace(',', '')))
                self.__names_female_first.append(fname)
                self.__weights_female_first.append(weight)
                ctr += 1

        # Last (family) names
        family_name_file = os.sep.join((self.__main_data_dir, 'person-names/csv', 'sukunimitilasto-2020-02-06.csv'))
        with open(family_name_file, encoding='utf8') as infile:
            inreader = csv.reader(infile)
            next(inreader)  # skip the header row
            ctr = 0
            for row in inreader:
                (lname,weight) = (row[0],int(row[1].replace(',', '')))
                self.__names_last.append(lname)
                self.__weights_last.append(weight)
                ctr += 1


    def get_a_name(self, gender=None):
        '''
        Returns a name in (given,family) tuple.
        Randomly picks a gender if none is specified
        Gender is in English - "m" or "f"
        '''

        lname = random.choices(self.__names_last, self.__weights_last)[0]
        fname = None
        if gender is None:
            gender = random.choice(['f', 'm'])
        if gender == 'm':
            fname = random.choices(self.__names_male_first, self.__weights_male_first)[0]
        else:
            fname = random.choices(self.__names_female_first, self.__weights_female_first)[0]

        return((fname,lname))


class FinnishAddressGenerator:

    def __init__(self, main_data_dir):

        # Assign properties
        self.__main_data_dir = main_data_dir
        # Mappings
        self.__postal_code_to_city = {}
        self.__postal_code_addresses = {}  # {post code: [(street,unit,lat,long)....] }
        self.__population_by_postal_code = {}  # {post code: (total pop, male pop, female pop)}
        # Initiate random seed for generator functions
        random.seed()
        # Load data
        self.load_postal_code_city()
        self.load_population_stats()

    def get_postal_codes(self): return sorted(self.__population_by_postal_code.keys())

    def get_city_by_postal_code(self, postal_code): return self.__postal_code_to_city[postal_code]

    def get_population_by_postal_code(self, postal_code): return self.__population_by_postal_code[postal_code]


    def load_postal_code_city(self):
        file_loc = os.sep.join((self.__main_data_dir, 'posti', 'PCF_20200523.dat'))
        with open(file_loc, encoding='latin-1') as infile:    # This file is ANSI encoded
            for row in infile.readlines():
                postcode = row[13:18] # Fixed width file
                city_fi = row[179:199].strip()
                self.__postal_code_to_city[postcode] = city_fi
    

    def load_population_stats(self):
        file_loc = os.sep.join((self.__main_data_dir, 'population-stats', '001_12ey_2018.csv'))
        with open(file_loc, encoding='utf8') as infile:
            csv_reader = csv.reader(infile)
            next(csv_reader)
            for row in csv_reader:
                (postal_code_area, total_population, male_population, female_population) = row
                postal_code = postal_code_area[0:5]
                # Right now, this just uses total population
                self.__population_by_postal_code[postal_code] = int(total_population)
        

    def load_postal_code_addresses(self, postal_code):
        # To save memory, this procedure loads addresses by the first number of a postal code.
        # If you call this procedure and the necessary posal code is already loaded - then it just does nothing
        dict_length = len(self.__postal_code_addresses.keys())
        keys = list(self.__postal_code_addresses.keys())
        if dict_length > 0 and keys[0][0] == postal_code[0]:
            return None
        self.__postal_code_addresses = {}
        file_loc = os.sep.join((self.__main_data_dir, 'openaddr-collected-europe', 'fi', 'countrywide-fi.csv'))
        if not os.path.exists(file_loc):
            raise Exception('\n***You will need to download address files from openaddresses.io.  Please see the openaddr-collected-europe subdirectory for details.')
        with open(file_loc, encoding='utf8') as infile:
            csv_reader = csv.reader(infile)
            next(csv_reader)
            for row in csv_reader:
                (long, lat,addr_number, street, unit, city, district, region, postcode, rowid, rowhash) = row
                if postcode[0] == postal_code[0]:
                    # Add it to the dictionary
                    if postcode not in self.__postal_code_addresses:
                        self.__postal_code_addresses[postcode] = []
                    self.__postal_code_addresses[postcode].append((street, addr_number, long, lat))


    def get_address_in_postal_code(self, postal_code):
        # The postal code population file is only good at 4-digit granularity
        self.load_postal_code_addresses(postal_code)

        potential_postal_codes = []
        potential_weights = [] # number of units per postal code
        
        for pca_code in self.__postal_code_addresses:
            if pca_code[0:4] == postal_code[0:4]:
                potential_postal_codes.append(pca_code)
                potential_weights.append(len(self.__postal_code_addresses[pca_code]))
        
        chosen_code = random.choices(potential_postal_codes,weights=potential_weights)[0]
        
        if chosen_code not in self.__postal_code_addresses:
            return ('','',25.0,66.5)
        else:
            return random.choice(self.__postal_code_addresses[chosen_code])
    

def get_arguments(args, arg_defs):
    '''
    Read and parse program arguments.
    '''

    parser = argparse.ArgumentParser()
    for arg_name in arg_defs.keys():
        short_flag = '-' + arg_defs[arg_name]['short_flag']
        long_flag = '--' + arg_name
        default_value = arg_defs[arg_name]['default_value']
        arg_type = arg_defs[arg_name]['type']
        description = arg_defs[arg_name]['description']
        parser.add_argument(
            short_flag, long_flag, dest=arg_name, type=arg_type,
            default=default_value, help=description
        )
    args = parser.parse_args(args[1:])
    return args


def main(argv):

    output_filename = 'fakepeople_fi.csv'

    # Define and read program input arguments
    program_args = {
        'sample_rate': {
            'short_flag': 'r',
            'type': float,
            'default_value': .01,
            'description': 'The sampling rate over the total population.'
        },
        'data_dir': {
            'short_flag': 'd',
            'type': str,
            'default_value': 'data',
            'description': 'Data directory path on the host system.'
        },
        'output_dir': {
            'short_flag': 'o',
            'type': str,
            'default_value': 'output',
            'description': 'Output directory path on the host system.'
        },
        'log_level': {
            'short_flag': 'l',
            'type': str,
            'default_value': 'warning',
            'description': 'Logging output level.'
        }
    }
    args = get_arguments(argv, program_args)

    # Set up logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(level=log_level, format=log_format)

    person_generator = FinnishPersonGenerator(main_data_dir=args.data_dir)
    address_generator = FinnishAddressGenerator(main_data_dir=args.data_dir)

    output_file = os.sep.join((args.output_dir, output_filename))
    logging.info('Beginning output to ' + output_file)
    total_samples = 0
    with open(output_file, mode='w', encoding='utf8', newline='') as ow: # change the newline if using Linux
        cw = csv.writer(ow)
        postal_codes = address_generator.get_postal_codes()
        for postcode in postal_codes:
            population = address_generator.get_population_by_postal_code(postcode)
            num_samples = int(population * args.sample_rate)
            logging.info('Processing postal code {0} ({1} samples)'.format(postcode, num_samples))
            for _ in range(num_samples):
                (first_name, last_name) = person_generator.get_a_name()
                (street, unit, lat, long) = address_generator.get_address_in_postal_code(postcode)
                city = address_generator.get_city_by_postal_code(postcode)
                row = (first_name, last_name, street, unit, city, postcode, lat, long)
                cw.writerow(row)
            total_samples += num_samples
    logging.info((
        'Generated total {} samples for {} postal codes with sampling rate {:.4f}'
        .format(total_samples, len(postal_codes), args.sample_rate)
    ))


if __name__ == '__main__':

    main(sys.argv)
