const DATA_ROOT='https://raw.githubusercontent.com/stringer56/fantasy-football-site/main/_data/generated';
const SCORE_POLL_MS=60_000;
const ROSTER_POLL_MS=15*60_000;
const STALE_AFTER_MS=12*60_000;
const REQUEST_TIMEOUT_MS=15_000;

export function parseFreshness(value,minimum=0){
  const timestamp=Date.parse(String(value||''));
  return Number.isFinite(timestamp)&&timestamp>=minimum?timestamp:null;
}

export function normalizeRecord(value){
  if(typeof value!=='string')return null;
  const normalized=value.trim().replace(/[–—]/g,'-');
  return /^\d+-\d+(?:-\d+)?$/.test(normalized)?normalized:null;
}

export function formatEastern(timestamp){
  return new Intl.DateTimeFormat('en-US',{
    timeZone:'America/New_York',
    hour:'numeric',
    minute:'2-digit',
    timeZoneName:'short'
  }).format(new Date(timestamp));
}

export function freshnessState(timestamp,now=Date.now()){
  return now-timestamp>STALE_AFTER_MS?'stale':'current';
}

const roots=typeof document==='undefined'
  ?[]
  :[...document.querySelectorAll('[data-yahoo-live]')];

if(roots.length){
  const matchupLabel=status=>({
    preevent:'Scheduled',
    midevent:'Live',
    postevent:'Final'
  }[String(status||'').toLowerCase()]||'Yahoo update');

  const formattedScore=value=>{
    const number=Number(value);
    return Number.isFinite(number)?number.toFixed(2):null;
  };

  const get=async name=>{
    const controller=new AbortController();
    const timeout=setTimeout(()=>controller.abort(),REQUEST_TIMEOUT_MS);
    try{
      const version=Math.floor(Date.now()/SCORE_POLL_MS);
      const response=await fetch(`${DATA_ROOT}/${name}?v=${version}`,{
        cache:'no-store',
        signal:controller.signal
      });
      if(!response.ok)throw new Error('Yahoo live resource unavailable');
      return await response.json();
    }finally{
      clearTimeout(timeout);
    }
  };

  const rosterGroup=slot=>{
    if(slot==='BN')return 'Bench';
    if(slot==='IR'||slot==='IR+')return 'Injured reserve';
    return 'Active lineup';
  };

  const replaceRoster=(panel,team)=>{
    const table=panel.querySelector('[data-yahoo-roster-table]');
    if(!table||!Array.isArray(team.players))return;
    table.querySelectorAll('tbody').forEach(body=>body.remove());
    ['Active lineup','Bench','Injured reserve'].forEach(group=>{
      const players=team.players.filter(player=>
        rosterGroup(player.selected_position||player.primary_position||'—')===group
      );
      if(!players.length)return;
      const body=document.createElement('tbody');
      const heading=document.createElement('tr');
      heading.className='rtg-roster-group';
      const title=document.createElement('th');
      title.colSpan=2;
      title.scope='rowgroup';
      title.textContent=group;
      heading.append(title);
      body.append(heading);
      players.forEach(player=>{
        const row=document.createElement('tr');
        const slot=document.createElement('td');
        const name=document.createElement('td');
        const badge=document.createElement('span');
        badge.className='rtg-roster-slot';
        badge.textContent=player.selected_position||player.primary_position||'—';
        slot.append(badge);
        name.textContent=player.player_name||'Unknown player';
        row.append(slot,name);
        body.append(row);
      });
      table.append(body);
    });
    const meta=panel.querySelector('[data-yahoo-roster-meta]');
    if(meta)meta.textContent=`${team.players.length} players · latest Yahoo roster`;
  };

  let lastApplied=0;
  let lastRosterFetch=0;
  let refreshing=false;

  const showDelayed=message=>{
    roots.forEach(root=>{
      const state=root.querySelector('[data-yahoo-live-state]');
      if(state){
        state.className='rtg-yahoo-live__status is-delayed';
        state.textContent=message;
      }
    });
  };

  const apply=(matchups,rosters,sync,timestamp)=>{
    const matchupList=Array.isArray(matchups.matchups)?matchups.matchups:[];
    if(!Number(matchups.week)||!matchupList.length)return false;
    const teamToMatchup=new Map();
    const teamData=new Map();
    matchupList.forEach(matchup=>(matchup.teams||[]).forEach(team=>{
      teamData.set(team.team_key,team);
      teamToMatchup.set(team.team_key,matchup);
    }));
    if(!teamData.size)return false;
    const rosterData=new Map(
      Array.isArray(rosters?.teams)?rosters.teams.map(team=>[team.team_key,team]):[]
    );

    roots.forEach(root=>{
      const state=root.querySelector('[data-yahoo-live-state]');
      const currentWeek=Number(root.dataset.yahooWeek);
      if(currentWeek&&currentWeek!==Number(matchups.week)){
        if(state)state.textContent='Final Yahoo snapshot';
        return;
      }
      root.querySelectorAll('[data-yahoo-team-key]').forEach(side=>{
        const key=side.dataset.yahooTeamKey;
        const team=teamData.get(key);
        const matchup=teamToMatchup.get(key);
        if(!team)return;
        const score=formattedScore(team.score);
        const value=side.querySelector('[data-yahoo-score]');
        if(value&&score!==null)value.textContent=score;
        const record=normalizeRecord(team.record);
        const recordValue=side.querySelector('[data-yahoo-record]');
        if(recordValue&&record!==null)recordValue.textContent=record;
        const projected=formattedScore(team.projected_score);
        const projection=side.querySelector('[data-yahoo-projection]');
        if(projection){
          projection.textContent=projected===null
            ?'Projection unavailable'
            :`Projected ${projected}`;
        }
        side.classList.toggle(
          'is-winner',
          Boolean(matchup?.winner_team_key)&&matchup.winner_team_key===key
        );
      });
      root.querySelectorAll('.rtg-matchup-hero').forEach(card=>{
        const side=card.querySelector('[data-yahoo-team-key]');
        const matchup=side&&teamToMatchup.get(side.dataset.yahooTeamKey);
        const status=card.querySelector('[data-yahoo-matchup-status]');
        if(status&&matchup){
          status.textContent=`WEEK ${matchup.week} · ${matchupLabel(matchup.status)}`;
        }
      });
      if(rosterData.size){
        root.querySelectorAll('[data-yahoo-roster-team]').forEach(panel=>{
          const team=rosterData.get(panel.dataset.yahooRosterTeam);
          if(team)replaceRoster(panel,team);
        });
      }
      if(state){
        const stale=freshnessState(timestamp)==='stale';
        state.className=`rtg-yahoo-live__status ${stale?'is-delayed':'is-current'}`;
        state.textContent=stale
          ?`Yahoo update delayed · last updated ${formatEastern(timestamp)}`
          :`Yahoo updated ${formatEastern(timestamp)} · scores refresh automatically`;
      }
    });
    lastApplied=timestamp;
    return true;
  };

  const refresh=async()=>{
    if(refreshing)return;
    refreshing=true;
    try{
      const now=Date.now();
      const includeRosters=!lastRosterFetch||now-lastRosterFetch>=ROSTER_POLL_MS;
      const [matchups,sync,rosters]=await Promise.all([
        get('matchups.json'),
        get('live_sync.json').catch(()=>get('manifest.json').then(manifest=>({
          fetched_at:manifest.source_update_timestamp,
          source:manifest.source,
          status:manifest.status
        }))),
        includeRosters?get('rosters.json'):Promise.resolve(null)
      ]);
      const timestamp=parseFreshness(sync.fetched_at,lastApplied);
      if(timestamp===null)return;
      if(apply(matchups,rosters,sync,timestamp)&&includeRosters)lastRosterFetch=now;
    }catch{
      showDelayed(
        lastApplied
          ?`Yahoo feed delayed · last updated ${formatEastern(lastApplied)}`
          :'Yahoo feed delayed · showing the last saved scores'
      );
    }finally{
      refreshing=false;
    }
  };

  refresh();
  const timer=setInterval(()=>{if(!document.hidden)refresh();},SCORE_POLL_MS);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
  window.addEventListener('pagehide',()=>clearInterval(timer),{once:true});
}
