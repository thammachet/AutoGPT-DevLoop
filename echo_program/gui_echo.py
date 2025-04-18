import tkinter as tk


def main():
    # Create the main window
    root = tk.Tk()
    root.title("Echo GUI")

    # Input variable
    input_var = tk.StringVar()

    # Entry widget for user input
    entry = tk.Entry(root, textvariable=input_var, width=50)
    entry.pack(padx=10, pady=10)

    # Label to display the echoed text
    echo_label = tk.Label(root, text="", width=50)
    echo_label.pack(padx=10, pady=10)

    # Function to update label text
    def echo_input():
        echo_label.config(text=input_var.get())

    # Button to trigger echo
    button = tk.Button(root, text="Echo", command=echo_input)
    button.pack(padx=10, pady=10)

    # Start the GUI event loop
    root.mainloop()


if __name__ == "__main__":
    main()
