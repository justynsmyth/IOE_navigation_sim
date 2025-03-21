import json


def load_settings(filename):
    """Load settings from a JSON file."""
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def merge_settings(config_file, default_file='DefaultConfig.json'):
    """Merge configuration settings with default settings."""
    # Load the settings from both files
    config_settings = load_settings(config_file)
    default_settings = load_settings(default_file)

    # Update the config settings with default values where needed
    for key, default_value in default_settings.items():
        if config_settings.get(key) is None:
            config_settings[key] = default_value

    return config_settings


def process_settings(settings):
    """Process settings to replace None with 'None'."""

    # If TimeLag is Not Active, Set Values to None
    if not settings.get("TimeLagActivated", False):
        settings["TimeLagActivated"] = False
        settings["TimeLag"] = 0
    else:
        settings["TimeLagActivated"] = True
        isValidTimeLagValues(settings)

    # If ReportTimePenalty is Not Active, Set Values to None
    if not settings.get("ReportTimePenaltyActivated", False):
        settings["ReportTimePenaltyActivated"] = False
        settings["ReportTimePenalty"]['mean'] = 0
        settings["ReportTimePenalty"]['std_dev'] = 0
    else:
        settings["ReportTimePenaltyActivated"] = True
        isValidReportTimePenaltyValues(settings)

    if settings.get("IsAIControlled", True):
        ValidateAISettings(settings)

    # Replace None with 'None' for Setup.csv record
    processed_settings = {key: (value if value is not None else 'None')
                          for key, value in settings.items()}

    return processed_settings


def isValidReportTimePenaltyValues(settings) -> bool:
    try:
        mean = float(settings["ReportTimePenalty"]['mean'])
        std_dev = float(settings["ReportTimePenalty"]['std_dev'])
        if mean < 0:
            raise ValueError(
                f"Mean: {mean} must be a non-negative number.")
        if std_dev < 0:
            raise ValueError(
                f"Std_dev {std_dev} must be a non-negative number"
            )
    except ValueError as e:
        print(e)
        exit(1)


def isValidTimeLagValues(settings) -> bool:
    try:
        time_lag = int(settings["TimeLag"]['mean'])
        if time_lag < 0:
            raise ValueError(
                f"TimeLagMin: {time_lag} must be a non-negative integer.")
        std_dev = (settings['TimeLag']['std_dev'])
        if std_dev < 0:
            raise ValueError(
                f"TimeLagStd: {std_dev} must be a non-negative number.")
        if time_lag < std_dev:
            raise ValueError(
                f"TimeLagMin: {time_lag} must be >= TimeLagStd: {std_dev}."
            )

    except ValueError as e:
        print(e)
        exit(1)


def ValidateAISettings(settings) -> bool:
    try:
        # Validate ProbOfNextNode
        prob_of_next_node = float(settings["ProbOfNextNode"])
        if not (0.0 <= prob_of_next_node <= 1.0):
            raise ValueError(
                f"ProbOfNextNode: {prob_of_next_node} must be between 0.0 and 1.0."
            )

        # Validate ProbCorrectReportIfRoadblock
        prob_correct_report_if_roadblock = float(
            settings["ProbCorrectReportIfRoadblock"])
        if not (0.0 <= prob_correct_report_if_roadblock <= 1.0):
            raise ValueError(
                f"ProbCorrectReportIfRoadblock: {prob_correct_report_if_roadblock} must be between 0.0 and 1.0."
            )

        # Validate ProbWrongReportIfNoRoadblock
        prob_wrong_report_if_no_roadblock = float(
            settings["ProbWrongReportIfNoRoadblock"])
        if not (0.0 <= prob_wrong_report_if_no_roadblock <= 1.0):
            raise ValueError(
                f"ProbWrongReportIfNoRoadblock: {prob_wrong_report_if_no_roadblock} must be between 0.0 and 1.0."
            )

        # Validate ParticipationAmount
        participation_amount = int(settings["ParticipationAmount"])
        if participation_amount < 0:
            raise ValueError(
                f"ParticipationAmount: {participation_amount} must be a non-negative integer."
            )

        # Validate MinReportDistance
        min_report_distance = int(settings["MinReportDistance"])
        if min_report_distance < 0:
            raise ValueError(
                f"MinReportDistance: {min_report_distance} must be a non-negative integer."
            )

        # Validate MaxReportDistance
        max_report_distance = int(settings["MaxReportDistance"])
        if max_report_distance < 0:
            raise ValueError(
                f"MaxReportDistance: {max_report_distance} must be a non-negative integer."
            )
        if max_report_distance < min_report_distance:
            raise ValueError(
                f"Invalid ReportDistance values: MaxReportDistance ({max_report_distance}) should be >= MinReportDistance ({min_report_distance})."
            )

        # Validate ProbCorrectReport (Experimenter)
        prob_correct_report = float(settings["ProbCorrectRandomReport"])
        if not (0.0 <= prob_correct_report <= 1.0):
            raise ValueError(
                f"ProbCorrectReport: {prob_correct_report} must be between 0.0 and 1.0."
            )
        
        # Validate ProbPlayerFollowsNavigation
        prob_player_follows_navigation = float(settings["ProbPlayerFollowsNavigation"])
        if not (0.0 <= prob_player_follows_navigation <= 1.0):
            raise ValueError(
                f"ProbPlayerFollowsNavigation: {prob_player_follows_navigation} must be between 0.0 and 1.0."
            )
        
        # Validate ProbPlayerReportsCorrectRoadblock
        prob_player_reports_correct_roadblock = float(settings["ProbPlayerReportsCorrectRoadblock"])
        if not (0.0 <= prob_player_reports_correct_roadblock <= 1.0):
            raise ValueError(
                f"ProbPlayerReportsCorrectRoadblock: {prob_player_reports_correct_roadblock} must be between 0.0 and 1.0."
            )
        
        # Validate ProbPlayerReportsRoadblock        
        prob_player_reports_roadblock = float(settings["ProbPlayerReportsRoadblock"])
        if not (0.0 <= prob_player_reports_roadblock <= 1.0):
            raise ValueError(
                f"ProbPlayerReportsRoadblock: {prob_player_reports_roadblock} must be between 0.0 and 1.0.")

    except ValueError as e:
        print(e)
        exit(1)