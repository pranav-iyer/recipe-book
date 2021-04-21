from cookbook import Cookbook
import os
import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox
import logging
logging.basicConfig(level=logging.INFO)

class AutoScrollbar(tk.Scrollbar):
    # TAKEN from effbot.org/zone/tkinter-autoscrollbar.htm
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        tk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise TclError("cannot use pack with this widget")
    def place(self, **kw):
        raise TclError("cannot use place with this widget")



class GUI:

    def __init__(self, directory="Recipes"):

        # look for previously saved recipes in the Recipes folder,
        # if there are none, just create a new Cookbook object
        self.directory = directory
        old_cwd = os.getcwd()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        if os.path.exists(self.directory):
            self.ckbk = Cookbook.read_from_dir(self.directory)
        else:
            self.ckbk = Cookbook()

        os.chdir(old_cwd)

        self.main_window = None

        '''
        for i in range(100):
            self.ckbk.add(f"Recipe {i+1}", f"1 c flour, {i+1} tbsp water", "Make paste. Cook on stovetop until not sticky.")
        '''


    def run(self):
        """
        Main function for using this class. Runs the tkinter window and contains
        all the logic.
        """
        #————————————————————setup window frame—————————————————————————————————
        self.main_window = tk.Tk()
        self.main_window.title("Recipe Master")
        self.main_window.minsize(700,500)
        self.main_window.protocol("WM_DELETE_WINDOW", self._save_and_close)
        self.main_window.rowconfigure(0, weight=1, minsize=500)
        self.main_window.columnconfigure(0, weight=1, minsize=200)
        self.main_window.columnconfigure(1, weight=4, minsize=500)


        #—————————————————————recipe list sidebar———————————————————————————————
        sidebar = tk.Frame(master=self.main_window)
        sidebar.config(background='white')
        sidebar.grid(row=0, column=0, sticky='nsew')

        sidebar.rowconfigure(0, minsize=30)
        sidebar.rowconfigure(1, weight=1)
        sidebar.rowconfigure(2, weight=0)
        sidebar.columnconfigure(0, weight=1)

        #----------------------------SEARCHBAR----------------------------------

        # create stringvar to hold text that is in the entry box. Whenever it is
        # changed the list will update
        self.search_text = tk.StringVar()

        searchbar = tk.Entry(master=sidebar, textvariable=self.search_text,
                highlightthickness=0, borderwidth=4, relief=tk.FLAT)

        def focus_off_searchbar(event):
            if self.search_text.get() == '':
                searchbar.config(foreground='gray')
                self.search_text.set('Search...')
            return None

        def focus_on_searchbar(event):
            if self.search_text.get() == 'Search...':
                searchbar.config(foreground='black')
                self.search_text.set('')
            return None

        focus_off_searchbar(None)

        searchbar.bind('<FocusIn>', focus_on_searchbar)
        searchbar.bind('<FocusOut>', focus_off_searchbar)


        searchbar.grid(row=0, column=0, columnspan=2, sticky='nsew')

        #-----------------------------recipe list-------------------------------

        # recipe listbox ...
        self.recipe_list = tk.Listbox(master=sidebar, borderwidth=4,
            selectmode=tk.SINGLE, relief=tk.FLAT)
        self.recipe_list.grid(row=1, column=0, columnspan=2, sticky='nsew')

        recipe_list_scrollbar_x = AutoScrollbar(master=sidebar,
            orient='horizontal', command=self.recipe_list.xview,
            highlightthickness=0, borderwidth=0)
        recipe_list_scrollbar_x.grid(row=2, column=0, sticky='sew')

        recipe_list_scrollbar_y = AutoScrollbar(master=sidebar,
            command=self.recipe_list.yview)
        recipe_list_scrollbar_y.grid(row=1, column=1, sticky='nse')

        self.recipe_list.config(xscrollcommand=recipe_list_scrollbar_x.set)
        self.recipe_list.config(yscrollcommand=recipe_list_scrollbar_y.set)

        # configure recipe_list so that it will update when the searchbar
        # is changed
        self.search_text.trace_add('write', self._update_recipe_list)

        self._update_recipe_list(0,0,0)

        # add button at bottom of recipe list.
        add_button = tk.Button(master=sidebar, text='Add New Recipe',
            command=self._add_new_recipe_window, borderwidth=0,
            highlightthickness=0)
        add_button.grid(row=3, column=0, columnspan=2, sticky='nsew')

        rc_options = tk.Menu(master=sidebar, tearoff=0)

        #---------------------------edit and delete options---------------------

        rc_options.add_command(label='Edit')
        rc_options.add_command(label='Delete')

        def popup_rc_options(event):
            # show the clicked on recipe in the main panel
            idx_to_show = self.recipe_list.nearest(event.y)
            title_to_show = self.recipe_list.get(idx_to_show)
            recipe_to_show = self.ckbk.find_by_title(title_to_show)

            self._show_recipe_in_main(recipe_to_show)

            item_clicked = self.recipe_list.nearest(event.y)
            self.recipe_list.selection_clear(0, tk.END)
            self.recipe_list.selection_set(item_clicked)
            self.recipe_list.update()
            title_clicked = self.recipe_list.get(item_clicked)
            logging.info(f"Right Click on recipe {title_clicked}!")

            # update what the edit and delete buttons do 
            rc_options.entryconfig('Edit',
                command= lambda: self.edit_window(title_clicked))
            rc_options.entryconfig('Delete',
                command= lambda: self.delete_window(title_clicked))

            rc_options.post(event.x_root, event.y_root)

        self.recipe_list.bind("<ButtonRelease-2>", popup_rc_options)

        #—————————————————————recipe view (main panel)——————————————————————————

        main_panel = tk.Frame(master=self.main_window, borderwidth=1)
        main_panel.config(background='white')
        main_panel.grid(row=0, column=1, sticky='nsew')
        main_panel.rowconfigure(0, weight=0, minsize=30)
        main_panel.rowconfigure(1, weight=1)
        main_panel.rowconfigure(2, weight=0)
        main_panel.columnconfigure(0, weight=1)

        self.title_label = tk.Label(master=main_panel,
                font='Helvetica 18 bold', bg='white')
        self.title_label.grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.recipe_body = tk.Text(master=main_panel, state='disabled',
            font='TkDefaultFont', height=27, width=20, wrap=tk.WORD,
            borderwidth=0, highlightthickness=0)
        self.recipe_body.config(background='white')
        self.recipe_body.grid(row=1, column=0, sticky='nsew')

        recipe_body_scrollbar = AutoScrollbar(master=main_panel,
            command=self.recipe_body.yview)
        recipe_body_scrollbar.grid(row=1, column=1, sticky='nse')

        self.recipe_body.config(yscrollcommand=recipe_body_scrollbar.set)

        self.recipe_tags = tk.Label(master=main_panel, anchor='nw',
                justify=tk.LEFT, bg='white')
        self.recipe_tags.grid(row=2, column=0, columnspan=2, sticky='nsew')

        # I want the recipe_body label to refigure its wrapping when the window 
        # is resized.
        def update_recipe_body_width(event):
            main_panel.update()
            wrap_length = main_panel.winfo_width() - 5
            # recipe_body.config(wraplength=wrap_length)

        main_panel.bind('<Configure>', update_recipe_body_width)

        #—————————————showing recipe in main on click————————————————————
        # bind click to show recipe in main panel
        def select_recipe(event):
            idx_to_show = self.recipe_list.nearest(event.y)
            title_to_show = self.recipe_list.get(idx_to_show)
            recipe_to_show = self.ckbk.find_by_title(title_to_show)

            self._show_recipe_in_main(recipe_to_show)

        self.recipe_list.bind('<Button-1>', select_recipe)

        self._show_recipe_in_main(self.ckbk.recipes[0])
        self.recipe_list.select_set(0)

        #————————————————————————main loop——————————————————————————————————————
        self.main_window.mainloop()

    def _show_recipe_in_main(self, recipe_to_show):

        self.title_label.config(text=recipe_to_show.title)

        # format recipe text in main body
        recipe_text = ''
        recipe_text += recipe_to_show.get_ingredients()
        recipe_text += '----------------------------------------\n'
        recipe_text += recipe_to_show.instructions
        self.recipe_body.config(state='normal')
        self.recipe_body.delete('1.0', tk.END)
        self.recipe_body.insert('1.0', str(recipe_text))
        self.recipe_body.config(state='disabled')


        # format recipe tags into the tags section
        recipe_tag_text = 'Tags: '
        for tag in recipe_to_show.tags:
            recipe_tag_text += tag +', '
        if recipe_tag_text != "Tags: ":
            recipe_tag_text = recipe_tag_text[:-2]
        self.recipe_tags.config(text=str(recipe_tag_text))


    def _load_all_recipes(self):
        """
        Loads all of the recipes into the recipe list in the taskbar, for use
        on startup, or after search has been cleared.
        """
        self.recipe_list.delete(0, tk.END)
        for recipe in self.ckbk.recipes:
            self.recipe_list.insert(tk.END, recipe.title)

    def _update_recipe_list(self, var, idx, mode):
        """
        Callback function for the stringvar in the searchbar Entry.
        When the text in the searchbar is updated, this changes the recipe list
        to reflect the string's value. Arguments are required to make signature
        match up, but are not used.
        """
        fil = self.search_text.get()
        if fil =='Search...': fil=''
        recipes_to_show = self.ckbk.find(fil)

        self.recipe_list.delete(0, tk.END)
        for recipe in recipes_to_show:
            self.recipe_list.insert(tk.END, recipe.title)

    def _add_new_recipe_window(self):
        """
        Displays popup window which prompts user for information about recipe
        """
        nrw = tk.Tk()

        nrw.title("Add New Recipe")
        nrw.resizable(False, False)

        nrw.rowconfigure(3, minsize=30)

        title_entry = tk.Entry(master=nrw, borderwidth=0, justify=tk.CENTER,
            highlightthickness=0, font='Helvetica 18 bold')
        ingredients_text = tk.Text(master=nrw, relief=tk.SUNKEN, borderwidth=1,
            highlightthickness=0, height=20)
        instructions_text = tk.Text(master=nrw, relief=tk.SUNKEN, borderwidth=1,
            highlightthickness=0, height=20)
        tags_entry = tk.Entry(master=nrw, borderwidth=0, justify=tk.LEFT,
            highlightthickness=0)

        ingredients_scrollbar = AutoScrollbar(master=nrw, orient=tk.VERTICAL,
            command=ingredients_text.yview)
        instructions_scrollbar = AutoScrollbar(master=nrw, orient=tk.VERTICAL,
            comman=instructions_text.yview)

        ingredients_text.config(yscrollcommand=ingredients_scrollbar.set)
        instructions_text.config(yscrollcommand=instructions_scrollbar.set)



        def add_recipe_callback():
            title_to_add = title_entry.get()

            # if title is empty, tell the user to enter a title
            if not title_to_add.strip():
                messagebox.showwarning(title="Enter a Title", message="No \
title entered. Please enter a title for the recipe and try again.")
                return
            # if this title is already in the cookbook, tell the user and tell
            # them to choose a different title
            if self.ckbk.find_by_title(title_to_add):
                messagebox.showwarning(title="Recipe Already Exists",
                message="A recipe with this title already exists in the \
cookbook. Please choose a different title and try again.")
                return

            ings_to_add = ingredients_text.get('1.0', tk.END)
            instr_to_add = instructions_text.get('1.0', tk.END)
            tags_to_add = tags_entry.get()
            tags_to_add = tags_to_add.split(', ')
            self.ckbk.add(title_to_add, ings_to_add, instr_to_add, tags=tags_to_add)

            nrw.destroy()

            self._update_recipe_list(0,0,0)



        submit_button = tk.Button(master=nrw, text="Add Recipe",
            command=add_recipe_callback)

        tags_entry.bind("<Return>", lambda e: submit_button.invoke())

        title_entry.grid(row=0, column=0, columnspan=2, sticky='nsew')
        ingredients_text.grid(row=1, column=0, sticky='nsew')
        instructions_text.grid(row=2, column=0, sticky='nsew')

        ingredients_scrollbar.grid(row=1, column=1, sticky='nse')
        instructions_scrollbar.grid(row=2, column=1, sticky='nse')

        tags_entry.grid(row=3, column=0, sticky='nsew')
        submit_button.grid(row=4, column=0, columnspan=2, sticky='nsew')

        nrw.mainloop()

    def edit_window(self, title):

        ew = tk.Tk()

        ew.title("Edit Recipe")
        ew.resizable(False, False)

        ew.rowconfigure(3, minsize=30)

        title_label = tk.Label(master=ew, borderwidth=0, text=title,
            font='Helvetica 18 bold')
        ingredients_text = tk.Text(master=ew, relief=tk.SUNKEN, borderwidth=1,
            highlightthickness=0, height=20)
        instructions_text = tk.Text(master=ew, relief=tk.SUNKEN, borderwidth=1,
            highlightthickness=0, height=20)
        tags_entry_frame = tk.Frame(master=ew)
        tags_entry_frame.columnconfigure(1, weight=1)
        tags_label = tk.Label(master=tags_entry_frame, text='Tags:')
        tags_entry = tk.Entry(master=tags_entry_frame, borderwidth=0,
                highlightthickness=0)

        ingredients_scrollbar = AutoScrollbar(master=ew, orient=tk.VERTICAL,
            command=ingredients_text.yview)
        instructions_scrollbar = AutoScrollbar(master=ew, orient=tk.VERTICAL,
            command=instructions_text.yview)

        ingredients_text.config(yscrollcommand=ingredients_scrollbar.set)
        instructions_text.config(yscrollcommand=instructions_scrollbar.set)

        # fill in the text boxes with the old data
        old_ings = self.ckbk.find_by_title(title).get_ingredients()
        old_instr = self.ckbk.find_by_title(title).instructions
        old_tags = ', '.join(self.ckbk.find_by_title(title).tags)

        ingredients_text.insert(tk.END, old_ings)
        instructions_text.insert(tk.END, old_instr)
        tags_entry.insert(tk.END, old_tags)

        def edit_recipe_callback():
            ings_to_edit = ingredients_text.get('1.0', tk.END)
            instr_to_edit = instructions_text.get('1.0', tk.END)
            tags_to_edit = tags_entry.get()
            self.ckbk.update(title, ings_to_edit, instr_to_edit,
                    tags=tags_to_edit)

            ew.destroy()

            self._update_recipe_list(0,0,0)
            self._show_recipe_in_main(self.ckbk.find_by_title(title))



        submit_button = tk.Button(master=ew, text="Save Recipe",
            command=edit_recipe_callback)

        # make it so that clicking enter when you are in the last text entry
        # (the one for the tags) will invoke the submit button
        tags_entry.bind("<Return>", lambda e: submit_button.invoke())

        title_label.grid(row=0, column=0, columnspan=2, sticky='nsew')
        ingredients_text.grid(row=1, column=0, sticky='nsew')
        instructions_text.grid(row=2, column=0, sticky='nsew')

        ingredients_scrollbar.grid(row=1, column=1, sticky='nse')
        instructions_scrollbar.grid(row=2, column=1, sticky='nse')

        tags_entry_frame.grid(row=3, column=0, columnspan=2, sticky='nsew')
        tags_label.grid(row=0, column=0)
        tags_entry.grid(row=0, column=1, sticky='nsew')
        submit_button.grid(row=4, column=0, columnspan=2, sticky='nsew')

        ew.mainloop()

    def delete_window(self, title):

        dw = tk.Tk()

        dw.title("Delete Recipe?")
        dw.grab_set()

        dw.resizable(False,False)

        rusure_label = tk.Label(master=dw, borderwidth=0,
            text='Are you sure you want to delete this recipe?\nThis cannot be undone.')


        def really_delete():
            self.ckbk.delete_recipe(title)

            dw.destroy()

            self._update_recipe_list(0,0,0)

        def cancel_delete():

            dw.destroy()
            self._update_recipe_list(0,0,0)

        yes_button = tk.Button(master=dw, text='Delete', command=really_delete)
        no_button = tk.Button(master=dw, text='Cancel', command=cancel_delete)

        rusure_label.grid(row=0, column=0, columnspan=2, sticky='nsew')
        yes_button.grid(row=1, column=0, sticky='nsew')
        no_button.grid(row=1, column=1, sticky='nsew')

        dw.mainloop()


    def _save_and_close(self):
        """
        Function which is called when the tkinter window is closed. Writes
        all of the recipes in the cookbook to files in a directory for use
        later.
        """

        for rec in self.ckbk.recipes:
            rec.save_to_file()
        self.main_window.destroy()

if __name__ == '__main__':
    g = GUI()
    g.run()
