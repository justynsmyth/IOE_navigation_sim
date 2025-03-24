import os
import csv
from roadblock import Roadblock

class ReportManager:
    def __init__(self):
        self.ReportHistory = []
        self.Reports= [] # used for scroll side bar
        self.report_spacing = 25
        self.padding = 10
        self.content_height = len(self.Reports) * self.report_spacing + self.padding

    def ResetReportManager(self):
        self.Reports = []
        self.ReportHistory = []
        self.content_height = len(self.Reports) * self.report_spacing + self.padding

    def add_to_report_history(self, id, roadblockIdx, time, exists: bool, node_a, node_b, affected_player_data: list):
        entry = {
            "id": id,
            "roadblockIdx": roadblockIdx,
            "time": time,
            "exists": exists,
            "node_a": node_a,
            "node_b": node_b,
            "affected_players": affected_player_data
        }
        self.ReportHistory.append(entry)
        if exists:
            self.Reports.append(f"{time}: Player {id} reported roadblock {roadblockIdx} at [{node_a}, {node_b}]")
        else:
            self.Reports.append(f"{time}: Player {id} reported fake roadblock {roadblockIdx} at [{node_a}, {node_b}]")
        self.content_height = len(self.Reports) * self.report_spacing + self.padding
    
    def SaveReportHistory(self, time, roadblock_map: dict[tuple,Roadblock], fake_roadblock_map: dict[tuple, Roadblock]):
        '''Save Report History to CSV File.
        1. Lists all roadblocks by index, node_a, node_b
        2. Lists all fake roadblocks by index, node_a, node_b
        3. Saves navigation history stored in the order appended in ReportHistory list
        '''
        directory = os.path.join('logs', time)
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, 'ReportHistory.csv')
        with open(file_path, mode='w', newline='') as file:
            w = csv.writer(file)

            w.writerow(['Roadblocks', '', '', 'TimesReported'])
            for i, roadblock in enumerate(roadblock_map):
                roadblock_obj = roadblock_map[roadblock]
                w.writerow([i, roadblock[0], roadblock[1], roadblock_obj.times_reported])
            
            w.writerow(['FakeRoadblocks', '', '', 'TimesReported'])
            for i, roadblock in enumerate(fake_roadblock_map):
                roadblock_obj = fake_roadblock_map[roadblock]
                w.writerow([i, roadblock[0], roadblock[1], roadblock_obj.times_reported])

            w.writerow(['Navigation History'])
            w.writerow(['id',
                        'roadblockIdx',
                        'time',
                        'RealRoadblock?',
                        'node_a',
                        'node_b'
                        ])
            for entry in self.ReportHistory:
                w.writerow([entry['id'],
                            entry['roadblockIdx'],
                            entry['time'],
                            entry['exists'],
                            entry['node_a'],
                            entry['node_b'],
                            entry['affected_players']
                            ])
                            