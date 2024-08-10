# databases.py
import tkinter as tk
from tkinter import ttk
from django_extensions.management.commands.show_urls import Command

class DatabasesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        # Add widgets to display database information
        label = tk.Label(self, text='Databases Information', font=('Helvetica', 16, 'bold'))
        label.pack(pady=20)

        # Get database information using django-extensions
        command = Command()
        # Add the required options
        options = {'no_color': False, 'language': 'en-us'}
        # Use the handle method with options
        database_info = command.handle(**options)

        # Display information in a treeview
        tree = ttk.Treeview(self, columns=('App', 'Model', 'Name', 'Type', 'Size'), show='headings')
        tree.heading('App', text='App')
        tree.heading('Model', text='Model')
        tree.heading('Name', text='Name')
        tree.heading('Type', text='Type')
        tree.heading('Size', text='Size')

        for entry in database_info:
            tree.insert('', 'end', values=(entry['app'], entry['model'], entry['name'], entry['type'], entry['size']))

        tree.pack(padx=20, pady=20)
