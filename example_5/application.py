"""
Application graphique pour afficher les moyennes, les succès, les difficultés et les gains liés aux
résultats scolaires de l'eleve
"""

import tkinter as tk


class PoleBancoFrame(tk.LabelFrame):
    "Frame dédiée aux BANCOS des poles de disciplines (dans la frame des bancos)"

    def __init__(self, container, pole, text='Banco', banco_total=None):
        self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin
        super().__init__(container, text=text)  # pole.name())
        self.pack(fill="both", expand="yes")

        self.labels = []
        if banco_total is False or not self.rules.pole_is_bancoed(pole):
            self.write("no BANCO", None)
        else:
            self.write("BANCO !", 'dark green')

    def write(self, text, fg):
        "Ecriture de la moyenne de discipline"
        self.labels.append(
            tk.Label(
                self,
                text=text,
                anchor='w',
                foreground=fg,
                width=9).pack(
                fill='x'))


class PoleGainFrame(tk.LabelFrame):
    "Frame dédiée au gains des poles de disciplines (dans la frame des gains)"

    def __init__(self, container, pole, text='Gains', gain_total=None):
        self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin
        super().__init__(container, text=text)  # pole.name())
        self.pack(fill="both", expand="yes")

        self.labels = []
        if gain_total:
            self.write(f"{gain_total}€", 'dark green')
        else:
            marathon = self.rules.get_pole_marathon_gain(pole)
            if not self.rules.pole_is_marathoned(pole):
                self.write(f"{marathon}€ à gagner", None)
            else:
                self.write(f"{marathon}€", 'dark green')

            boost = self.rules.get_pole_boost_gain(pole)
            if not self.rules.pole_is_boosted(pole):
                if self.rules.pole_has_boost(pole):
                    self.write(
                        f"{boost}€ à BOOSTER",
                        None)  # 'dark slate gray')
            else:
                self.write(f"{boost}€ de BOOST !", 'dark green')

    def write(self, text, fg):
        "Ecriture de la moyenne de discipline"
        self.labels.append(
            tk.Label(
                self,
                text=text,
                anchor='w',
                foreground=fg,
                width=12).pack(
                fill='x'))


class SubjectAveragesFrame(tk.Frame):
    "Frame dédiée aux moyennes de disciplines (dans la frame des poles)"

    def __init__(self, container, bg):
        # frame 'moyenne par discipline'
        super().__init__(container, relief=tk.GROOVE, background=bg)
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
                anchor='w',
                foreground=fg,
                width=7).pack(
                fill='x'))


class SubjectsFrame(tk.Frame):
    "Frame dédiée aux disciplines (dans la frame des poles)"

    def __init__(self, container, bg):
        # frame 'bulletin'
        super().__init__(container, relief=tk.GROOVE, background=bg)
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
                anchor='e',
                width=25).pack(
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

            text = f"{pole.name()} : {pole.average():.2f}/20"
            if pole.name() == 'Retards':
                text = f"{pole.name()} : {pole.average():.0f}"
        else:
            text = pole.name()
        super().__init__(container, text=text, background=bg)
        self.pack(fill="both", expand="yes")

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

                text = f"{subject_average:.2f}/20"
                if bulletin_subject.name() == 'Retards':
                    text = f"{subject_average:.0f}"
                self.frame_subject_averages.write(text, average_fg)
            else:
                self.frame_subject_averages.write('-', average_fg)


class BancoFrame(tk.Frame):
    "Frames dédiée aux bancos"

    def __init__(self, container, pole, text='Banco', banco_total=None):
        # frame 'banco par discipline'
        super().__init__(container, relief=tk.GROOVE)
        # self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin
        self.pole_frame = []
        self.pole_frame.append(PoleBancoFrame(self, pole, text, banco_total))


class GainsFrame(tk.Frame):
    "Frames dédiée aux gains"

    def __init__(self, container, pole, text='Gains', gain_total=None):
        # frame 'gains'
        super().__init__(container, relief=tk.GROOVE)
        # self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin
        self.pole_frame = []
        self.pole_frame.append(PoleGainFrame(self, pole, text, gain_total))


class BulletinFrame(tk.Frame):
    "Frames dédiée au bulletin"

    def __init__(self, container, pole):
        # frame 'moyenne'
        super().__init__(container, relief=tk.GROOVE)
        # self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin
        self.pole_frame = []
        self.pole_frame.append(PoleAverageFrame(self, pole))


class Application(tk.Tk):
    "Application graphique"

    def __init__(self, rules, bulletin):
        super().__init__()
        self.rules = rules
        self.bulletin = bulletin

        self.title('PS5 ?')
        self.resizable(False, False)

        current_row = 0
        self.bulletin_frame = []
        self.gains = []
        self.banco = []
        self.gain_total = 0
        self.banco_total = rules.bulletin_is_banco(bulletin)
        for pole in self.bulletin.poles():
            bulletin_frame = BulletinFrame(self, pole)
            gains = GainsFrame(self, pole)
            banco = BancoFrame(self, pole)

            bulletin_frame.grid(
                row=current_row,
                column=0,
                padx=5,
                pady=5,
                sticky='n')
            gains.grid(row=current_row, column=1, pady=5, sticky='n')
            banco.grid(row=current_row, column=2, padx=5, pady=5, sticky='n')

            # Rendre les frames visibles
            bulletin_frame.grid_propagate(False)
            gains.grid_propagate(False)
            banco.grid_propagate(False)

            self.bulletin_frame.append(bulletin_frame)
            self.gains.append(gains)
            self.banco.append(banco)
            current_row = current_row + 1

            # Gain total
            gain = rules.get_pole_gain(pole)
            if gain:
                self.gain_total = self.gain_total + gain

        # Bilan
        gains = GainsFrame(self, None, 'Synthèse', self.gain_total)
        banco = BancoFrame(self, None, 'Synthèse', self.banco_total)

        gains.grid(row=current_row, column=1, pady=5, sticky='n')
        banco.grid(row=current_row, column=2, padx=5, pady=5, sticky='n')

        gains.grid_propagate(False)
        banco.grid_propagate(False)

        self.gains.append(gains)
        self.banco.append(banco)
