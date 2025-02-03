import os
import random
import csv
import numpy as np

class GameGenerator:
    def __init__(self, settings, start_end_json):
        self.n = settings['n']
        self.seed = settings['Seed']
        self.rng = np.random.default_rng(self.seed)
        self.TimeLagActivated = settings['TimeLagActivated']
        self.TimeLagMin = settings['TimeLagMin']
        self.TimeLagMax = settings['TimeLagMax']
        self.ReportTimePenaltyActivated = settings['ReportTimePenaltyActivated']
        self.ReportTimePenalty = settings['ReportTimePenalty']
        self.IsAIControlled = settings['IsAIControlled']
        self.PartipicationAmount = settings['ParticipationAmount']
        self.settings = settings

        # Generating boolean arrays with unique values
        self.ArrIsNextNode = self.generate_bool_array('ProbOfNextNode')
        self.ArrIsCorrectNextRoadblock = self.generate_bool_array(
            'ProbCorrectReportIfRoadblock')
        self.ArrIsCorrectAdjRoadblock = self.generate_bool_array(
            'ProbCorrectReportIfRoadblock')
        self.ArrIsWrongNextNoRoadblock = self.generate_bool_array(
            'ProbWrongReportIfNoRoadblock')
        self.ArrIsWrongAdjNoRoadblock = self.generate_bool_array(
            'ProbWrongReportIfNoRoadblock')
        
        self.ArrIsCorrectRandomReport = self.generate_bool_array(
            'ProbCorrectRandomReport')
        
        self.ArrPlayerFollowsNavigation = self.generate_bool_array(
            "ProbPlayerFollowsNavigation")
        self.ArrPlayerReportsCorrectRoadblock = self.generate_bool_array(
            'ProbPlayerReportsCorrectRoadblock')
        self.ArrPlayerReportsRoadblock = self.generate_bool_array(
            'ProbPlayerReportsRoadblock')
                
        if settings['TimeLagActivated']:
            self.ArrTimeLagValues = self.generate_timelag_values(settings['TimeLagMin'], settings['TimeLagMax'])
        else:
            self.ArrTimeLagValues = [0] * self.n

        self.start_end_json = start_end_json
        self.players_speeds = self.generate_players_speeds(len(start_end_json["start_end_indices"]))

        self.random_time_sequences = self.generate_poisson_times(self.PartipicationAmount)

    def generate_timelag_values(self, min, max):
        return self.rng.uniform(min, max, size=self.n).tolist()

    def generate_bool_array(self, setting_name) -> list:
        """ Generates a deterministic array of size n bool values based on a given probabibility within self.settings."""
        bool_array = self.rng.random(self.n) < self.settings[setting_name]
        return bool_array.tolist()  # Convert to list
    
    def generate_poisson_times(self, partipicationAmt) -> list:
        lmbda = partipicationAmt
        times = self.rng.exponential(scale=1/lmbda, size=self.n)
        return np.cumsum(times)
    
    def generate_players_speeds(self, num_players):
        min_speed = self.settings['PlayerSpeed']['min']
        max_speed = self.settings['PlayerSpeed']['max']
        speeds = [self.rng.uniform(int(min_speed), int(max_speed)) for _ in range(num_players)]
        return speeds

    def SaveSetupCsv(self, time: str):
        directory = os.path.join('logs', time)
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, 'Setup.csv')
        with open(file_path, mode='w', newline='') as file:
            w = csv.writer(file)

            w.writerow(['IsAICo  ntrolled',
                        '[1] Prob. Of Next Node',
                        '[2] Prob. Correct Report if Roadblock',
                        '[3] Prob. Wrong Report if no Roadblock',
                        '[4] Participation Amount',
                        '[5] Min. Report Distance',
                        '[5] Max. Report Distance',
                        '[6] Prob. Correct Random Report]',])
            w.writerow([self.settings['IsAIControlled'],
                        self.settings['ProbOfNextNode'],
                        self.settings['ProbCorrectReportIfRoadblock'],
                        self.settings['ProbWrongReportIfNoRoadblock'],
                        self.settings['ParticipationAmount'],
                        self.settings['MinReportDistance'],
                        self.settings['MaxReportDistance'],
                        self.settings['ProbCorrectRandomReport']])
            w.writerow([])
            w.writerow(['Seed',
                        'RNG Event Length',
                        'Time Lag Activated',
                        'Time Lag Min.',
                        'Time Lag Max.',
                        'Report Time Penalty Activated',
                        'Time Penalty'
                        ])
            w.writerow([self.seed,
                        self.n,
                        self.TimeLagActivated,
                        self.TimeLagMin,
                        self.TimeLagMax,
                        self.ReportTimePenaltyActivated,
                        self.ReportTimePenalty
                        ])
            w.writerow([])
            w.writerow(['Player Follows Navigation',
                        'Player Reports Correct Roadblock',
                        'Player Reports Roadblock'
                        ])
            w.writerow([self.settings['ProbPlayerFollowsNavigation'],
                        self.settings['ProbPlayerReportsCorrectRoadblock'],
                        self.settings['ProbPlayerReportsRoadblock']
                        ])
            w.writerow([])
            w.writerow(['Player Speed Min.',
                        'Player Speed Max.'
                        ])
            w.writerow([self.settings['PlayerSpeed']['min'],
                        self.settings['PlayerSpeed']['max']
                        ])

    def SaveDecisionCsv(self, time):
        directory = os.path.join('logs', time)
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, 'Decision.csv')
        with open(file_path, mode='w', newline='') as file:
            w = csv.writer(file)
            w.writerow(['[1] Is Next Node',
                        '[2-1] Is Report Correct If Next And Roadblock',
                        '[2-2] Is Report Correct If Adjacent And Roadblock',
                        '[3-1] Is Report Wrong If Next and No Roadblock',
                        '[3-2] Is Report Wrong If Adjacent and No Roadblock',
                        '[4] Random Time Sequence',
                        '[6] Is Random Report Correct',
                        '[7] Time Lag Values',
                        'Player Follows Navigation',
                        'Player Reports Correct Roadblock',
                        'Player Reports Roadblock',
                        'Player Speeds'])

            for i in range(self.n):
                speed_val = self.players_speeds[i] if i < len(self.players_speeds) else None
                w.writerow([self.ArrIsNextNode[i],
                            self.ArrIsCorrectNextRoadblock[i],
                            self.ArrIsCorrectAdjRoadblock[i],
                            self.ArrIsWrongNextNoRoadblock[i],
                            self.ArrIsWrongAdjNoRoadblock[i],
                            self.random_time_sequences[i],
                            self.ArrIsCorrectRandomReport[i],
                            self.ArrTimeLagValues[i],
                            self.ArrPlayerFollowsNavigation[i],
                            self.ArrPlayerReportsCorrectRoadblock[i],
                            self.ArrPlayerReportsRoadblock[i],
                            speed_val
                            ])

            print("Successfully Saved Decision.csv!")
