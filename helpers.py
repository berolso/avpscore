

class Helper():
  """helper functions"""

  @staticmethod
  def parse_avp_match(i):

    '''parse xml file sent from avp api'''
    # unique 4 digit match id from CompId and MatchNo
    m_id = int(str(i['CompetitionId']) + str(i['MatchNo']).zfill(2))
    # stats string. (create stats relational table in future
    stats = str(i['Stats'])
    # team strings
    null_filler = 'TBD'
    try:
      team_a = f'''({i['TeamA']['Seed']}) {i['TeamA']['Captain']['FirstName']} {i['TeamA']['Captain']['LastName']} / {i['TeamA']['Player']['FirstName']} {i['TeamA']['Player']['LastName']}'''
    except:
      team_a = null_filler
    try:
      team_b = f'''({i['TeamB']['Seed']}) {i['TeamB']['Captain']['FirstName']} {i['TeamB']['Captain']['LastName']} / {i['TeamB']['Player']['FirstName']} {i['TeamB']['Player']['LastName']}'''
    except:
      team_b=null_filler
    # Sets will parse out a string for the order of who won the set
    try:
      score_w_a = ', '.join([f'''{j['A']} - {j['B']}''' for j in i['Sets']])
    except:
      score_w_a = null_filler

    try:
      score_w_b = ', '.join([f'''{j['B']} - {j['A']}''' for j in i['Sets']])
    except:
      score_w_b = null_filler

    # format match into dictionary for **upacking directly into Match class constructor
    match_dict = {
      'match_id' : m_id,
      'stats' : stats,
      'competition_id' : i['CompetitionId'],
      'competition_name' : i['CompetitionName'],
      'competition_code' : i['CompetitionCode'],
      'match_no' : i['MatchNo'],
      'bracket' : i['Bracket'],
      'team_a' : team_a,
      'team_b' : team_b,
      'sets' : (score_w_a,'%^',score_w_b),
      'winner' : i['Winner'],
      'match_state' : i['MatchState'],
    }

    return match_dict

  @staticmethod
  def format_result_message(m):
    """format the match result message for delivery"""
    # hyperlink bracket for telegram markdown 
    bracket = f"[{m.bracket}](https://avp.com/brackets/)"
    # HTML
    # bracket = f"<a href='https://avp.com/brackets/'>{m.bracket}</a>"
    #m.sets example ("21 - 12, 21 - 16",%^,"12 - 21, 16 - 21")
    scores = m.sets.split('",%^,"')
    if m.winner == 1:
      return f'''{m.team_a} W 
{m.team_b} 
{scores[0][2:]}
in {bracket}'''
    if m.winner == 2:
      return f'''{m.team_b} W
{m.team_a} 
{scores[1][:-2]} 
in {bracket}'''
    else:
      return 'no score'
