from recipe import Recipe
import os

class Cookbook:
    '''
    Holds a cookbook full of recipes!

    Attributes:
        recipes (list): list of Recipe objects holding all of the recipes in
            the cookbook
    '''
    def __init__(self):
        self.recipes = []

    def __str__(self):
        return '\n'.join([r.title for r in self.recipes])

    def find(self, fil):
        '''
        Searches the recipes for a filter string, and returns a list of recipes
        that match the filter. Matches the filter in the title, recipe
        instructions 

        Args:
            fil (str): filter string to search for

        Returns:
            found (list): list of Recipe objects which match the filter string
        '''
        fil = fil.lower()
        found = []

        for rec in self.recipes:
            # search recipes by title, ingredient, or tag
            if fil in rec.title.lower():
                found.append(rec)
                continue
            if fil in '\t'.join(rec.tags):
                found.append(rec)
                continue

            for ing in rec.ingredients:
                if fil in ing[2].lower():
                    found.append(rec)
                    break

        return found

    def find_by_title(self, title):
        for rec in self.recipes:
            if rec.title==title:
                return rec
        return None

    def add_recipe(self, recipe):
        self.recipes.append(recipe)

    def delete_recipe(self, title):
        rec_to_delete = self.find_by_title(title)
        file_to_delete = rec_to_delete.get_filename()
        self.recipes.remove(rec_to_delete)
        # remove text file containing this recipe
        os.remove(file_to_delete)

    def add(self, title, ingredients, instructions, tags=None):
        '''
        Adds a recipe into the list of recipes. Takes same arguments as Recipe 
        constructor.

        Args: see Recipe class in file recipe.py
        '''
        self.recipes.append(Recipe(title, ingredients, instructions, tags=tags))

    def update(self, title, ingredients, instructions, tags=None):
        '''
        Finds a recipe by its title, and modifies the ingredients and 
        instructions.

        Args:
            ingredients (str): unparsed string containing ingredients data
            instructions (str): str containing new instructions for recipe
        '''
        rec = self.find_by_title(title)
        rec.ingredients = Recipe.parse_ingredients(ingredients)
        rec.instructions = instructions
        if tags:
            rec.tags = tags.split(', ')

    @classmethod
    def read_from_dir(cls, directory):
        '''
        Loads in a cookbook containing all recipe files in the given directory.
        Recipe files are expected to be saved in the format decribed in
        recipe.py.

        Args:
            directory (str): directory in which to search for recipe files.
                Relative to the directory in which this file is stored.
        '''
        old_cwd = os.getcwd()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        ckbk = cls()

        for fnam in os.listdir(directory):
            # this is the  mac file that auto-generates to store display
            # preferences in Finder
            if fnam == '.DS_Store': continue
            rec = Recipe.read_from_file(os.path.join(directory, fnam))
            ckbk.add_recipe(rec)

        os.chdir(old_cwd)
        return ckbk



if __name__ == '__main__':
    c = Cookbook()

    potat_recipe = Recipe('French Fries',
        [(2, 'lbs', 'potatoes'), (1, 'c', 'vegetable oil')],
        "Fill skillet with 1/2 inch of oil. Fry potatoes until golden brown.\nLay out on paper towels to dry.")
    tomat_recipe = Recipe('Fried Green Tomatoes',
        [(3, 'lbs', 'tomatoes'), (0.5, 'c', 'vegetable oil'), (1, 'c', 'breadcrumbs')],
        "Fill skillet with oil. Coat tomatoes in breadcrumbs. Fry until brown.")
    
    # potat_recipe.save_to_file()
    # tomat_recipe.save_to_file()

    c.add(potat_recipe)
    c.add(tomat_recipe)
    
    # print(c)
    # print(c.find('potato'))
    # print(c.find('green'))

    c2 = Cookbook.read_from_dir('Recipe')
    print(c2)
