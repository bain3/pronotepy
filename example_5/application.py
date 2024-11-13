"""
Application graphique pour afficher les moyennes, les succès, les difficultés et les gains liés aux
résultats scolaires de l'eleve
"""

import tkinter as tk


class PoleBancoFrame(tk.LabelFrame):
    "Frame dédiée aux BANCOS des poles de disciplines (dans la frame des bancos)"

    def __init__(self, container, pole, text='Banco', banco_global=None):
        self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin
        super().__init__(container, text=text)  # pole.name())
        self.pack(fill="both", expand="yes")

        self.labels = []
        if banco_global is True or pole and self.rules.cluster_is_bancoed(
                pole):
            self.write("BANCO !", 'dark green')
        else:
            self.write("no BANCO", None)

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
            marathon = self.rules.get_cluster_marathon_money(pole)
            if not self.rules.cluster_is_marathoned(pole):
                self.write(f"{marathon}€ à gagner", None)
            else:
                self.write(f"{marathon}€", 'dark green')

            boost = self.rules.get_cluster_boost_money(pole)
            if not self.rules.cluster_is_boosted(pole):
                if self.rules.cluster_has_boost(pole):
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
            if self.rules.cluster_is_boosted(pole):
                bg = 'Spring Green'
            elif self.rules.get_cluster_marathon_money(pole):
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
                if self.rules.subject_downgrades_boosted_cluster(
                        pole, subject_average):
                    average_fg = 'FireBrick'
                elif self.rules.subject_downgrades_marathon_cluster(pole, subject_average):
                    average_fg = 'Red'

                text = f"{subject_average:.2f}/20"
                if bulletin_subject.name() == 'Retards':
                    text = f"{subject_average:.0f}"
                self.frame_subject_averages.write(text, average_fg)
            else:
                self.frame_subject_averages.write('-', average_fg)


class BancoFrame(tk.Frame):
    "Frames dédiée aux bancos"

    def __init__(self, container, pole, text='Banco', banco_global=None):
        # frame 'banco par discipline'
        super().__init__(container, relief=tk.GROOVE)
        # self.container = container
        self.rules = container.rules
        self.bulletin = container.bulletin
        self.pole_frame = []
        self.pole_frame.append(PoleBancoFrame(self, pole, text, banco_global))


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


class JaugeHorizontale(tk.Canvas):
    """Code généré par 'Copilot' pour réaliser une jauge horizontale"""

    def __init__(self, parent, width=400, height=50):
        super().__init__(parent, width=width, height=height)
        # self.pack()
        self.width = width
        self.height = height
        self.create_rectangle(10, 10, width - 10, height - 10, outline='black')
        self.barre = self.create_rectangle(
            10, 10, 10, height - 10, fill='green')

        # Création du label avec une couleur de fond correspondant à celle du
        # canevas
        self.label = tk.Label(
            self, text="", font=(
                'Arial', 12, 'bold'), bg=self['bg'])
        # Initialement placé sur la gauche
        self.label.place(x=10, y=height // 2, anchor='e')

    def set_value(self, value, max_value=100):
        "Positionner le niveau de la jauge"
        fill_width = 10 + (self.width - 20) * (value / max_value)
        self.coords(self.barre, 10, 10, fill_width, self.height - 10)

        ratio = value / max_value
        if ratio <= 0.5:
            red = 255
            green = int(2 * ratio * 255)
        else:
            green = 255
            red = int((1 - 2 * (ratio - 0.5)) * 255)
        color = f'#{red:02x}{green:02x}00'

        self.itemconfig(self.barre, fill=color)

        # Mettre à jour le texte du label et sa position
        self.label.config(text=f"{int(value / max_value * 100)}%", bg=color)
        self.label.place(x=fill_width, y=self.height // 2, anchor='e')


class Application(tk.Tk):
    "Application graphique"

    def __init__(self, rules, bulletin):
        super().__init__()
        self.rules = rules
        self.bulletin = bulletin

        self.title('The school award')
        self.resizable(False, False)

        current_row = 0
        self.bulletin_frame = []
        self.gains = []
        # Représentation textuelle de BANCO obsolète avec le CANVAS
        # self.banco = []
        self.gain_total = 0
        # Représentation textuelle de BANCO obsolète avec le CANVAS
        # self.banco_global = rules.report_card_is_banco(self.bulletin)
        for pole in self.bulletin.poles():
            bulletin_frame = BulletinFrame(self, pole)
            gains = GainsFrame(self, pole)
            # Représentation textuelle de BANCO obsolète avec le CANVAS
            # banco = BancoFrame(self, pole)

            bulletin_frame.grid(
                row=current_row,
                column=0,
                padx=5,
                pady=5,
                sticky='n')
            gains.grid(row=current_row, column=1, pady=5, sticky='n')
            # Représentation textuelle de BANCO obsolète avec le CANVAS
            # banco.grid(row=current_row, column=2, padx=5, pady=5, sticky='n')

            # Rendre les frames visibles
            bulletin_frame.grid_propagate(False)
            gains.grid_propagate(False)
            # Représentation textuelle de BANCO obsolète avec le CANVAS
            # banco.grid_propagate(False)

            self.bulletin_frame.append(bulletin_frame)
            self.gains.append(gains)
            # Représentation textuelle de BANCO obsolète avec le CANVAS
            # self.banco.append(banco)
            current_row = current_row + 1

        # Bilan
        self.gain_total = rules.get_report_card_money(self.bulletin)
        gains = GainsFrame(self, None, 'Synthèse', self.gain_total)
        # Représentation textuelle de BANCO obsolète avec le CANVAS
        # banco = BancoFrame(self, None, 'Synthèse', self.banco_global)

        gains.grid(row=current_row, column=1, pady=5, sticky='n')
        # Représentation textuelle de BANCO obsolète avec le CANVAS
        # banco.grid(row=current_row, column=2, padx=5, pady=5, sticky='n')

        gains.grid_propagate(False)
        # Représentation textuelle de BANCO obsolète avec le CANVAS
        # banco.grid_propagate(False)

        self.gains.append(gains)
        # Représentation textuelle de BANCO obsolète avec le CANVAS
        # self.banco.append(banco)

        # Representation graphique du BANCO
        # TODO : Déplacer ce code dans sa propre 'class'
        self.canvas_width = 250
        self.canvas_height = 450
        self.canvas = tk.Canvas(
            self,
            width=self.canvas_width,
            height=self.canvas_height)
        self.canvas.grid(row=0, column=3, rowspan=5, pady=5, sticky='n')

        # self.opened_safe_party_small = tk.PhotoImage(
        #       file = "example_5\\images\\opened_safe_party_small.png"
        #                                               ) #charger l'image depuis un fichier
        # self.opened_safe_party = tk.PhotoImage(file = "example_5\\images\\opened_safe_party.png")
        self.safe = {}
        self.safe[0] = tk.PhotoImage(file="example_5\\images\\safe_00%.png")
        self.safe[20] = tk.PhotoImage(file="example_5\\images\\safe_20%.png")
        self.safe[40] = tk.PhotoImage(file="example_5\\images\\safe_40%.png")
        self.safe[60] = tk.PhotoImage(file="example_5\\images\\safe_60%.png")
        self.safe[80] = tk.PhotoImage(file="example_5\\images\\safe_80%.png")
        self.safe[100] = tk.PhotoImage(file="example_5\\images\\safe_100%.png")

        self.images = []
        self.rate_banco = self.rules.get_banco_rate(self.bulletin)
        self.images.append(self.canvas.create_image(
            self.canvas_width / 2, self.canvas_height / 2, image=self.safe[self.rate_banco]))

        # Jauge de la cagnote de récompense
        self.rate_target_amount = rules.get_target_amount_rate(self.bulletin)
        self.rate_target_amount_canvas = JaugeHorizontale(
            self, self.canvas_width, 49)
        self.rate_target_amount_canvas.set_value(self.rate_target_amount)
        self.rate_target_amount_canvas.grid(
            row=current_row, column=3, padx=5, pady=5, sticky='n')
        self.rate_target_amount_canvas.grid_propagate(False)
