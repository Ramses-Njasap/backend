# commands.py
import tkinter as tk
from tkinter import messagebox, Text, Scrollbar, ttk
import subprocess
import sys

class CommandsFrame(tk.Frame):
    def __init__(self, parent, output_text, root):
        super().__init__(parent)
        self.parent = parent
        self.output_text = output_text
        self.root = root
        self.create_widgets()

    def create_widgets(self):
        self.output_text = Text(self, wrap='word', height=20, width=80, bg='#ffffff')
        self.output_text.pack(side='right', pady=10, padx=10, fill='both', expand=True)

        scrollbar = Scrollbar(self, command=self.output_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.output_text['yscrollcommand'] = scrollbar.set

        commands = {
            "Run Makemigrations": "makemigrations",
            "Migrate Data To DB": "migrate",
            "Check For Errors": "check",
            "Create Superuser": "createsuperuser",
            "Runserver": "runserver"
        }

        for command_name, management_command in commands.items():
            btn = ttk.Button(self, text=command_name, command=lambda cmd=management_command: self.run_management_command(cmd))
            btn.pack(pady=10, padx=20, fill='x')

        phone_label = tk.Label(self, text='Phone:')
        phone_label.pack(pady=(20, 0), padx=20, anchor='w')
        self.phone_entry = tk.Entry(self)
        self.phone_entry.pack(pady=(0, 20), padx=20, fill='x')

        password_label = tk.Label(self, text='Password:')
        password_label.pack(pady=(20, 0), padx=20, anchor='w')
        self.password_entry = tk.Entry(self, show='*')
        self.password_entry.pack(pady=(0, 20), padx=20, fill='x')

    def run_management_command(self, command):
        try:
            separator = f"\n{'*' * 20} {command} Output {'*' * 20}\n\n"
            self.output_text.insert('end', separator)
            process = subprocess.Popen(['python', 'manage.py', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_text.insert('end', output.strip() + '\n\n')
                    self.output_text.see('end')
                    self.parent.update_idletasks()

            if process.returncode == 0:
                messagebox.showinfo('Success', f'{command} executed successfully.')
            else:
                messagebox.showerror('Error', f'Error executing {command}.')
        except Exception as e:
            messagebox.showerror('Error', f'An unexpected error occurred:\n\n{e}')
