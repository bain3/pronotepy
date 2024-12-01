"""
Application graphique pour afficher les moyennes, les succès, les difficultés et les gains liés aux
résultats scolaires de l'eleve
"""

import tkinter as tk


class ToolTip:
    """ToolTip pour afficher une description sur passage de la souris.
    (code produit pas copilot)"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.nb_lines = text.count('\n')
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        "Afficher le ToolTip"
        x = event.x_root + 10
        if self.nb_lines > 1:
            y = event.y_root - 15 * int(self.nb_lines / 2)
        else:
            y = event.y_root + 10
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            relief="solid",
            borderwidth=1,
            justify="left",
            anchor="w")
        label.pack()

    def hide_tooltip(self, event): # pylint: disable=unused-argument
        "Cacher le ToolTip"
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None


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
    "Frame dédiée aux gains en cours des poles de disciplines (dans la frame des gains)"

    def __init__(self, container, cluster, text='Gains', money_pool=None):
        self.container = container
        self.rules = container.rules
        self.report_card = container.report_card
        super().__init__(container, text=text)  # cluster.name())
        self.pack(fill="both", expand="yes")

        self.labels = []
        if money_pool is not None:
            self.write(f"{money_pool}€", 'Forest Green')
        else:
            marathon_money = self.rules.get_cluster_marathon_money(cluster)
            if not self.rules.cluster_is_eligible_for_marathon(cluster):
                self.write(f"{marathon_money}€ à gagner", None)
            else:
                self.write(f"{marathon_money}€", 'Forest Green')

            boost_money = self.rules.get_cluster_boost_money(cluster)
            if not self.rules.cluster_is_eligible_for_boost(cluster):
                if self.rules.cluster_can_boost_money(cluster):
                    self.write(
                        f"{boost_money}€ à BOOSTER",
                        None)  # 'dark slate gray')
            else:
                self.write(f"{boost_money}€ de BOOST !", 'Forest Green')

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

class ShortClusterMoneyFrame(tk.LabelFrame):
    "Frame étroite dédiée aux gains des poles de disciplines passés (dans la frame des gains)"

    def __init__(self, container, cluster, text='Gains', money_pool=None):
        self.container = container
        self.rules = container.rules
        self.report_card = container.report_card
        super().__init__(container, text=text)  # cluster.name())
        self.pack(fill="both", expand="yes")

        self.labels = []
        if money_pool is not None:
            self.write(f"{money_pool}€", 'Forest Green')
        else:
            marathon_money = self.rules.get_cluster_marathon_money(cluster)
            if not self.rules.cluster_is_eligible_for_marathon(cluster):
                self.write("0€", 'Red')
            else:
                self.write(f"{marathon_money}€", 'Forest Green')

            boost_money = self.rules.get_cluster_boost_money(cluster)
            if not self.rules.cluster_is_eligible_for_boost(cluster):
                if self.rules.cluster_can_boost_money(cluster):
                    self.write(
                        "0€",
                        'Red')  # 'dark slate gray')
            else:
                self.write(f"{boost_money}€", 'Forest Green')

    def write(self, text, fg):
        "Ecriture de la moyenne de discipline"
        self.labels.append(
            tk.Label(
                self,
                text=text,
                anchor='w',
                foreground=fg,
                width=3).pack(
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
        if cluster.average() is not None:
            if self.rules.cluster_is_eligible_for_boost(cluster):
                bg = 'Spring Green'
            elif self.rules.cluster_is_eligible_for_marathon(cluster):
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
            subject_average = cluster.subject_average(
                report_card_subject.name())
            average_fg = None
            if subject_average is not None:
                if self.rules.subject_downgrades_eligible_cluster_for_boost(
                        cluster, subject_average):
                    average_fg = 'FireBrick'
                elif self.rules.subject_downgrades_eligible_cluster_for_marathon(
                        cluster, subject_average):
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
        self.cluster_frame.append(
            ClusterBancoFrame(
                self, cluster, text, banco_global))


class MoneyFrame(tk.Frame):
    "Frames dédiées aux gains en cours"

    def __init__(self, container, report_card, cluster, text=None, gain_total=None):
        # frame 'gains'
        super().__init__(container, relief=tk.GROOVE)
        # self.container = container
        self.rules = container.rules
        self.report_card = report_card
        if not text:
            text = report_card.infos.period_name()
        self.cluster_frame = []
        self.cluster_frame.append(
            ClusterMoneyFrame(
                self, cluster, text, gain_total))

class ShortMoneyFrame(tk.Frame):
    "Frames étroites dédiées aux gains passés"

    def __init__(self, container, report_card, cluster, text=None, gain_total=None):
        # frame 'gains'
        super().__init__(container, relief=tk.GROOVE)
        # self.container = container
        self.rules = container.rules
        self.report_card = report_card
        if not text:
            text = report_card.infos.short_period_name()
        self.cluster_frame = []
        self.cluster_frame.append(
            ShortClusterMoneyFrame(
                self, cluster, text, gain_total))


class ReportCardFrame(tk.Frame):
    "Frames dédiée au bulletin"

    def __init__(self, container, report_card, cluster):
        # frame 'moyenne'
        super().__init__(container, relief=tk.GROOVE)
        # self.container = container
        self.rules = container.rules
        self.report_card = report_card
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
        ratio = min(ratio, 1.0)

        fill_width = 10 + (self.width - 20) * ratio
        # Gérer l'affichage des petites valeurs et du passage sur deux chiffres
        if ratio * 100 < 10.:
            fill_width = max(fill_width, 45)
        else:
            fill_width = max(fill_width, 55)
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
        self.safe[0]   = tk.PhotoImage(file="the_school_award\\images\\safe_00%.png")
        self.safe[20]  = tk.PhotoImage(file="the_school_award\\images\\safe_20%.png")
        self.safe[40]  = tk.PhotoImage(file="the_school_award\\images\\safe_40%.png")
        self.safe[60]  = tk.PhotoImage(file="the_school_award\\images\\safe_60%.png")
        self.safe[80]  = tk.PhotoImage(file="the_school_award\\images\\safe_80%.png")
        self.safe[100] = tk.PhotoImage(file="the_school_award\\images\\safe_100%.png")

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
        self.opened_safe_party = tk.PhotoImage(
            file="the_school_award\\images\\congratulation.png")
        self.canvas = tk.Canvas(self,
                                width=self.opened_safe_party.width(),
                                height=self.opened_safe_party.height())
        self.canvas.pack()
        self.images = []
        self.images.append(
            self.canvas.create_image(
                self.opened_safe_party.width() / 2,
                self.opened_safe_party.height() / 2,
                image=self.opened_safe_party))


class Application(tk.Tk):
    "Application graphique"

    def __init__(self, rules, report_cards):
        super().__init__()
        self.rules = rules
        self.report_cards = report_cards
        self.nb_report_cards = len(report_cards)

        self.title('The school award')
        self.resizable(False, False)

        current_column = 1
        self.report_card_frame = []
        self.gains = []
        current_report_card_done = False
        for report_card in self.report_cards[-1::-1]: # Current report card to first one
            current_row = 0
            for cluster in report_card.clusters():
                if not current_report_card_done:
                    report_card_frame = ReportCardFrame(self, report_card, cluster)

                    report_card_frame.grid(
                        row=current_row,
                        column=0,
                        padx=5,
                        pady=5,
                        sticky='n')
                    # Rendre les frames visibles
                    report_card_frame.grid_propagate(False)

                if not current_report_card_done:
                    gains = MoneyFrame(self, report_card, cluster)
                else:
                    gains = ShortMoneyFrame(self, report_card, cluster)
                gains.grid(row=current_row, column=current_column, pady=5, sticky='n')
                # Rendre les frames visibles
                gains.grid_propagate(False)

                self.report_card_frame.append(report_card_frame)
                self.gains.append(gains)
                current_row += 1
            current_column += 1
            current_report_card_done = True

        # Bilan
        self.gain_total = 0
        for report_card in self.report_cards:
            self.gain_total += rules.get_report_card_money(report_card)
        gains = MoneyFrame(self, None, None, text='Synthèse', gain_total=self.gain_total)
        gains.grid(row=current_row, column=1, pady=5, sticky='n', columnspan=self.nb_report_cards)
        gains.grid_propagate(False)
        self.gains.append(gains)

        # Representation graphique du BANCO
        self.banco_safe_width = 250
        self.banco_safe_height = 450
        self.banco_safe = BancoSafe(
            self.rules,
            self.report_cards[-1], # Current report card
            self.banco_safe_width,
            self.banco_safe_height)
        self.banco_safe.grid(row=0, column=current_column, rowspan=5, pady=5, sticky='n')
        self.banco_tooltip = ToolTip(
            self.banco_safe,
            self.rules.get_banco_description())

        # Jauge de la cagnote de récompense
        self.rate_target_amount = rules.get_target_amount_rate(
            money_pool=self.gain_total)
        self.rate_target_amount_canvas = JaugeHorizontale(
            self, self.banco_safe_width, 49)
        self.rate_target_amount_canvas.set_value(self.rate_target_amount)
        self.rate_target_amount_canvas.grid(
            row=current_row, column=current_column, padx=5, pady=5, sticky='n')
        self.rate_target_amount_canvas.grid_propagate(False)
        self.rate_target_amount_tooltip = ToolTip(
            self.rate_target_amount_canvas,
            self.rules.get_marathon_description() +
            '\n\n' +
            self.rules.get_boost_description())

        # Afficher le coffre ouvert festif si la cagnotte est pleine
        if self.rate_target_amount >= 100:
            self.money_pool = MoneyPoolFull(self)
