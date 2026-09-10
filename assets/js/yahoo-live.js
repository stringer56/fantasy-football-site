(()=>{
  const roots=[...document.querySelectorAll('[data-yahoo-live]')];
  if(!roots.length)return;
  const source='https://raw.githubusercontent.com/stringer56/fantasy-football-site/main/_data/generated';
  const score=value=>Number.isFinite(Number(value))?Number(value).toFixed(2):'0.00';
  const label=status=>({preevent:'Scheduled',midevent:'Live',postevent:'Final'}[String(status||'').toLowerCase()]||String(status||'Yahoo update'));
  const get=async name=>{const response=await fetch(`${source}/${name}?v=${Math.floor(Date.now()/60000)}`,{cache:'no-store'});if(!response.ok)throw new Error(`Yahoo ${name} unavailable`);return response.json();};
  const rosterGroup=slot=>slot==='BN'?'Bench':slot==='IR'||slot==='IR+'?'Injured reserve':'Active lineup';
  const replaceRoster=(panel,team)=>{
    const table=panel.querySelector('[data-yahoo-roster-table]');
    if(!table||!Array.isArray(team.players))return;
    table.querySelectorAll('tbody').forEach(body=>body.remove());
    const groups=['Active lineup','Bench','Injured reserve'];
    groups.forEach(group=>{
      const players=team.players.filter(player=>rosterGroup(player.selected_position||player.primary_position||'—')===group);
      if(!players.length)return;
      const body=document.createElement('tbody');
      const heading=document.createElement('tr');heading.className='rtg-roster-group';
      const title=document.createElement('th');title.colSpan=2;title.scope='rowgroup';title.textContent=group;heading.append(title);body.append(heading);
      players.forEach(player=>{const row=document.createElement('tr'),slot=document.createElement('td'),name=document.createElement('td'),badge=document.createElement('span');badge.className='rtg-roster-slot';badge.textContent=player.selected_position||player.primary_position||'—';slot.append(badge);name.textContent=player.player_name||'Unknown player';row.append(slot,name);body.append(row);});
      table.append(body);
    });
    const meta=panel.querySelector('[data-yahoo-roster-meta]');if(meta)meta.textContent=`${team.players.length} players · latest Yahoo roster`;
  };
  const apply=(matchups,rosters,sync)=>{
    const matchupList=Array.isArray(matchups.matchups)?matchups.matchups:[];
    const teamToMatchup=new Map(),teamData=new Map();
    matchupList.forEach(matchup=>(matchup.teams||[]).forEach(team=>{teamData.set(team.team_key,team);teamToMatchup.set(team.team_key,matchup);}));
    const rosterData=new Map((rosters.teams||[]).map(team=>[team.team_key,team]));
    roots.forEach(root=>{
      const currentWeek=Number(root.dataset.yahooWeek);if(currentWeek&&currentWeek!==Number(matchups.week)){root.querySelector('[data-yahoo-live-state]').textContent='Final Yahoo snapshot';return;}
      root.querySelectorAll('[data-yahoo-team-key]').forEach(side=>{const key=side.dataset.yahooTeamKey,team=teamData.get(key),matchup=teamToMatchup.get(key);if(!team)return;const value=side.querySelector('[data-yahoo-score]');if(value)value.textContent=score(team.score);const projection=side.querySelector('[data-yahoo-projection]');if(projection&&team.projected_score!=null)projection.textContent=`Projected ${score(team.projected_score)}`;side.classList.toggle('is-winner',Boolean(matchup?.winner_team_key)&&matchup.winner_team_key===key);});
      root.querySelectorAll('.rtg-matchup-hero').forEach(card=>{const side=card.querySelector('[data-yahoo-team-key]'),matchup=side&&teamToMatchup.get(side.dataset.yahooTeamKey),status=card.querySelector('[data-yahoo-matchup-status]');if(status&&matchup)status.textContent=`WEEK ${matchup.week} · ${label(matchup.status)}`;});
      root.querySelectorAll('[data-yahoo-roster-team]').forEach(panel=>{const team=rosterData.get(panel.dataset.yahooRosterTeam);if(team)replaceRoster(panel,team);});
      const state=root.querySelector('[data-yahoo-live-state]'),updated=new Date(sync.fetched_at||Date.now());if(state){state.className='rtg-yahoo-live__status is-current';state.textContent=`Yahoo updated ${updated.toLocaleTimeString([],{hour:'numeric',minute:'2-digit'})} · scores refresh automatically`;}
    });
  };
  const refresh=async()=>{try{const [matchups,rosters,sync]=await Promise.all([get('matchups.json'),get('rosters.json'),get('live_sync.json').catch(()=>get('manifest.json').then(manifest=>({fetched_at:manifest.source_update_timestamp})))]);apply(matchups,rosters,sync);}catch{roots.forEach(root=>{const state=root.querySelector('[data-yahoo-live-state]');if(state){state.className='rtg-yahoo-live__status is-delayed';state.textContent='Yahoo feed delayed · showing the last saved scores';}});}};
  refresh();
  let timer=setInterval(()=>{if(!document.hidden)refresh();},60000);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
  window.addEventListener('pagehide',()=>clearInterval(timer),{once:true});
})();
