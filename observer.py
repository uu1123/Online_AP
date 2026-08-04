import tkinter as tk

# --------------------------------
# Observer Pattern Implementation
# --------------------------------

class Subject:
    def __init__(self):
        self._observers = []  # List of observer objects

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self, event_type, data=None):
        for observer in self._observers:
            observer.update(event_type, data)


class Observer:
    def update(self, event_type, data):
        raise NotImplementedError("Subclasses must implement this method.")


# --------------------------------
# Concrete Observers
# --------------------------------

class LabelObserver(Observer):
    """Updates a label when notified."""

    def __init__(self, label):
        self.label = label

    def update(self, event_type, data):
        if event_type == "text_changed":
            self.label.config(text=f"Text changed: {data}")

        elif event_type == "button_clicked":
            self.label.config(text="Button was clicked!")


class LoggerObserver(Observer):
    """Prints messages to the console."""

    def update(self, event_type, data):
        if event_type == "text_changed":
            print(f"[LOG] Text changed to: {data}")

        elif event_type == "button_clicked":
            print("[LOG] Button was clicked!")


# --------------------------------
# Tkinter GUI (Subject)
# --------------------------------

class GUIApp(tk.Tk, Subject):
    def __init__(self):
        tk.Tk.__init__(self)
        Subject.__init__(self)

        self.title("Observer Pattern GUI Example")
        self.geometry("400x250")
        self.config(padx=20, pady=20)

        # Label
        self.label = tk.Label(
            self,
            text="Type something or click the button",
            font=("Arial", 12)
        )
        self.label.pack(pady=10)

        # Text Entry
        self.entry = tk.Entry(self, width=30)
        self.entry.pack(pady=5)
        self.entry.bind("<KeyRelease>", self.on_text_change)

        # Button
        self.button = tk.Button(
            self,
            text="Click Me!",
            command=self.on_button_click
        )
        self.button.pack(pady=10)

        # Observers
        self.label_observer = LabelObserver(self.label)
        self.logger_observer = LoggerObserver()

        # Attach observers
        self.attach(self.label_observer)
        self.attach(self.logger_observer)

    def on_text_change(self, event):
        text = self.entry.get()
        self.notify("text_changed", text)

    def on_button_click(self):
        self.notify("button_clicked")


# --------------------------------
# Run the Application
# --------------------------------

if __name__ == "__main__":
    app = GUIApp()
    app.mainloop()