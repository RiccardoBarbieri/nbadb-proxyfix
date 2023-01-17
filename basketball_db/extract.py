"""data extraction functions
"""
# -- Imports --------------------------------------------------------------------------
import os
from datetime import datetime

import pandas as pd
import swifter
from nba_api.stats.endpoints.boxscoresummaryv2 import BoxScoreSummaryV2
from nba_api.stats.endpoints.leaguegamelog import LeagueGameLog
from nba_api.stats.endpoints.teamdetails import TeamDetails
from nba_api.stats.static import players, teams
from tqdm import tqdm

from basketball_db.utils import get_proxies, combine_team_games


# -- Functions -----------------------------------------------------------------------
def get_players(save_to_db:bool=False, conn=None) -> pd.DataFrame:
    """retrieves all players from the static players endpoint

    Returns:
        pd.DataFrame: all players
    """
    column_types = {
        "id": "category",
        "full_name": "category",
        "first_name": "category",
        "last_name": "category",
        "is_active": "bool"
    }
    df = pd.concat([pd.DataFrame(player, index=[0]).astype(column_types) for player in players.get_players()], ignore_index=True)
    df.columns = df.columns.to_series().apply(lambda x: x.lower())
    if save_to_db:
        df.to_sql("player", conn, if_exists="replace", index=False)
    return df


def get_teams(save_to_db:bool=False, conn=None) -> pd.DataFrame:
    """retrieves all teams from the static teams endpoint

    Returns:
        pd.DataFrame: all teams
    """
    column_types = {
        'id': 'category',
        'full_name': 'category',
        'abbreviation': 'category',
        'nickname': 'category',
        'city': 'category',
        'state': 'category',
        "year_founded": 'int'
    }
    df = pd.concat([pd.DataFrame(team, index=[0]).astype(column_types) for team in teams.get_teams()], ignore_index=True)
    df.columns = df.columns.to_series().apply(lambda x: x.lower())
    if save_to_db:
        df.to_sql("team", conn, if_exists="replace", index=False)
    return df


def get_league_game_log_from_date(datefrom, save_to_db=False, conn=None):
    column_types = {
        'season_id': 'category',
        'team_id_home': 'category',
        'team_abbreviation_home': 'category',
        'team_name_home': 'category',
        'game_id': 'category',
        'game_date': 'datetime64[ns]',
        'matchup_home': 'category',
        'wl_home': 'category',
        'video_available_home': 'category',
        'team_id_away': 'category',
        'team_abbreviation_away': 'category',
        'team_name_away': 'category',
        'matchup_away': 'category',
        'wl_away': 'category',
        'video_available_away': 'category'
    }
    proxies = get_proxies()
    while True:
        if len(proxies) < 1:
            proxies = get_proxies()
        try:
            df = combine_team_games(LeagueGameLog(date_from_nullable=datefrom, proxy=proxies[0], timeout=3).get_data_frames()[0])
            df.columns = df.columns.to_series().apply(lambda x: x.lower())
            df = df.astype(column_types)
            if save_to_db:
                df.to_sql("game", conn, if_exists="append", index=False)
        except:
            proxies = proxies[1:]
            continue
    return df


def get_league_game_log_all(conn) -> pd.DataFrame:
    """ret

    _extended_summary_

    Returns:
        pd.DataFrame: _description_
    """
    def helper(season:str, proxies:list[str]=[]):
        column_types = {
            'season_id': 'category',
            'team_id_home': 'category',
            'team_abbreviation_home': 'category',
            'team_name_home': 'category',
            'game_id': 'category',
            'game_date': 'datetime64[ns]',
            'matchup_home': 'category',
            'wl_home': 'category',
            'video_available_home': 'category',
            'team_id_away': 'category',
            'team_abbreviation_away': 'category',
            'team_name_away': 'category',
            'matchup_away': 'category',
            'wl_away': 'category',
            'video_available_away': 'category'
        }
        while True:
            if len(proxies) < 1:
                proxies = get_proxies()
            try:
                df = combine_team_games(LeagueGameLog(season=season, proxy=proxies[0], timeout=3).get_data_frames()[0])
                df.columns = df.columns.to_series().apply(lambda x: x.lower())
                df = df.astype(column_types)
                return df
            except:
                proxies = proxies[1:]
                continue
    this_year = datetime.now().year
    proxies = get_proxies()
    for season in tqdm(range(1946, this_year), desc="Seasons"):
        df = helper(str(season), proxies=proxies)
        df.to_sql("game", conn, if_exists="append", index=False)
    return df


def get_player_info(save_to_db:bool=False, conn=None) -> pd.DataFrame:
    def helper(player, proxies):
        while True:
            if len(proxies) < 1:
                proxies = get_proxies()
            try:
                return CommonPlayerInfo(player_id=player, proxy=proxies[0], timeout=3).get_data_frames()[0]
            except:
                proxies = proxies[1:]
                continue

    player_ids = pd.concat([pd.DataFrame(p, index=[0]) for p in players.get_players()], ignore_index=True)['id']
    col_types = {
        'person_id': 'category',
        'first_name': 'category',
        'last_name': 'category',
        'display_first_last': 'category',
        'display_last_comma_first': 'category',
        'display_fi_last': 'category',
        'player_slug': 'category',
        'birthdate': 'datetime64[ns]',
        'school': 'category',
        'country': 'category',
        'last_affiliation': 'category',
        'height': 'category',
        'weight': 'int',
        'season_exp': 'int',
        'jersey': 'category',
        'position': 'category',
        'rosterstatus': 'category',
        'games_played_current_season_flag': 'category',
        'team_id': 'category',
        'team_name': 'category',
        'team_abbreviation': 'category',
        'team_code': 'category',
        'team_city': 'category',
        'playercode': 'category',
        'from_year': 'int',
        'to_year': 'int',
        'dleague_flag': 'category',
        'nba_flag': 'category',
        'games_played_flag': 'category',
        'draft_year': 'int',
        'draft_round': 'int',
        'draft_number': 'int',
        'greatest_75_flag': 'category'
    }
    proxies = get_proxies()
    dfs = player_ids.swifter.allow_dask_on_strings(enable=True).apply(lambda x: helper(x, proxies))
    dfs = pd.concat(dfs, ignore_index=True)
    dfs.columns = dfs.columns.to_series().apply(lambda x: x.lower())
    dfs = dfs.astype(col_types)
    if save_to_db:
        dfs.to_sql("common_player_info", conn, if_exists="append", index=False)
    return dfs


def get_teams_details(save_to_db:bool=False, conn=None) -> pd.DataFrame:
    def helper(team, proxies):
        dfs = {"team_details": [], "team_history": []}
        while True:
            if len(proxies) < 1:
                proxies = get_proxies()
            try:
                df = TeamDetails(team_id=team, proxy=proxies[0], timeout=3).get_data_frames()
                df = pd.concat([df[0], df[2].set_index("ACCOUNTTYPE").T.reset_index(drop=True)], axis=1)
                df.columns = df.columns.to_series().apply(lambda x: x.lower())
                df = df.astype(column_types)
                dfs['team_details'].append(df)
                history = dfs[1]
                history.columns = ['team_id', 'city', 'nickname', 'year_founded', 'year_active_till']
                history['team_id'] = history['team_id'].astype('category')
                dfs['team_history'].append(history)
                return dfs
            except:
                proxies = proxies[1:]
                continue
    column_types = {
        'team_id': 'category', 
        'abbreviation': 'category', 
        'nickname': 'category',
        "yearfounded": 'int',
        'city': 'category', 
        'arena': 'category',
        'arenacapacity': 'int',
        'generalmanager': 'category',
        'headcoach': 'category',
        'dleagueaffiliation': 'category',
        'facebook': 'category',
        'instagram': 'category',
        'twitter': 'category'
    }
    teams = teams.get_teams()['id']
    proxies = get_proxies()
    dfs = teams.swifter.allow_dask_on_strings(enable=True).apply(lambda x: helper(x, proxies))
    team_details = pd.concat([df['team_details'] for df in dfs], ignore_index=True)
    team_history = pd.concat([df['team_history'] for df in dfs], ignore_index=True)
    if save_to_db:
        team_details.to_sql("team_details", conn, if_exists="replace", index=False)
        team_history.to_sql("team_history", conn, if_exists="replace", index=False)
    return dfs


def get_box_score_summaries(game_ids, save_to_db=False, conn=None):
    def helper():
        dfs = {t: [] for t in ['box_score', 'officials', 'inactive_players']}
        while True:
            if len(proxies) < 1:
                proxies = get_proxies()
            try:
                res_dfs = BoxScoreSummary(game_id=game_id, proxy=proxies[0], timeout=3).get_data_frames()
                for df in res_dfs:
                    df.columns = df.columns.to_series().apply(lambda x: x.lower())
                df = pd.merge(res_dfs[1], res_dfs[1], suffixes=['_home', '_away'], on='league_id')
                df = pd.DataFrame(df[df.team_id_home != df.team_id_away].iloc[0, :]).T.drop(['team_id_home', 'team_id_away'], axis=1).reset_index(drop=True)
                df = pd.concat([df, res_dfs[0], res_dfs[4]], axis=1)
                temp = pd.merge(dfs[5], dfs[5], on=['game_date_est', 'game_sequence', 'game_id'], suffixes=["_home", "_away"])
                temp = pd.DataFrame(temp[temp.team_id_home != temp.team_id_away].iloc[0, :]).T.drop(['team_id_home', 'team_id_away'], axis=1).reset_index(drop=True)
                df = pd.concat([df, temp], axis=1)
                dfs['box_score'] = df
                officials = res_dfs[2]
                officials['game_id'] = game_id
                dfs['officials'] = officials
                inactive_players = res_dfs[3]
                inactive_players['game_id'] = game_id
                dfs['inactive_players'] = inactive_players
                return dfs
            except:
                proxies = proxies[1:]
                continue
    proxies = get_proxies()
    # game_ids = pd.read_sql("SELECT game_id FROM game", conn).game_id.to_list()
    dfs = pd.Series(game_ids).swifter.allow_dask_on_strings(enable=True).apply()
    box_score = pd.concat([d['box_score'] for d in dfs]).reset_index(drop=True)
    officials = pd.concat([d['officials'] for d in dfs]).reset_index(drop=True)
    inactive_players = pd.concat([d['inactive_players'] for d in dfs]).reset_index(drop=True)
    if save_to_db:
        box_score.to_sql("box_score", conn, if_exists="append", index=False)
        officials.to_sql("officials", conn, if_exists="append", index=False)
        inactive_players.to_sql("inactive_players", conn, if_exists="append", index=False)
    return dfs