import os
import csv
import numpy as np

class GameGenerator:
    def __init__(self, settings, start_end_json):
        # General values for Generation
        self.settings = settings
        self.n = settings['n']
        self.seed = settings['Seed']
        self.rng = np.random.default_rng(self.seed)
        self.num_players = len(start_end_json["start_end_indices"])


        # Player Probability Setup
        self.players_speeds = self.generate_players_speeds(self.num_players)
        self.players_follow_navigation_probabilities = self.generate_probabilities_array(
            "ProbPlayerFollowsNavigation", self.num_players
        )
        self.players_report_if_roadblock_probabilities = self.generate_probabilities_array(
            "ProbPlayerReportIfRoadblock", self.num_players
        )        
        self.players_report_if_no_roadblock_probabilities = self.generate_probabilities_array(
            "ProbPlayerReportIfNoRoadblock", self.num_players
        )
        self.Players = []
        for i in range(self.num_players):
            player_data = {
                "follows_navigation": self.generate_array_by_probability(self.players_follow_navigation_probabilities[i]), 
                "follows_navigation_idx": 0,
                "reports_roadblock_if_roadblock": self.generate_array_by_probability(self.players_report_if_roadblock_probabilities[i]),
                "reports_roadblock_if_roadblock_idx": 0,
                "reports_roadblock_no_roadblock": self.generate_array_by_probability(self.players_report_if_no_roadblock_probabilities[i]),
                "reports_roadblock_no_roadblock_idx": 0,
                "follow_navigation_prob": self.players_follow_navigation_probabilities[i],
                "report_roadblock_prob": self.players_report_if_roadblock_probabilities[i],
                "false_report_no_roadblock_prob": self.players_report_if_no_roadblock_probabilities[i],
                "NavHistory": [],
            }
            self.Players.append(player_data)
        self.ResetAllPlayerIndices()
        
        # AI Experimenter Setup
        self.TimeLagActivated = settings['TimeLagActivated']
        self.TimeLagMin = settings['TimeLagMin']
        self.TimeLagMax = settings['TimeLagMax']

        if settings['TimeLagActivated']:
            self.ArrTimeLagValues = self.generate_timelag_values(settings['TimeLagMin'], settings['TimeLagMax'])
        else:
            self.ArrTimeLagValues = [0] * self.n

        # Report Time Setup
        self.ReportTimePenaltyActivated = settings['ReportTimePenaltyActivated']
        self.ReportTimePenalty = settings['ReportTimePenalty']
        self.IsAIControlled = settings['IsAIControlled']

        # AI Experimenter boolean array setup
        self.PartipicationAmount = settings['ParticipationAmount']
        self.random_time_sequences = self.generate_poisson_times(self.PartipicationAmount)

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

        self.start_end_json = start_end_json

    def generate_timelag_values(self, min, max):
        return self.rng.uniform(min, max, size=self.n).tolist()

    def generate_array_by_probability(self, probability) -> list:
        bool_array = self.rng.random(self.n) < probability
        return bool_array

    def generate_bool_array(self, setting_name) -> list:
        """ Generates a deterministic array of size n bool values based on a given probabibility within self.settings."""
        bool_array = self.rng.random(self.n) < self.settings[setting_name]
        return bool_array.tolist()  # Convert to list
    
    def generate_poisson_times(self, partipicationAmt) -> list:
        lmbda = partipicationAmt
        times = self.rng.exponential(scale=1/lmbda, size=self.n)
        return np.cumsum(times)
    
    def generate_players_speeds(self, num_players):
        mean_speed = self.settings['PlayerSpeed']['mean']
        std_dev_speed = self.settings['PlayerSpeed']['std_dev']
        speeds = self.rng.normal(mean_speed, std_dev_speed, num_players)
        speeds = np.clip(speeds, 0, None)
        return speeds.tolist()
    
    def generate_probabilities_array(self, setting_key, num_players):
        mean = self.settings[setting_key]['mean']
        std_dev = self.settings[setting_key]['std_dev']
        probabilities = self.rng.normal(mean, std_dev, num_players)
        # probabilities within [0,1]
        probabilities = np.clip(probabilities, 0, 1)
        return probabilities.tolist()
    
    def add_to_nav_history(self, id, time, reason, current_waypoint, route):
        entry = {
            "time": time,
            "reason": reason,
            "current_waypoint": current_waypoint,
            "updateRoute": list(route)
        }
        self.Players[id]["NavHistory"].append(entry)


    def SaveSetupCsv(self, time: str):
        directory = os.path.join('logs', time)
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, 'Setup.csv')
        with open(file_path, mode='w', newline='') as file:
            w = csv.writer(file)
            w.writerow(['IsAIControlled',
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
                    self.settings['ProbCorrectRandomReport']
                   ])
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
            w.writerow(['Player Speed Mean',
                    'Player Speed Std. Dev.',
                    'ProbPlayerFollowsNavigation Mean',
                    'ProbPlayerFollowsNavigation Std. Dev.',
                    'ProbPlayerReportIfRoadblock Mean',
                    'ProbPlayerReportIfRoadblock Std. Dev.',
                    'ProbPlayerReportIfNoRoadblock Mean',
                    'ProbPlayerReportIfNoRoadblock Std. Dev.'])
            w.writerow([self.settings['PlayerSpeed']['mean'],
                    self.settings['PlayerSpeed']['std_dev'],
                    self.settings['ProbPlayerFollowsNavigation']['mean'],
                    self.settings['ProbPlayerFollowsNavigation']['std_dev'],
                    self.settings['ProbPlayerReportIfRoadblock']['mean'],
                    self.settings['ProbPlayerReportIfRoadblock']['std_dev'],
                    self.settings['ProbPlayerReportIfNoRoadblock']['mean'],
                    self.settings['ProbPlayerReportIfNoRoadblock']['std_dev']])

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
                        ])


            for i in range(self.n):
                w.writerow([self.ArrIsNextNode[i],
                            self.ArrIsCorrectNextRoadblock[i],
                            self.ArrIsCorrectAdjRoadblock[i],
                            self.ArrIsWrongNextNoRoadblock[i],
                            self.ArrIsWrongAdjNoRoadblock[i],
                            self.random_time_sequences[i],
                            self.ArrIsCorrectRandomReport[i],
                            self.ArrTimeLagValues[i]
                            ])


    def SavePlayerDecisionCsv(self, time):
        directory = os.path.join('logs', time)
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, 'PlayerDecisions.csv')
        with open(file_path, mode='w', newline='') as file:
            w = csv.writer(file)
            w.writerow(['PlayerID',
                        'Player Speeds',
                        'Player Follows Navigation',
                        'ProbReportIfRoadblock',
                        'ProbReportIfNoRoadblock',
                        ])

            for i, player in enumerate(self.Players):
                w.writerow([i,
                            self.players_speeds[i],
                            player['follow_navigation_prob'],
                            player['report_roadblock_prob'],
                            player['false_report_no_roadblock_prob']])
            w.writerow([])
            w.writerow(['PlayerID',
                        ' ',
                        'Player Follows Navigation',
                        'ProbReportIfRoadblock',
                        'ProbReportIfNoRoadblock',
                        ])
            for i, player in enumerate(self.Players):
                for j in range(self.n):
                    w.writerow([i,
                                ' ',
                                player['follows_navigation'][j],
                                player['reports_roadblock_if_roadblock'][j],
                                player['reports_roadblock_no_roadblock'][j]
                                ])
    

    def SaveNavHistory(self, time):
        directory = os.path.join('logs', time)
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, 'NavHistory.csv')
        with open(file_path, mode='w', newline='') as file:
            w = csv.writer(file)
            w.writerow(['ParticipantIdx',
                        'Time',
                        'Reason',
                        'CurrentWaypoint',
                        'UpdatedRoute',
                        ])
            for i, player in enumerate(self.Players):
                for entry in player['NavHistory']:
                    w.writerow([i,
                                entry['time'],
                                entry['reason'],
                                entry['current_waypoint'],
                                entry['updateRoute']
                                ])    


    def GetNextFollowNavigation(self, id) -> bool:
        # "reports_roadblock_no_roadblock": self.generate_array_by_probability(self.players_report_if_no_roadblock_probabilities[i]),
        # "follow_navigation_prob": self.players_follow_navigation_probabilities[i],
        # "report_roadblock_prob": self.players_report_if_roadblock_probabilities[i],
        # "false_report_no_roadblock_prob": self.players_report_if_no_roadblock_probabilities[i],
        idx = self.Players[id]["follows_navigation_idx"]
        result = self.Players[id]["follows_navigation"][idx]
        self.Players[id]["follows_navigation_idx"] += 1
        return result

    def GetNextReportsRoadblockIfRoadblock(self, id) -> bool:
        # "reports_roadblock_no_roadblock": self.generate_array_by_probability(self.players_report_if_no_roadblock_probabilities[i]),
        # "follow_navigation_prob": self.players_follow_navigation_probabilities[i],
        # "report_roadblock_prob": self.players_report_if_roadblock_probabilities[i],
        # "false_report_no_roadblock_prob": self.players_report_if_no_roadblock_probabilities[i],
        idx = self.Players[id]["reports_roadblock_if_roadblock_idx"]
        result = self.Players[id]["reports_roadblock_if_roadblock"][idx]
        self.Players[id]["reports_roadblock_if_roadblock_idx"] += 1
        return result

    def GetNextReportsRoadblockIfNoRoadblock(self, id) -> bool:
        idx = self.Players[id]["reports_roadblock_no_roadblock_idx"]
        result = self.Players[id]["reports_roadblock_no_roadblock"][idx]
        self.Players[id]["reports_roadblock_no_roadblock_idx"] += 1
        return result

    def ResetAllPlayerIndices(self):
        for player in self.Players:
            player["reports_roadblock_no_roadblock_idx"] = 0
            player["reports_roadblock_if_roadblock_idx"] = 0
            player["follows_navigation_idx"] = 0
    