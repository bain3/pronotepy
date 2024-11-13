"""
Application graphique pour afficher les moyennes, les succès, les difficultés et les gains liés aux
résultats scolaires de l'eleve
"""

import tkinter as tk


class ClusterBancoFrame(tk.LabelFrame):
    "Frame dédiée aux BANCOS des poles de disciplines (dans la frame des bancos)"

    def __init__(self, container, cluster, text='Banco', banco_global=None):
        self.container = container
        self.rules = container.rules
        self.report_card = container.report_card
        super().__init__(container, text=text)  # cluster.name())
        self.pack(fill="both", expand="yes")

        self.labels = []
        if banco_global is True or cluster and self.rules.cluster_is_eligible_for_banco(
                cluster):
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


class ClusterMoneyFrame(tk.LabelFrame):
    "Frame dédiée au gains des poles de disciplines (dans la frame des gains)"

    def __init__(self, container, cluster, text='Gains', money_pool=None):
        self.container = container
        self.rules = container.rules
        self.report_card = container.report_card
        super().__init__(container, text=text)  # cluster.name())
        self.pack(fill="both", expand="yes")

        self.labels = []
        if money_pool:
            self.write(f"{money_pool}€", 'dark green')
        else:
            marathon_money = self.rules.get_cluster_marathon_money(cluster)
            if not self.rules.cluster_is_eligible_for_marathon(cluster):
                self.write(f"{marathon_money}€ à gagner", None)
            else:
                self.write(f"{marathon_money}€", 'dark green')

            boost_money = self.rules.get_cluster_boost_money(cluster)
            if not self.rules.cluster_is_eligible_for_boost(cluster):
                if self.rules.cluster_can_boost_money(cluster):
                    self.write(
                        f"{boost_money}€ à BOOSTER",
                        None)  # 'dark slate gray')
            else:
                self.write(f"{boost_money}€ de BOOST !", 'dark green')

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
        self.report_card = container.report_card

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
        # frame 'report_card'
        super().__init__(container, relief=tk.GROOVE, background=bg)
        self.container = container
        self.rules = container.rules
        self.report_card = container.report_card

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


class ClusterAverageFrame(tk.LabelFrame):
    "Frame dédiée aux moyennes des poles de disciplines (dans la frame des moyennes)"

    def __init__(self, container, cluster):
        self.container = container
        self.rules = container.rules
        self.report_card = container.report_card
        # Apply rules on background
        bg = None
        if cluster.average():
            if self.rules.cluster_is_eligible_for_boost(cluster):
                bg = 'Spring Green'
            elif self.rules.get_cluster_marathon_money(cluster):
                bg = 'Light Green'

            text = f"{cluster.name()} : {cluster.average():.2f}/20"
            if cluster.name() == 'Retards':
                text = f"{cluster.name()} : {cluster.average():.0f}"
        else:
            text = cluster.name()
        super().__init__(container, text=text, background=bg)
        self.pack(fill="both", expand="yes")

        # frame 'subjects' et 'grades'
        self.frame_subjects = SubjectsFrame(self, bg)
        self.frame_subject_averages = SubjectAveragesFrame(self, bg)

        for report_card_subject in cluster.subjects():
            self.frame_subjects.write(report_card_subject)

            # Apply rules on foreground
            subject_average = cluster.subject_average(report_card_subject.name())
            average_fg = None
            if subject_average:
                if self.rules.subject_downgrades_eligible_cluster_for_boost(
                        cluster, subject_average):
                    average_fg = 'FireBrick'
                elif self.rules.subject_downgrades_eligible_cluster_for_marathon(cluster, subject_average):
                    average_fg = 'Red'

                text = f"{subject_average:.2f}/20"
                if report_card_subject.name() == 'Retards':
                    text = f"{subject_average:.0f}"
                self.frame_subject_averages.write(text, average_fg)
            else:
                self.frame_subject_averages.write('-', average_fg)


class BancoFrame(tk.Frame):
    "Frames dédiée aux bancos"

    def __init__(self, container, cluster, text='Banco', banco_global=None):
        # frame 'banco par discipline'
        super().__init__(container, relief=tk.GROOVE)
        # self.container = container
        self.rules = container.rules
        self.report_card = container.report_card
        self.cluster_frame = []
        self.cluster_frame.append(ClusterBancoFrame(self, cluster, text, banco_global))


class MoneyFrame(tk.Frame):
    "Frames dédiée aux gains"

    def __init__(self, container, cluster, text='Gains', gain_total=None):
        # frame 'gains'
        super().__init__(container, relief=tk.GROOVE)
        # self.container = container
        self.rules = container.rules
        self.report_card = container.report_card
        self.cluster_frame = []
        self.cluster_frame.append(ClusterMoneyFrame(self, cluster, text, gain_total))


class ReportCardFrame(tk.Frame):
    "Frames dédiée au bulletin"

    def __init__(self, container, cluster):
        # frame 'moyenne'
        super().__init__(container, relief=tk.GROOVE)
        # self.container = container
        self.rules = container.rules
        self.report_card = container.report_card
        self.cluster_frame = []
        self.cluster_frame.append(ClusterAverageFrame(self, cluster))


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
        ratio = value / max_value
        if ratio > 1.:
            ratio = 1.

        fill_width = 10 + (self.width - 20) * ratio
        self.coords(self.barre, 10, 10, fill_width, self.height - 10)

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




class BancoSafe(tk.Canvas):
    "Representation graphique du BANCO"

    def __init__(self, rules, report_card, width, height):
        super().__init__(width=width, height=height)
        self.width = width
        self.height = height

        self.rules = rules
        self.report_card = report_card
        self.rate_banco = self.rules.get_banco_rate(self.report_card)

        self.safe = {}
        self.safe[0]   = tk.PhotoImage(file="example_5\\images\\safe_00%.png")
        self.safe[20]  = tk.PhotoImage(file="example_5\\images\\safe_20%.png")
        self.safe[40]  = tk.PhotoImage(file="example_5\\images\\safe_40%.png")
        self.safe[60]  = tk.PhotoImage(file="example_5\\images\\safe_60%.png")
        self.safe[80]  = tk.PhotoImage(file="example_5\\images\\safe_80%.png")
        self.safe[100] = tk.PhotoImage(file="example_5\\images\\safe_100%.png")

        self.images = []
        self.images.append(self.create_image(
            self.width / 2, self.height / 2, image=self.safe[self.rate_banco]))


class MoneyPoolFull(tk.Toplevel):
    "Representation graphique du BANCO"

    def __init__(self, container):
        super().__init__(container)
        self.container = container
        self.title("Congratulation !")

        # Afficher le coffre ouvert festif si la cagnotte est pleine
        self.opened_safe_party = tk.PhotoImage(file = "example_5\\images\\congratulation.png")
        self.canvas = tk.Canvas(self, width=self.opened_safe_party.width(), height=self.opened_safe_party.height())
        self.canvas.pack()
        self.images = []
        self.images.append(self.canvas.create_image(self.opened_safe_party.width() / 2, self.opened_safe_party.height() / 2, image=self.opened_safe_party))


class Application(tk.Tk):
    "Application graphique"

    def __init__(self, rules, report_card):
        super().__init__()
        self.rules = rules
        self.report_card = report_card

        self.title('The school award')
        self.resizable(False, False)

        current_row = 0
        self.report_card_frame = []
        self.gains = []
        for cluster in self.report_card.clusters():
            report_card_frame = ReportCardFrame(self, cluster)
            gains = MoneyFrame(self, cluster)

            report_card_frame.grid(
                row=current_row,
                column=0,
                padx=5,
                pady=5,
                sticky='n')
            gains.grid(row=current_row, column=1, pady=5, sticky='n')

            # Rendre les frames visibles
            report_card_frame.grid_propagate(False)
            gains.grid_propagate(False)

            self.report_card_frame.append(report_card_frame)
            self.gains.append(gains)
            current_row = current_row + 1

        # Bilan
        self.gain_total = rules.get_report_card_money(self.report_card)
        gains = MoneyFrame(self, None, 'Synthèse', self.gain_total)
        gains.grid(row=current_row, column=1, pady=5, sticky='n')
        gains.grid_propagate(False)
        self.gains.append(gains)

        # Representation graphique du BANCO
        self.banco_safe_width = 250
        self.banco_safe_height = 450
        self.banco_safe = BancoSafe(self.rules, self.report_card, self.banco_safe_width, self.banco_safe_height)
        self.banco_safe.grid(row=0, column=3, rowspan=5, pady=5, sticky='n')

        # Jauge de la cagnote de récompense
        self.rate_target_amount = rules.get_target_amount_rate(self.report_card)
        self.rate_target_amount_canvas = JaugeHorizontale(
            self, self.banco_safe_width, 49)
        self.rate_target_amount_canvas.set_value(self.rate_target_amount)
        self.rate_target_amount_canvas.grid(
            row=current_row, column=3, padx=5, pady=5, sticky='n')
        self.rate_target_amount_canvas.grid_propagate(False)

        # Afficher le coffre ouvert festif si la cagnotte est pleine
        if self.rate_target_amount >= 100:
            self.money_pool = MoneyPoolFull(self)
