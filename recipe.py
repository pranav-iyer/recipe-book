import os
import re
from datetime import datetime
import csv
import sys
from math import isclose, floor
import logging
logging.basicConfig(level=logging.INFO)

#read in the unit conversion as a dictionary, so that it can be used to parse
# ingredient lists.
unit_conversions = {}
with open('tables/unit_conversions.txt', 'r', newline='') as f:
    reader = csv.reader(f, delimiter='\t')
    next(reader)
    for row in reader:
        unit_conversions[row[0]] = row[1]

class Recipe:
    '''Holds information associated with one recipe.

    Attributes:
        title (str): title of recipe
        ingredients (str): string of ingredients in the format as listed
            in the parse_ingredients method
        instructions (str): string containing all instructions for how to
            cook recipe
    '''

    def __init__(self, title, ingredients, instructions, tags=None, notes=None):
        self.title = title
        self.ingredients = Recipe.parse_ingredients(ingredients)
        self.instructions = instructions.strip()

        if not tags:
            self.tags = []
        else:
            self.tags = tags

        if not notes:
            self.notes = []
        else:
            self.notes = notes

    def __str__(self):
        recipe_string = self.title + '\n--------\n'
        for ing in self.ingredients:
            recipe_string += '\t'.join(ing) + '\n'
        recipe_string += '--------\n'
        recipe_string += self.instructions
        return recipe_string

    def get_filename(self, directory=None):
        '''
        Returns the filename where the data for this recipe should be saved.
        Also creates any needed directories that may not exist.

        Args:
            directory (str or None): if None, the directory will be autofilled
                to "Recipes". Otherwise, it is saved in the format of
                <directory>/<title>.txt
        '''
        if not directory:
            if not os.path.exists('Recipes'):
                os.makedirs('Recipes')
            return f'Recipes/{self.title.replace(" ", "_") + ".txt"}'
        else:
            if not os.path.exists(directory):
                os.makedirs(directory)
            return f'{directory}/{self.title.replace(" ", "_") + ".txt"}'

    def save_to_file(self, **kwargs):
        """
        Saves the recipe object to a text file. The path is relative to the
        directory this file is saved in. Can also take any kwargs taken by
        get_filename()
        """
        old_cwd = os.getcwd()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        with open(self.get_filename(**kwargs), 'w') as f:
            f.write(f"{self.title}\n\n")

            f.write(self.get_ingredients())
            f.write('--------\n')
            f.write(f"{self.instructions}\n")
            f.write('--------\n')

            # write tags and notes
            if self.tags:
                f.write("\n".join(self.tags) + '\n')
            f.write('--------\n')

            if self.notes:
                notes_strings = [n[0].strftime('%Y-%m-%d') + f"\t{n[1]}" for n in self.notes]
                f.write('\n'.join(notes_strings) + '\n')
            f.write('--------\n')


        os.chdir(old_cwd)

    def get_ingredients(self):
        """
        Returns the ingredients of the recipe in a nicely formatted string.
        """
        return Recipe.unparse_ingredients(self.ingredients)

    @classmethod
    def read_from_file(cls, filename):
        '''
        Reads in a Recipe object from its text  file

        Args:
            filename (str): path to file from which to load object. Should be
                relative to the directory containing this file.

        Returns:
            recipe (Recipe): recipe object created from data in text file.
        '''
        old_cwd = os.getcwd()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        title = ''
        ingredients = ''
        instructions = ''
        tags = []
        notes = []

        logging.info(f"Reading recipe in {filename}")
        with open(filename, 'r') as f:
            title = f.readline()[:-1]
            f.readline()[:-1]

            done_ingredients = False
            while not done_ingredients:
                line = f.readline()
                if line != '--------\n':
                    ingredients += line
                else:
                    done_ingredients = True


            done_instructions = False
            while not done_instructions:
                line = f.readline()
                if line != '--------\n':
                    instructions += line
                else:
                    done_instructions = True

            # read in tags
            done_tags = False
            while not done_tags:
                line = f.readline()
                if line != '--------\n':
                    tags.append(line[:-1])
                else:
                    done_tags = True

            # read in notes
            done_notes = False
            while not done_notes:
                line = f.readline()
                if line == '\n': continue
                if line != '--------\n':
                    note_to_add = line.strip().split('\t')
                    note_to_add[0] = datetime.strptime(note_to_add[0], '%Y-%m-%d')
                    notes.append(tuple(note_to_add))
                else:
                    done_notes = True


        os.chdir(old_cwd)

        return cls(title, ingredients, instructions, tags=tags, notes=notes)


    @staticmethod
    def parse_line_to_ingredient(line):
        """
        Takes in one line of text, assumed to represent one ingredient. Parses
        it into a 3-tuple to be stored in a recipe object. First element number,
        second contains unit ['' if no unit], third element ingredient name.

        Args:
            line (str): line of text to parse

        Returns:
            ingredient (tuple): parsed tuple
        """
        split = re.split(r'\s', line)

        # parse first element to number
        number = float(split.pop(0))

        #parse second to unit
        unit = split.pop(0)
        name = ''
        if unit in unit_conversions.keys():
            unit = unit_conversions[unit]
        else:
            name = unit
            unit = ''

        # parse rest to name of ingredient
        if name and split: name += ' '

        name += ' '.join(split)

        return (number, unit, name)


    @staticmethod
    def parse_ingredients(ingredients_raw):
        """
        Takes in a string containing the ingredients list of a recipe, and
        parses it into the list-of-tuples format usable by the class constructor

        Args:
            ingredients_raw (str): list of ingredients, of the form:
                1 cup potatoes, 2 cups green beans, 1 tbsp butter

        Returns:
            ingredients (list): list of tuples containing ingredient data
                to store.
        """
        ingredients_raw = ingredients_raw.strip()
        separated_ingredients = re.split(r',\s*|\s*\n\s*', ingredients_raw)
        ingredients = []
        for ing_string in separated_ingredients:
            split = re.split(r'\s', ing_string)

            # parse fractions in first and second elements
            number = 0
            # first, check if it is a mixed number in the form of "1 3/4"
            if type(Recipe.parse_fraction(' '.join(split[:2]))) != str:
                number = Recipe.parse_fraction(' '.join(split[:2]))
                del split[:2]
            elif type(Recipe.parse_fraction(split[0])) != str:
                number = Recipe.parse_fraction(split[0])
                del split[0]
            else:
                # could not parse the number—don't even try to parse the units,
                # just put everything into the item slot
                ingredients.append((0, '', ' '.join(split)))
                continue

            # parse units
            unit=''
            if split[0] in unit_conversions.keys():
                unit =  unit_conversions[split[0]]
                del split[0]

            ingredients.append((number, unit, ' '.join(split)))
        return ingredients

    @staticmethod
    def unparse_ingredients(ingredients):
        """
        Takes in the list-of-tuple format ingredients, and converts into a
        string that can be read back

        Args:
            ingredients (list): list of tuples containing ingredient data
                to store.

        Returns:
            ingredients_raw (str): list of ingredients, of the form:
                1 cup potatoes\n2 cups green beans\n1 tbsp butter
        """


        ingredients_string = ''
        for ing in ingredients:
            ing = list(ing)
            # unparse the unit (if number >1, add plural to units that need it)
            if ing[0] > 1:
                if ing[1][-2:] == '^^':
                    ing[1] = ing[1][:-2] + 'es'
                elif ing[1][-1:] == '^':
                    ing[1] = ing[1][:-1] + 's'
            else:
                ing[1] = ing[1].replace('^', '')


            # if the number is 0, then this means we couldn't parse the number/unit
            # when it was inputted. this means that the whole text of the
            # ingredient is in the third element; just return this
            if ing[0] == 0:
                ingredients_string += ing[2] + '\n'
                continue

            ing[0] = Recipe.unparse_fraction(float(ing[0]))
            if ing[1]:
                ingredients_string += ' '.join(ing) + '\n'
            else:
                ingredients_string += str(ing[0]) + ' ' + ing[2] + '\n'
        return ingredients_string

    @staticmethod
    def parse_fraction(fraction_string):
        """
        function for parsing fraction strings ("1/2", "1/3") into floats (0.5,
        0.3333333). Can understand mixed numbers like "1 1/2" or "2-1/4". Will also
        pass through any floats if possible (i.e. input "4.134" returns float
        4.134). If all parsing fails, will return the input unchanged (i.e. input
        "4.5" returns "4.5")
        """
        # parse integer part
        whole_number = 0
        remainder = ''
        if len(fraction_string.split(' ')) > 1:
            try:
                split_fraction = fraction_string.split(' ')
                whole_number = int(split_fraction[0])
                remainder = split_fraction[1]
            except:
                pass
        elif len(fraction_string.split('-')) > 1:
            split_fraction = fraction_string.split('-')
            whole_number = int(split_fraction[0])
            remainder = split_fraction[1]
        else:
            whole_number = 0
            remainder = fraction_string

        if len(remainder.split('/')) == 2:
            num, denom = [int(x) for x in remainder.split('/')]
            return whole_number + num / denom
        else:
            try:
                return float(fraction_string)
            except:
                return fraction_string

    @staticmethod
    def unparse_fraction(fraction_float, tol=1e-3):
        '''
        function for turning decimals of fractions into nicely printable fractions
        like 1/3 and 3/4. Handles mixed numbers (i.e. 1.5 -> "1 1/2"). Anything it
        cannot parse will be simply passed through as the string version (i.e.
        2.9185 -> "2.9185").
        '''

        # check if the number is close to an integer, then we can print it as
        # an int
        for n in range(1, 200):
            if isclose(fraction_float, n, rel_tol=tol):
                return str(int(n))

        # check if the fraction is greater than 1 (then it will be a mixed
        # number) and then strip off the integer part
        if fraction_float >= 1:
            whole_num = floor(fraction_float)
            remainder = fraction_float - whole_num
        else:
            whole_num = 0
            remainder = fraction_float

        possible_denoms = [2, 3, 4, 8]
        for d in possible_denoms:
            for n in range(1, d):
                if  isclose(d*remainder, n, rel_tol=tol):
                    if whole_num:
                        return f"{whole_num} {n}/{d}"
                    else:
                        return f"{n}/{d}"
        return str(fraction_float)

if __name__=='__main__':
    # r = Recipe("Salt Potatoes", '1 c potatoes \n 4 tbsp butter', "Mix potatoes and butter.\nCook until done.")
    # r.save_to_file()
    # r = Recipe.read_from_file('Test_Recipe.txt')
    # print(r)
    # print(r.title)
    # print(r.ingredients)
    # print(r.instructions)
    # print(r.tags)
    # print(r.notes)

    # r.tags.append('breakfast??')
    # r.save_to_file()

    # raw_ing = Recipe.unparse_ingredients([(1, 'c', 'flour'), (0.5, 'c', 'sugar')])
    parsed = Recipe.parse_ingredients("1 egg\nA whole piece of ginger\n25 c flour")
    print(Recipe.unparse_ingredients(parsed))

    print(unit_conversions.keys())
