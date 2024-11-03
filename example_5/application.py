"""
Application graphique pour afficher les moyennes, les succès, les difficultés et les gains liés aux
résultats scolaires de l'eleve
"""

import tkinter as tk


class SubjectAveragesFrame(tk.Frame):
    "Frame dédiée aux moyennes de disciplines (dans la frame des poles)"

    def __init__(self, container, bg):
        # frame 'bulletin'
        super().__init__(container, relief=tk.GROOVE, background=bg, padx=5)
        self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin

        self.pack(side=tk.RIGHT)
        self.bg = bg
        self.labels = []

    def write(self, text, fg):
        "Ecriture de la moyenne de discipline"
        self.labels.append(
            tk.Label(
                self,
                text=text,
                background=self.bg,
                anchor='e',
                foreground=fg).pack(
                fill='x'))


class SubjectsFrame(tk.Frame):
    "Frame dédiée aux disciplines (dans la frame des poles)"

    def __init__(self, container, bg):
        # frame 'bulletin'
        super().__init__(container, relief=tk.GROOVE, background=bg, padx=5)
        self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin

        self.pack(side=tk.LEFT)
        self.bg = bg
        self.labels = []

    def write(self, text):
        "Ecriture de la discipline"
        self.labels.append(
            tk.Label(
                self,
                text=text,
                background=self.bg,
                anchor='w').pack(
                fill='x'))


class PoleGainFrame(tk.LabelFrame):
    "Frame dédiée au gains des poles de disciplines (dans la frame des gains)"

    def __init__(self, container, pole):
        self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin
        # Apply rules on background
        self.bg = None
        # if pole.average():
        #     if self.rules.pole_is_boosted(pole):
        #         self.bg = 'Spring Green'
        #     elif self.rules.get_pole_marathon_gain(pole):
        #         self.bg = 'Light Green'

        super().__init__(container, text=pole.name(), background=self.bg)
        self.pack(fill="both", expand="yes", padx=5, pady=5)

        self.labels = []
        if not self.rules.pole_is_boosted(pole):
            gain = self.rules.get_pole_marathon_gain(pole)
            if gain:
                self.write(f"{gain}€", 'dark green')
            if self.rules.pole_has_boost(pole):
                boost = self.rules.get_pole_boost_gain(pole)
                self.write(f"{boost}€ à BOOSTER !", 'dark slate gray')
        else:
            gain = self.rules.get_pole_marathon_gain(pole)
            self.write(f"{gain}€", 'dark slate gray')
            boost = self.rules.get_pole_boost_gain(pole)
            self.write(f"{boost}€ BOOST !", 'dark green')

    def write(self, text, fg):
        "Ecriture de la moyenne de discipline"
        self.labels.append(
            tk.Label(
                self,
                text=text,
                background=self.bg,
                anchor='w',
                foreground=fg).pack(
                fill='x'))

class PoleAverageFrame(tk.LabelFrame):
    "Frame dédiée aux moyennes des poles de disciplines (dans la frame des moyennes)"

    def __init__(self, container, pole):
        self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin
        # Apply rules on background
        bg = None
        if pole.average():
            if self.rules.pole_is_boosted(pole):
                bg = 'Spring Green'
            elif self.rules.get_pole_marathon_gain(pole):
                bg = 'Light Green'

        if pole.average():
            text = f"{pole.name()} : {pole.average():.2f}/20"
        else:
            text = pole.name()
        super().__init__(container, text=text, background=bg)
        self.pack(fill="both", expand="yes", padx=5, pady=5)

        # frame 'subjects' et 'grades'
        self.frame_subjects = SubjectsFrame(self, bg)
        self.frame_subject_averages = SubjectAveragesFrame(self, bg)

        for bulletin_subject in pole.subjects():
            self.frame_subjects.write(bulletin_subject)

            # Apply rules on foreground
            subject_average = pole.subject_average(bulletin_subject.name())
            average_fg = None
            if subject_average:
                if self.rules.subject_downgrade_boosted_pole(
                        pole, subject_average):
                    average_fg = 'FireBrick'
                elif self.rules.subject_downgrade_marathon_pole(pole, subject_average):
                    average_fg = 'Red'

            if subject_average:
                self.frame_subject_averages.write(
                    f"{subject_average:.2f}/20", average_fg)
            else:
                self.frame_subject_averages.write('-', average_fg)


class GainsFrame(tk.Frame):
    "Frames dédiée aux gains"

    def __init__(self, container):
        # frame 'bulletin'
        super().__init__(container, relief=tk.GROOVE)
        # self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin
        self.pole_frame = []
        for pole in self.bulletin.poles():
            self.pole_frame.append(PoleGainFrame(self, pole))


class AveragesFrame(tk.Frame):
    "Frames dédiée aux moyennes"

    def __init__(self, container):
        # frame 'bulletin'
        super().__init__(container, relief=tk.GROOVE)
        # self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin
        self.pole_frame = []
        for pole in self.bulletin.poles():
            self.pole_frame.append(PoleAverageFrame(self, pole))


class DelaysFrames(tk.Frame):
    "Frame dédiée aux retards"

    def __init__(self, container):
        # frame 'retards'
        super().__init__(container, relief=tk.GROOVE)
        self.container = container

        if self.container.bulletin.delays() is not None:
            # Apply rules on background
            bg = None
            if self.container.rules.pole_is_boosted(
                    self.container.bulletin.delays()):
                bg = 'Spring Green'
            elif self.container.rules.get_pole_marathon_gain(self.container.bulletin.delays()):
                bg = 'Light Green'
            tk.Label(
                self,
                text=self.container.bulletin.delays(),
                background=bg,
                anchor='w').pack(
                fill='x')

class DelaysGainsFrames(tk.Frame):
    "Frame dédiée aux gains des retards"

    def __init__(self, container):
        # frame 'gains des retards'
        super().__init__(container, relief=tk.GROOVE)
        self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin
        self.retards = self.bulletin.delays()

        if self.retards is not None:
            # Apply rules on background
            self.bg = None
            # if self.container.rules.pole_is_boosted(
            #         self.container.bulletin.delays()):
            #     bg = 'Spring Green'
            # elif self.container.rules.get_pole_marathon_gain(self.container.bulletin.delays()):
            #     bg = 'Light Green'
            tk.Label(
                self,
                text=self.retards,
                background=self.bg,
                anchor='w').pack(
                fill='x')
            
        self.labels = []

        marathon = self.rules.get_pole_marathon_gain(self.retards)
        if not self.rules.pole_is_marathoned(self.retards):
            fg = 'dark slate gray'
        else:
            fg = 'dark green'
        self.write(f"{marathon}€", fg)
        
        boost = self.rules.get_pole_boost_gain(self.retards)
        if not self.rules.pole_is_boosted(self.retards):
            if self.rules.pole_has_boost(self.retards):
                self.write(f"{boost}€ à BOOSTER !", 'dark slate gray')
        else:
            self.write(f"{boost}€ BOOST !", 'dark green')

    def write(self, text, fg):
        "Ecriture de la moyenne de retards"
        self.labels.append(
            tk.Label(
                self,
                text=text,
                background=self.bg,
                anchor='w',
                foreground=fg).pack(
                fill='x'))


class Application(tk.Tk):
    "Application graphique"

    def __init__(self, rules, bulletin):
        super().__init__()
        self.rules = rules
        self.bulletin = bulletin

        self.title('PS5 ?')
        self.resizable(False, False)

        self.averages = AveragesFrame(self)
        self.gains = GainsFrame(self)
        self.delays = DelaysFrames(self)
        self.delays_gains = DelaysGainsFrames(self)

        self.averages.grid(row=0, column=0, padx=10, pady=10)
        self.gains.grid(row=0, column=1, padx=10, pady=10)
        self.delays.grid(row=1, column=0, padx=10, pady=10)
        self.delays_gains.grid(row=1, column=1, padx=10, pady=10)

        # Rendre les frames visibles
        self.averages.grid_propagate(False)
        self.delays.grid_propagate(False)
        self.gains.grid_propagate(False)
        self.delays_gains.grid_propagate(False)