import tkinter as tk
from tkinter import Text, Scrollbar, Entry, Label, messagebox, ttk
import subprocess
import pexpect

from commands import CommandsFrame
from databases import DatabasesFrame

class AdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title('LaLodge Admin Management')

        # Create a style for ttk widgets (used for buttons)
        style = ttk.Style()
        style.configure("TButton", padding=10, relief="flat")

        # Navigation bar
        nav_frame = tk.Frame(root, bg='#333')
        nav_frame.pack(side='left', fill='y')

        btn_commands = ttk.Button(nav_frame, text='Commands', command=self.show_commands)
        btn_commands.pack(pady=10, padx=20, fill='x', side='top')

        btn_databases = ttk.Button(nav_frame, text='Databases', command=self.show_databases)
        btn_databases.pack(pady=10, padx=20, fill='x', side='top')

        # Create a frame to hold the buttons and entry widgets
        self.frame = tk.Frame(root, bg='#f0f0f0')
        self.frame.pack(side='left', fill='both', expand=True)

        # Output space to the right
        self.output_text = Text(root, wrap='word', height=20, width=80, bg='#ffffff')
        self.output_text.pack(side='right', pady=10, padx=10, fill='both', expand=True)

        scrollbar = Scrollbar(root, command=self.output_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.output_text['yscrollcommand'] = scrollbar.set

        # Create a placeholder frame for Commands and Databases
        self.commands_frame = None
        self.databases_frame = None

    def show_commands(self):
        # Destroy the current frames if they exist
        if self.commands_frame:
            self.commands_frame.destroy()
        if self.databases_frame:
            self.databases_frame.destroy()

        # Create a new CommandsFrame instance
        self.commands_frame = CommandsFrame(self.frame, self.output_text, self.root)
        self.commands_frame.pack(fill='both', expand=True)
    
    def show_createsuperuser_prompt(self):
        # Display prompts for createsuperuser parameters
        prompts = ['Username', 'Email', 'Password', 'Password (again)']
        entries = {}

        for prompt in prompts:
            label = Label(self.root, text=f'{prompt}:', bg='#f0f0f0')
            label.pack(pady=(20, 0), padx=20, anchor='w')

            entry = Entry(self.root)
            entry.pack(pady=(0, 20), padx=20, fill='x')
            entries[prompt] = entry

        # Execute createsuperuser command when the button is clicked
        btn_create_superuser = ttk.Button(self.root, text='Create Superuser', command=lambda: self.execute_createsuperuser(entries))
        btn_create_superuser.pack(pady=10)
    
    def execute_createsuperuser(self, entries):
        try:
            # Run the createsuperuser command with the provided parameters
            process = subprocess.Popen(['python', 'manage.py', 'createsuperuser'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            for prompt, entry in entries.items():
                user_input = entry.get()
                process.stdin.write(f'{user_input}\n')
                process.stdin.flush()

            process.stdin.close()

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_text.insert('end', output.strip() + '\n\n')
                    self.output_text.see('end')
                    self.root.update_idletasks()

            if process.returncode == 0:
                messagebox.showinfo('Success', 'Superuser created successfully.')
            else:
                messagebox.showerror('Error', 'Error executing createsuperuser.')

        except Exception as e:
            messagebox.showerror('Error', f'An unexpected error occurred:\n\n{e}')

    def show_databases(self):
        # Destroy the current frames if they exist
        if self.commands_frame:
            self.commands_frame.destroy()
        if self.databases_frame:
            self.databases_frame.destroy()

        # Create a new DatabasesFrame instance
        self.databases_frame = DatabasesFrame(self.frame)
        self.databases_frame.pack(fill='both', expand=True)

        # Add code to display databases, tables, and data here

    def run_management_command(self, command):
        try:
            separator = f"\n{'*' * 20} {command} Output {'*' * 20}\n\n"
            self.output_text.insert('end', separator)
            # Run the selected management command
            process = subprocess.Popen(['python', 'manage.py', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_text.insert('end', output.strip() + '\n\n')
                    self.output_text.see('end')
                    self.root.update_idletasks()

            if process.returncode == 0:
                messagebox.showinfo('Success', f'{command} executed successfully.')
            else:
                messagebox.showerror('Error', f'Error executing {command}.')
        except Exception as e:
            messagebox.showerror('Error', f'An unexpected error occurred:\n\n{e}')