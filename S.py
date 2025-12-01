import tkinter as tk

def greet():
    name = name_entry.get()
    greeting_label.config(text=f"Hello, {name}!")

root = tk.Tk()
root.title("Greeting App")

tk.Label(root, text="Enter your name:").pack()
name_entry = tk.Entry(root)
name_entry.pack()

tk.Button(root, text="Greet", command=greet).pack()
greeting_label = tk.Label(root, text="")
greeting_label.pack()

root.mainloop()
