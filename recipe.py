import os
import re
from datetime import datetime

class Recipe:
    '''Holds information associated with one recipe.

    Attributes:
        title (str): title of recipe
        ingredients (str): string of ingredients in the format as listed
            in the parse_ingredients method
        instructions (str): string containing all instructions for how to
            cook recipe
        oven_temp (int): if applicable, oven temperature for this recipe
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


        return cls(title, ingredients, instructions, tags=tags, notes=notes)



        os.chdir(old_cwd)

    @staticmethod
    def parse_ingredients(ingredients_raw):
        """
        Takes in a string containing the ingredients list of a recipe, and
        parses it into the list-of-tuples format usable by the class constructor
        Do not use mixed numbers like "1 1/2", instead use 1.5

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

            # parse fractions in first element

            ingredients.append((float(split[0]), split[1], ' '.join(split[2:])))
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
            ingredients_string += ' '.join([str(i) for i in ing]) + '\n'
        return ingredients_string


if __name__=='__main__':
    # r = Recipe("Salt Potatoes", '1 c potatoes \n 4 tbsp butter', "Mix potatoes and butter.\nCook until done.")
    # r.save_to_file()
    r = Recipe.read_from_file('Test_Recipe.txt')
    # print(r)
    print(r.title)
    print(r.ingredients)
    print(r.instructions)
    print(r.tags)
    print(r.notes)

    r.tags.append('breakfast??')
    r.save_to_file()

    # raw_ing = Recipe.unparse_ingredients([(1, 'c', 'flour'), (0.5, 'c', 'sugar')])
    # parsed = Recipe.parse_ingredients(raw_ing)
    # print(parsed)